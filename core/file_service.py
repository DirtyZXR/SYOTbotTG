from pathlib import Path
from typing import List, Tuple
from config import settings


class FileService:
    """Сервис работы с файловой системой"""

    def __init__(self):
        pass

    @staticmethod
    def get_documents_root() -> Path:
        """Получить путь к корневой папке документов"""
        return Path(settings.documents_path)

    @staticmethod
    def get_folder_contents(folder_path: str) -> Tuple[List[str], List[str]]:
        """
        Получить содержимое папки

        Returns:
            (folders, files) - кортеж списков имен папок и файлов
        """
        folder = Path(folder_path)

        if not folder.exists() or not folder.is_dir():
            return [], []

        folders = []
        files = []

        for item in sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
            if item.is_dir():
                folders.append(item.name)
            elif item.is_file():
                files.append(item.name)

        return folders, files

    @staticmethod
    def is_file(path: str) -> bool:
        """Проверить, является ли путь файлом"""
        return Path(path).is_file()

    @staticmethod
    def is_folder(path: str) -> bool:
        """Проверить, является ли путь папкой"""
        return Path(path).is_dir()

    @staticmethod
    def file_exists(path: str) -> bool:
        """Проверить существование файла"""
        return Path(path).exists()
