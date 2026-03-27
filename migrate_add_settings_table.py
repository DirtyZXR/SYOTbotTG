"""
Миграция базы данных: добавление таблицы settings
"""
from sqlalchemy import create_engine, text
from config import settings


def migrate_add_settings_table():
    """Добавить таблицу settings"""
    engine = create_engine(
        f"sqlite:///{settings.database_path}",
        connect_args={"check_same_thread": False},
    )

    with engine.connect() as conn:
        # Проверяем, существует ли таблица settings
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='settings'"))
        settings_table_exists = result.fetchone() is not None

        if not settings_table_exists:
            print("Adding settings table...")
            conn.execute(text("""
                CREATE TABLE settings (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE NOT NULL,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print("Settings table successfully created!")
        else:
            print("Settings table already exists")


if __name__ == "__main__":
    migrate_add_settings_table()
