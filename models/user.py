from sqlalchemy import Column, Integer, String, DateTime, Boolean
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
    company = Column(String)  # Ключ компании из COMPANY_ROOTS (company1, company2)
    created_at = Column(DateTime, server_default=func.now())
    access_granted_at = Column(DateTime)  # Дата выдачи документа

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, email={self.email})>"
