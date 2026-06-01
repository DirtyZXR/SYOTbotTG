from typing import List, Optional
from pathlib import Path
from database import SessionLocal, DocumentRepository
from models.document import Document
from config import DOCUMENT_CATEGORIES


class DocumentService:
    """Сервис работы с документами"""

    def __init__(self):
        pass

    @staticmethod
    def get_documents_by_category(category: str) -> List[Document]:
        """Получение документов по категории"""
        db = SessionLocal()
        doc_repo = DocumentRepository(db)

        documents = doc_repo.get_by_category(category)
        db.close()
        return documents

    @staticmethod
    def get_documents_by_subcategory(category: str, subcategory: str) -> List[Document]:
        """Получение документов по подкатегории"""
        db = SessionLocal()
        doc_repo = DocumentRepository(db)

        documents = doc_repo.get_by_subcategory(category, subcategory)
        db.close()
        return documents

    @staticmethod
    def get_document_by_id(doc_id: int) -> Optional[Document]:
        """Получение документа по ID"""
        db = SessionLocal()
        doc_repo = DocumentRepository(db)

        document = doc_repo.get_by_id(doc_id)
        db.close()
        return document

    @staticmethod
    def get_all_categories() -> dict:
        """Получение всех категорий"""
        return DOCUMENT_CATEGORIES

    @staticmethod
    def scan_documents_folder() -> int:
        """
        Сканирование папки с документами и добавление в базу
        Возвращает количество добавленных документов
        """
        from config import settings

        db = SessionLocal()
        doc_repo = DocumentRepository(db)

        docs_path = Path(settings.documents_path)
        if not docs_path.exists():
            db.close()
            return 0

        added_count = 0
        for category_key, category_data in DOCUMENT_CATEGORIES.items():
            category_path = docs_path / category_key

            if not category_path.exists():
                continue

            # Обработка подкатегорий
            if "subcategories" in category_data:
                if isinstance(category_data["subcategories"], dict):
                    # Вложенные подкатегории (электробезопасность)
                    for sub_key, sub_data in category_data["subcategories"].items():
                        sub_path = category_path / sub_key
                        if sub_path.exists():
                            added_count += DocumentService._add_files_from_path(
                                db,
                                doc_repo,
                                sub_path,
                                category_key,
                                sub_data["name"],
                                added_count,
                            )
                else:
                    # Простые подкатегории
                    for subcategory in category_data["subcategories"]:
                        sub_path = category_path / subcategory
                        if sub_path.exists():
                            added_count += DocumentService._add_files_from_path(
                                db,
                                doc_repo,
                                sub_path,
                                category_key,
                                subcategory,
                                added_count,
                            )

        db.close()
        return added_count

    @staticmethod
    def _add_files_from_path(
        db, doc_repo, path: Path, category: str, subcategory: str, added_count: int
    ) -> int:
        """Добавление файлов из папки в базу данных"""
        for file_path in path.rglob("*"):
            if file_path.is_file():
                # Проверяем, нет ли уже такого файла в базе
                existing = doc_repo.get_by_id(
                    int(file_path.stat().st_ctime) % 1000000
                )  # Простой хеш
                if not existing:
                    doc_repo.create_document(
                        name=file_path.name,
                        file_path=str(file_path),
                        category=category,
                        subcategory=subcategory,
                    )
                    added_count += 1
        return added_count
