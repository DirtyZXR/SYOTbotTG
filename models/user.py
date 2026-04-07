from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from database import Base


class User(Base):
    """Модель пользователя"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    full_name_lower = Column(
        String
    )  # ФИО в нижнем регистре для регистронезависимого поиска (кириллица)
    username = Column(String)  # Telegram username
    is_pending = Column(Boolean, default=True)  # Ожидает подтверждения админом
    is_verified = Column(Boolean, default=False)  # Документ выдан (допуск активен)
    is_admin = Column(Boolean, default=False)  # Администратор системы
    notified_7d = Column(Boolean, default=False)  # Уведомление за 7 дней отправлено
    notified_1d = Column(Boolean, default=False)  # Уведомление за 1 день отправлено
    companies = Column(JSON, default=list)  # Список компаний пользователя
    group2_passed_at = Column(DateTime)  # Когда сдана группа 2
    group3_passed_at = Column(DateTime)  # Когда сдана группа 3
    notified_3g_7d = Column(
        Boolean, default=False
    )  # Уведомление за 7 дней до открытия группы 3
    notified_3g_1d = Column(
        Boolean, default=False
    )  # Уведомление за 1 день до открытия группы 3
    created_at = Column(DateTime, server_default=func.now())
    access_granted_at = Column(DateTime)  # Дата выдачи документа

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, email={self.email}, companies={self.companies})>"
