from sqlalchemy.orm import Session
from models.test_result import TestResult
from typing import List


class TestResultRepository:
    """Репозиторий для работы с результатами тестов"""

    def __init__(self, db: Session):
        self.db = db

    def create_result(
        self,
        user_id: int,
        test_id: int,
        score: int,
        total: int,
        percentage: float,
        passed: int,
    ) -> TestResult:
        """Создание результата теста"""
        result = TestResult(
            user_id=user_id,
            test_id=test_id,
            score=score,
            total=total,
            percentage=percentage,
            passed=passed,
        )
        self.db.add(result)
        self.db.commit()
        self.db.refresh(result)
        return result

    def get_by_user(self, user_id: int) -> List[TestResult]:
        """Получение результатов пользователя"""
        return (
            self.db.query(TestResult)
            .filter(TestResult.user_id == user_id)
            .all()
        )

    def get_by_user_and_test(
        self, user_id: int, test_id: int
    ) -> List[TestResult]:
        """Получение результатов пользователя по конкретному тесту"""
        return (
            self.db.query(TestResult)
            .filter(
                TestResult.user_id == user_id,
                TestResult.test_id == test_id,
            )
            .all()
        )

    def get_all(self) -> List[TestResult]:
        """Получение всех результатов"""
        return self.db.query(TestResult).all()

    def get_passed_results(self) -> List[TestResult]:
        """Получение только пройденных тестов"""
        return self.db.query(TestResult).filter(TestResult.passed == 1).all()
