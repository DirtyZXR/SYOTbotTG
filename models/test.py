from sqlalchemy import Column, Integer, String, JSON, DateTime
from sqlalchemy.sql import func
from database import Base


class Test(Base):
    """Модель теста"""

    __tablename__ = "tests"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    group = Column(Integer, nullable=False)  # Группа электробезопасности: 2, 3, 4
    questions = Column(JSON, nullable=False)  # Список вопросов и ответов
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Test(id={self.id}, name={self.name}, group={self.group})>"
