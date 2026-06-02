from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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

    # Создаём таблицы
    Base.metadata.create_all(bind=engine)

    # Синхронизируем alembic_version с текущим состоянием моделей
    from alembic.config import Config as AlembicConfig
    from alembic import command

    alembic_cfg = AlembicConfig("alembic.ini")
    try:
        command.stamp(alembic_cfg, "head")
    except Exception:
        pass
