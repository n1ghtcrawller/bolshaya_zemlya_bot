import logging

import structlog

from bot.config import LoggingSettings


def configure_logging(settings: LoggingSettings) -> None:
    level = getattr(logging, settings.level.upper(), logging.INFO)

    timestamper = structlog.processors.TimeStamper(fmt="iso")
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
    ]

    if settings.as_json:
        renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    logging.basicConfig(level=level, format="%(message)s")
    for noisy in ("aiogram.event", "aiogram.dispatcher", "asyncio"):
        logging.getLogger(noisy).setLevel(max(level, logging.INFO))


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    # Биндим имя в контекст вместо stdlib-процессора add_logger_name,
    # т.к. PrintLoggerFactory создаёт логгер без атрибута .name.
    return structlog.get_logger().bind(logger=name)
