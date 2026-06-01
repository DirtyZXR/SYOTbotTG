from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
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

    def get_history_grouped(self, user_id: int = None) -> List[dict]:
        """Получить сгруппированную историю скачиваний."""
        year_expr = func.strftime("%Y", DocumentDownload.downloaded_at).label("year")
        month_expr = func.strftime("%m", DocumentDownload.downloaded_at).label("month")

        query = self.db.query(
            year_expr, month_expr, func.count(DocumentDownload.id).label("count")
        )

        if user_id is not None:
            query = query.filter(DocumentDownload.user_id == user_id)

        query = query.group_by(year_expr, month_expr).order_by(
            year_expr.desc(), month_expr.desc()
        )

        results = query.all()
        return [
            {"year": row.year, "month": row.month, "count": row.count}
            for row in results
        ]

    def get_download_leaderboard(
        self, limit: int, offset: int
    ) -> Tuple[List[dict], int]:
        """Получить таблицу лидеров по скачиваниям."""
        total_count = self.db.query(User).filter(User.is_verified == True).count()

        query = (
            self.db.query(User, func.count(DocumentDownload.id).label("downloads"))
            .outerjoin(DocumentDownload, User.id == DocumentDownload.user_id)
            .filter(User.is_verified == True)
            .group_by(User.id)
            .order_by(func.count(DocumentDownload.id).desc(), User.id)
            .limit(limit)
            .offset(offset)
        )

        results = query.all()
        return [{"user": row[0], "downloads": row[1]} for row in results], total_count
