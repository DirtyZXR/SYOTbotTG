"""
Миграция базы данных: добавление поля is_admin в таблицу users
"""
from sqlalchemy import create_engine, text
from config import settings


def migrate_add_is_admin():
    """Добавить поле is_admin в таблицу users"""
    engine = create_engine(
        f"sqlite:///{settings.database_path}",
        connect_args={"check_same_thread": False},
    )

    with engine.connect() as conn:
        # Проверяем, существует ли уже поле is_admin
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]

        if "is_admin" not in columns:
            print("Adding is_admin column to users table...")
            conn.execute(text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
            conn.commit()
            print("is_admin column successfully added!")
        else:
            print("is_admin column already exists in users table")

        # Проверяем результат
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result.fetchall()]
        print(f"Current columns in users table: {', '.join(columns)}")


if __name__ == "__main__":
    migrate_add_is_admin()
