import logging
from pathlib import Path

import pytest

from app.core.logging import configure_logging
from app.core.settings import Settings


def test_configure_logging_does_not_add_duplicate_handlers(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]

    try:
        root_logger.handlers.clear()
        settings = Settings(log_level="INFO")

        configure_logging(settings)
        configure_logging(settings)

        assert len(root_logger.handlers) == 1
    finally:
        root_logger.handlers = original_handlers


def test_configure_logging_sets_root_level(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    root_logger = logging.getLogger()
    original_level = root_logger.level
    original_handlers = root_logger.handlers[:]

    try:
        settings = Settings(log_level="ERROR")
        configure_logging(settings)

        assert root_logger.level == logging.ERROR
    finally:
        root_logger.setLevel(original_level)
        root_logger.handlers = original_handlers
