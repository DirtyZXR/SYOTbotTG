from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from database.base import Base


class DocumentDownload(Base):
    """Модель для логирования скачиваний документов"""

    __tablename__ = "document_downloads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    file_name = Column(String, nullable=False)
    downloaded_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<DocumentDownload(user_id={self.user_id}, file_name={self.file_name}, downloaded_at={self.downloaded_at})>"
