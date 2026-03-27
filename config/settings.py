from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Настройки бота"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram
    bot_token: str
    admin_id: int

    # Database
    database_path: str = "./data/bot.db"

    # Documents
    documents_path: str = "./data/documents"

    # Security
    security_code: str = "123456"  # Код, который админ сообщает пользователям

    # Paths
    @property
    def db_path(self) -> Path:
        return Path(self.database_path)

    @property
    def docs_path(self) -> Path:
        return Path(self.documents_path)


settings = Settings()
