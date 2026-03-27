from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path
from config import settings

# Создаём директорию для БД если её нет
settings.db_path.parent.mkdir(parents=True, exist_ok=True)

# Создаём engine
engine = create_engine(
    f"sqlite:///{settings.database_path}",
    connect_args={"check_same_thread": False},
)

# Создаём сессию
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс моделей
Base = declarative_base()


def init_db():
    """Инициализация базы данных"""
    from models import User, Document, Test, TestResult

    Base.metadata.create_all(bind=engine)
