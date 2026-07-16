import logging

from app.core.settings import Settings

_HANDLER_MARKER = "vnstocklab"
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"


def configure_logging(settings: Settings) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.log_level)

    for handler in root_logger.handlers:
        if getattr(handler, "name", None) == _HANDLER_MARKER:
            handler.setLevel(settings.log_level)
            return

    handler = logging.StreamHandler()
    handler.name = _HANDLER_MARKER
    handler.setLevel(settings.log_level)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT))
    root_logger.addHandler(handler)
