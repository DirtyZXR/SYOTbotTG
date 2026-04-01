from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
    Float,
)
from sqlalchemy.sql import func
from database import Base


class TestResult(Base):
    """Результаты прохождения тестов"""

    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group = Column(Integer, nullable=False)  # 2 или 3
    score = Column(Integer, nullable=False)
    total = Column(Integer, nullable=False)
    percentage = Column(Float, nullable=False)
    passed = Column(Integer, default=0)  # 1=сдано, 0=не сдано
    passed_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<TestResult(user_id={self.user_id}, group={self.group}, passed={self.passed})>"
