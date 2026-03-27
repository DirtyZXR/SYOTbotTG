from sqlalchemy.orm import Session
from models import Settings
from typing import Optional


class SettingsRepository:
    """Репозиторий для работы с настройками"""

    def __init__(self, db: Session):
        self.db = db

    def get_value(self, key: str) -> Optional[str]:
        """Получение значения по ключу"""
        settings = self.db.query(Settings).filter(Settings.key == key).first()
        return settings.value if settings else None

    def set_value(self, key: str, value: str) -> Settings:
        """Установка значения по ключу"""
        settings = self.db.query(Settings).filter(Settings.key == key).first()
        if settings:
            settings.value = value
        else:
            settings = Settings(key=key, value=value)
            self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings

    def exists(self, key: str) -> bool:
        """Проверка существования ключа"""
        return self.db.query(Settings).filter(Settings.key == key).first() is not None
