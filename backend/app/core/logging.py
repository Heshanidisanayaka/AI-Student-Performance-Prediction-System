import logging
import sys
from app.core.config import settings


def setup_logging() -> logging.Logger:
    """Configures centralized structured logging for the application."""
    log_format = (
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
    )
    date_format = "%Y-%m-%d %H:%M:%S"

    log_level = getattr(logging, settings.LOG_LEVEL, logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").handlers = []

    logger = logging.getLogger("student_perf_api")
    logger.setLevel(log_level)
    return logger


logger = setup_logging()
