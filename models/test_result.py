from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from database import Base


class TestResult(Base):
    """Модель результата теста"""

    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    test_id = Column(Integer, ForeignKey("tests.id"), nullable=False)
    score = Column(Integer, nullable=False)  # Количество правильных ответов
    total = Column(Integer, nullable=False)  # Общее количество вопросов
    percentage = Column(Float, nullable=False)  # Процент правильных ответов
    passed = Column(Integer, default=0)  # 1 = пройден, 0 = не пройден
    passed_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<TestResult(id={self.id}, score={self.score}/{self.total}, percentage={self.percentage}%)>"
