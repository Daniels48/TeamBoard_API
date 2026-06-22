import logging
import logging.config
import time

from app.core.config import settings
from app.core.observability.logging_filter import ContextFilter
from app.core.observability.logging_formatter import CustomJsonFormatter

LOG_LEVEL = settings.logging.log_level.upper()


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"context_filter": {"()": ContextFilter}},
    "formatters": {
        "json": {
            "()": CustomJsonFormatter,
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["context_filter"],
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "handlers": ["console"],
    },
}


def setup_logging():
    logging.Formatter.converter = time.gmtime
    logging.config.dictConfig(LOGGING_CONFIG)
