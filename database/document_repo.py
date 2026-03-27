from sqlalchemy.orm import Session
from models.document import Document
from typing import Optional, List


class DocumentRepository:
    """Репозиторий для работы с документами"""

    def __init__(self, db: Session):
        self.db = db

    def create_document(
        self,
        name: str,
        file_path: str,
        category: str,
        subcategory: str,
    ) -> Document:
        """Создание документа"""
        document = Document(
            name=name,
            file_path=file_path,
            category=category,
            subcategory=subcategory,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_by_id(self, doc_id: int) -> Optional[Document]:
        """Получение документа по ID"""
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def get_by_category(self, category: str) -> List[Document]:
        """Получение документов по категории"""
        return self.db.query(Document).filter(Document.category == category).all()

    def get_by_subcategory(
        self, category: str, subcategory: str
    ) -> List[Document]:
        """Получение документов по подкатегории"""
        return (
            self.db.query(Document)
            .filter(
                Document.category == category,
                Document.subcategory == subcategory,
            )
            .all()
        )

    def get_all(self) -> List[Document]:
        """Получение всех документов"""
        return self.db.query(Document).all()

    def delete_document(self, document: Document) -> None:
        """Удаление документа"""
        self.db.delete(document)
        self.db.commit()
