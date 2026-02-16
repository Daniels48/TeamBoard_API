import logging
import logging.config
import time

from app.core.config import settings

LOG_LEVEL = settings.logging.log_level.upper()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": (
                "%(asctime)s.%(msecs)03dZ "
                "%(levelname)s "
                "%(name)s "
                "%(filename)s "
                "%(lineno)d "
                "%(message)s"
            ),
            "rename_fields": {
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger"
            },
            "datefmt": "%Y-%m-%dT%H:%M:%S",
        },
    },

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
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


