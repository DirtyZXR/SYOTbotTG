from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, date
from typing import List, Tuple
from models.document_download import DocumentDownload
from models.user import User


class DocumentDownloadRepository:
    """Репозиторий для работы со статистикой скачиваний"""

    def __init__(self, db: Session):
        self.db = db

    def log_download(self, user_id: int, file_name: str) -> DocumentDownload:
        """Логирование скачивания файла пользователем"""
        download = DocumentDownload(user_id=user_id, file_name=file_name)
        self.db.add(download)
        self.db.commit()
        self.db.refresh(download)
        return download

    def get_user_monthly_stats(self, user_id: int, year: int, month: int) -> int:
        """Получить количество скачиваний пользователя за указанный месяц"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        return (
            self.db.query(DocumentDownload)
            .filter(
                DocumentDownload.user_id == user_id,
                DocumentDownload.downloaded_at >= start_date,
                DocumentDownload.downloaded_at < end_date,
            )
            .count()
        )

    def get_global_monthly_stats(self, year: int, month: int) -> int:
        """Получить общее количество скачиваний всеми пользователями за месяц"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)

        return (
            self.db.query(DocumentDownload)
            .filter(
                DocumentDownload.downloaded_at >= start_date,
                DocumentDownload.downloaded_at < end_date,
            )
            .count()
        )
