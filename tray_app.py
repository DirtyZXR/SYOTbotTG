"""Запуск бота в системном трее"""

import sys
import os
import threading
import asyncio
import logging
from pathlib import Path
from PIL import Image, ImageDraw

import pystray
from pystray import Menu, MenuItem

# Базовый путь — директория, где лежит EXE (или скрипт при обычном запуске)
if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

# Создание папки для логов
log_dir = BASE_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)

# Настройка логирования
log_handlers = [logging.FileHandler(log_dir / "bot.log", encoding="utf-8")]
if sys.stdout is not None:
    log_handlers.append(logging.StreamHandler(sys.stdout))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=log_handlers,
)
logger = logging.getLogger(__name__)


def create_icon():
    """Создаёт иконку для системного трея"""
    # Создаём простую иконку
    image = Image.new("RGB", (64, 64), color="blue")
    dc = ImageDraw.Draw(image)

    # Рисуем букву "S" (от SYOT)
    dc.text((20, 15), "S", fill="white", font=None)

    # Рисуем индикатор работы (зелёный кружок)
    dc.ellipse((45, 5, 60, 20), fill="green")

    return image


class BotTrayApp:
    """Приложение бота в системном трее"""

    def __init__(self):
        self.icon = None
        self.bot_thread = None
        self.loop = None
        self.bot = None
        self.running = False

    def start_bot(self):
        """Запуск бота в отдельном потоке"""
        logger.info("Запуск бота...")
        self.running = True

        # Создаём новый event loop для потока
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        try:
            # Импортируем и запускаем бота
            from bot.bot import main as bot_main

            self.loop.run_until_complete(bot_main())
        except Exception as e:
            logger.error(f"Ошибка запуска бота: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Бот остановлен")

    def on_start(self, icon, item):
        """Обработчик запуска бота"""
        if self.bot_thread is None or not self.bot_thread.is_alive():
            logger.info("Запуск бота из меню...")
            self.bot_thread = threading.Thread(target=self.start_bot, daemon=True)
            self.bot_thread.start()
            icon.notify("Бот запущен", "SYOTbotTG")
        else:
            icon.notify("Бот уже запущен", "SYOTbotTG")

    def on_stop(self, icon, item):
        """Обработчик остановки бота"""
        if self.loop and self.loop.is_running():
            logger.info("Остановка бота...")
            self.loop.call_soon_threadsafe(self.loop.stop)
            icon.notify("Бот остановлен", "SYOTbotTG")
        else:
            icon.notify("Бот не запущен", "SYOTbotTG")

    def on_status(self, icon, item):
        """Показать статус бота"""
        if self.running:
            status = "Бот работает"
        else:
            status = "Бот остановлен"
        icon.notify(status, "Статус SYOTbotTG")

    def on_open_logs(self, icon, item):
        """Открыть папку с логами"""
        logs_dir = BASE_DIR / "logs"
        logs_dir.mkdir(exist_ok=True)

        import subprocess
        import os

        subprocess.Popen(f'explorer "{os.path.abspath(logs_dir)}"')

    def on_exit(self, icon, item):
        """Выход из приложения"""
        logger.info("Завершение работы...")
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        icon.stop()

    def run(self):
        """Запуск приложения в системном трее"""
        # Создаём директорию для логов
        Path(BASE_DIR / "logs").mkdir(parents=True, exist_ok=True)

        # Создаём иконку
        image = create_icon()

        # Создаём меню
        menu = Menu(
            MenuItem("Запустить бота", self.on_start),
            MenuItem("Остановить бота", self.on_stop),
            MenuItem("Статус", self.on_status),
            Menu.SEPARATOR,
            MenuItem("Открыть логи", self.on_open_logs),
            Menu.SEPARATOR,
            MenuItem("Выход", self.on_exit),
        )

        # Создаём иконку в трее
        self.icon = pystray.Icon(
            "SYOTbotTG", image, "SYOTbotTG - Бот по охране труда", menu
        )

        # Автоматически запускаем бота при старте
        logger.info("Автоматический запуск бота...")
        self.bot_thread = threading.Thread(target=self.start_bot, daemon=True)
        self.bot_thread.start()

        # Запускаем иконку в трее
        logger.info("Приложение запущено в системном трее")
        self.icon.run()


if __name__ == "__main__":
    app = BotTrayApp()
    app.run()
