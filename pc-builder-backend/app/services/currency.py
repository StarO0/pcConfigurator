from datetime import date
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import CurrencyRate


async def update_nbp_rates(session: AsyncSession) -> int:
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.get(settings.nbp_rates_url, headers={"Accept": "application/json"})
        response.raise_for_status()
        table = response.json()[0]
    rate_date = date.fromisoformat(table["effectiveDate"])
    count = 0
    for item in table["rates"]:
        code = item["code"].upper()
        rate = Decimal(str(item["mid"]))
        existing = await session.scalar(
            select(CurrencyRate).where(
                CurrencyRate.base == code,
                CurrencyRate.quote == "PLN",
                CurrencyRate.rate_date == rate_date,
            )
        )
        if existing is None:
            session.add(
                CurrencyRate(base=code, quote="PLN", rate=rate, rate_date=rate_date, source="NBP")
            )
            count += 1
    await session.commit()
    return count


async def convert(session: AsyncSession, amount: Decimal, source: str, target: str) -> Decimal:
    source, target = source.upper(), target.upper()
    if source == target:
        return amount
    source_rate = (
        Decimal("1")
        if source == "PLN"
        else await session.scalar(
            select(CurrencyRate.rate)
            .where(CurrencyRate.base == source, CurrencyRate.quote == "PLN")
            .order_by(CurrencyRate.rate_date.desc())
            .limit(1)
        )
    )
    target_rate = (
        Decimal("1")
        if target == "PLN"
        else await session.scalar(
            select(CurrencyRate.rate)
            .where(CurrencyRate.base == target, CurrencyRate.quote == "PLN")
            .order_by(CurrencyRate.rate_date.desc())
            .limit(1)
        )
    )
    if source_rate is None or target_rate is None:
        raise ValueError(f"Missing exchange rate for {source}/{target}")
    return (amount * source_rate / target_rate).quantize(Decimal("0.01"))
