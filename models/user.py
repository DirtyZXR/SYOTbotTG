from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from database.session import Base


class User(Base):
    """Модель пользователя"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(Integer, unique=True, index=True, nullable=False)
    email = Column(String, nullable=False, unique=True)
    full_name = Column(String)
    username = Column(String)  # Telegram username
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)  # Администратор системы
    created_at = Column(DateTime, server_default=func.now())
    access_granted_at = Column(DateTime)

    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, email={self.email})>"
