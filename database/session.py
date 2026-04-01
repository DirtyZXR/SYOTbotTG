from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path
from config import settings
from database.base import Base

# Создаём директорию для БД если её нет
settings.db_path.parent.mkdir(parents=True, exist_ok=True)

# Создаём engine
engine = create_engine(
    f"sqlite:///{settings.database_path}",
    connect_args={"check_same_thread": False},
)

# Создаём сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Инициализация базы данных"""
    from models import User, Document, Test, TestResult

    # Создаём таблицы
    Base.metadata.create_all(bind=engine)
