from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

from celery.utils.log import get_task_logger
from sqlalchemy import delete, select, update

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.entities import (
    AuthSession,
    Build,
    Notification,
    Offer,
    OneTimeToken,
    PriceAlert,
    PriceHistory,
    Product,
    RefreshTokenHistory,
    Store,
    User,
)
from app.services.currency import update_nbp_rates
from app.services.email import email_service
from app.services.parsers.sync import sync_store
from app.workers.celery_app import celery_app

logger = get_task_logger(__name__)


async def _sync_store(store_id: UUID, task_id: str | None) -> dict:
    async with AsyncSessionLocal() as session:
        store = await session.get(Store, store_id)
        if store is None or not store.is_active:
            raise ValueError("Store not found or disabled")
        run = await sync_store(session, store, task_id=task_id)
        return {
            "run_id": str(run.id),
            "status": run.status,
            "created": run.created_count,
            "updated": run.updated_count,
        }


@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 4},
)
def sync_store_task(self, store_id: str) -> dict:
    return asyncio.run(_sync_store(UUID(store_id), self.request.id))


async def _active_store_ids() -> list[str]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Store.id).where(Store.is_active.is_(True), Store.parser_type != "manual")
        )
        return [str(item) for item in result.scalars()]


@celery_app.task
def sync_all_stores_task() -> dict:
    store_ids = asyncio.run(_active_store_ids())
    for store_id in store_ids:
        sync_store_task.delay(store_id)
    return {"queued": len(store_ids)}


async def _cleanup() -> dict:
    now = datetime.now(UTC)
    offer_stale = now - timedelta(hours=max(settings.offer_stale_hours * 4, 48))
    history_cutoff = now - timedelta(days=730)
    async with AsyncSessionLocal() as session:
        expired_builds = await session.execute(
            delete(Build).where(
                Build.is_saved.is_(False),
                Build.expires_at.is_not(None),
                Build.expires_at < now,
            )
        )
        expired_sessions = await session.execute(
            delete(AuthSession).where(
                (AuthSession.expires_at < now)
                | (
                    (AuthSession.revoked_at.is_not(None))
                    & (AuthSession.revoked_at < now - timedelta(days=30))
                )
            )
        )
        refresh_history = await session.execute(
            delete(RefreshTokenHistory).where(
                RefreshTokenHistory.rotated_at
                < now - timedelta(days=settings.refresh_token_expire_days)
            )
        )
        expired_tokens = await session.execute(
            delete(OneTimeToken).where(
                (OneTimeToken.expires_at < now)
                | (
                    (OneTimeToken.used_at.is_not(None))
                    & (OneTimeToken.used_at < now - timedelta(days=7))
                )
            )
        )
        stale_offers = await session.execute(
            update(Offer)
            .where(Offer.fetched_at < offer_stale, Offer.in_stock.is_(True))
            .values(in_stock=False)
        )
        old_history = await session.execute(
            delete(PriceHistory).where(PriceHistory.recorded_at < history_cutoff)
        )
        await session.commit()
        return {
            "expired_builds": expired_builds.rowcount,
            "expired_sessions": expired_sessions.rowcount,
            "expired_tokens": expired_tokens.rowcount,
            "refresh_history": refresh_history.rowcount,
            "stale_offers": stale_offers.rowcount,
            "old_history": old_history.rowcount,
        }


@celery_app.task
def cleanup_task() -> dict:
    return asyncio.run(_cleanup())


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def update_currency_rates_task() -> dict:
    async def run() -> dict:
        async with AsyncSessionLocal() as session:
            count = await update_nbp_rates(session)
            return {"created": count}

    return asyncio.run(run())


async def _check_price_alerts() -> dict:
    sent = 0
    checked = 0
    pending_emails: list[tuple[str, str, str, str]] = []
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PriceAlert, User, Product)
            .join(User, User.id == PriceAlert.user_id)
            .join(Product, Product.id == PriceAlert.product_id)
            .where(
                PriceAlert.is_active.is_(True),
                User.is_active.is_(True),
                Product.is_active.is_(True),
            )
        )
        for alert, user, product in result.all():
            checked += 1
            best_offer = await session.scalar(
                select(Offer)
                .where(
                    Offer.product_id == product.id,
                    Offer.currency == alert.currency,
                    Offer.in_stock.is_(True),
                    Offer.is_active.is_(True),
                )
                .order_by((Offer.price + Offer.shipping_price).asc())
                .limit(1)
            )
            if best_offer is None:
                continue
            effective_price = best_offer.price + best_offer.shipping_price
            should_notify = effective_price <= alert.target_price and (
                alert.last_notified_price is None or effective_price < alert.last_notified_price
            )
            if not should_notify:
                continue
            notification = Notification(
                user_id=user.id,
                kind="price_alert",
                title=f"Цена снизилась: {product.name}",
                body=f"Текущая цена {effective_price} {alert.currency}",
                data={
                    "alert_id": str(alert.id),
                    "product_id": str(product.id),
                    "offer_id": str(best_offer.id),
                    "price": str(effective_price),
                    "currency": alert.currency,
                    "url": best_offer.url,
                },
            )
            session.add(notification)
            alert.last_notified_price = effective_price
            alert.last_notified_at = datetime.now(UTC)
            sent += 1
            pending_emails.append(
                (user.email, product.name, f"{effective_price} {alert.currency}", best_offer.url)
            )
        await session.commit()

    for email, product_name, price, url in pending_emails:
        try:
            await email_service.send_price_alert(email, product_name, price, url)
        except Exception:
            logger.exception("price_alert_email_failed recipient=%s", email)
    return {"checked": checked, "sent": sent}


@celery_app.task(
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 3},
)
def check_price_alerts_task() -> dict:
    return asyncio.run(_check_price_alerts())
