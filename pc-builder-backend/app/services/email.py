import logging
from email.message import EmailMessage

import aiosmtplib

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    async def _send(self, recipient: str, subject: str, text: str, html: str | None = None) -> None:
        if not settings.smtp_host:
            logger.info("email_queued recipient=%s subject=%s smtp=disabled", recipient, subject)
            return
        message = EmailMessage()
        message["From"] = settings.smtp_from_email
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(text)
        if html:
            message.add_alternative(html, subtype="html")
        await aiosmtplib.send(
            message,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_username,
            password=(
                settings.smtp_password.get_secret_value() if settings.smtp_password else None
            ),
            start_tls=settings.smtp_use_tls,
            timeout=20,
        )

    async def send_verification(self, email: str, token: str) -> None:
        link = f"{settings.frontend_url.rstrip('/')}/verify-email?token={token}"
        await self._send(
            email,
            "Подтверждение email",
            f"Подтвердите email: {link}",
            f'<p>Подтвердите email:</p><p><a href="{link}">Подтвердить</a></p>',
        )

    async def send_password_reset(self, email: str, token: str) -> None:
        link = f"{settings.frontend_url.rstrip('/')}/reset-password?token={token}"
        await self._send(
            email,
            "Сброс пароля",
            f"Сменить пароль: {link}",
            f'<p>Для смены пароля откройте:</p><p><a href="{link}">Сменить пароль</a></p>',
        )

    async def send_price_alert(self, email: str, product_name: str, price: str, url: str) -> None:
        await self._send(
            email,
            f"Цена снизилась: {product_name}",
            f"Цена {product_name} достигла {price}. Предложение: {url}",
            f'<p>Цена <strong>{product_name}</strong> достигла {price}.</p><p><a href="{url}">Открыть предложение</a></p>',
        )


email_service = EmailService()
