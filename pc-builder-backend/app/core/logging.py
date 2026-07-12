import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id", default=None)


class ContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        record.user_id = user_id_ctx.get()
        return True


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(ContextFilter())
    if settings.log_json:
        handler.setFormatter(
            JsonFormatter(
                "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(user_id)s",
                rename_fields={"levelname": "level", "name": "logger"},
            )
        )
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s "
                "user_id=%(user_id)s %(message)s"
            )
        )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())
