import logging
import sys
import os
from pathlib import Path
from logging.handlers import RotatingFileHandler


def _get_base_dir() -> Path:
    """Определяет базовую директорию: рядом с EXE или со скриптом."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def setup_logger(name: str = "SYOTbot", level: int = logging.INFO) -> logging.Logger:
    """Настройка логирования для проекта"""

    # Создаем логгер
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Избегаем дублирования логгеров
    if logger.handlers:
        return logger

    # Создаем форматтер
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Создаем папку для логов
    log_dir = _get_base_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Консольный хендлер
    if sys.stdout is not None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Лог-файл не должен блокировать запуск приложения.
    try:
        file_handler = RotatingFileHandler(
            log_dir / "bot.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError as exc:
        logger.warning(
            "File logging is unavailable (%s). Continuing with console logging only.",
            exc,
        )

    return logger


# Создаем глобальный логгер
logger = setup_logger("SYOTbot", logging.INFO)
