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
        group: int,
        score: int,
        total: int,
        percentage: float,
        passed: int,
    ) -> TestResult:
        """Создание результата теста"""
        result = TestResult(
            user_id=user_id,
            group=group,
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
        return self.db.query(TestResult).filter(TestResult.user_id == user_id).all()

    def get_by_user_and_group(self, user_id: int, group: int) -> List[TestResult]:
        """Получение результатов пользователя по конкретной группе"""
        return (
            self.db.query(TestResult)
            .filter(
                TestResult.user_id == user_id,
                TestResult.group == group,
            )
            .all()
        )

    def get_all(self) -> List[TestResult]:
        """Получение всех результатов"""
        return self.db.query(TestResult).all()

    def get_passed_results(self) -> List[TestResult]:
        """Получение только пройденных тестов"""
        return self.db.query(TestResult).filter(TestResult.passed == 1).all()

    def get_leaderboard(
        self, group: int, limit: int = 10, offset: int = 0
    ) -> tuple[List[dict], int]:
        """Получить таблицу лидеров для конкретной группы.
        Возвращает (список_результатов, общее_количество_участников).
        """
        from models.user import User

        # Получаем все результаты для группы
        results = (
            self.db.query(TestResult, User)
            .join(User, TestResult.user_id == User.id)
            .filter(TestResult.group == group)
            .all()
        )

        # Группируем по пользователю, выбираем лучший результат
        best_per_user = {}
        for res, user in results:
            if user.id not in best_per_user:
                best_per_user[user.id] = {"user": user, "result": res}
            else:
                current_best = best_per_user[user.id]["result"]
                # У кого балл больше, а при равном балле - кто сдал позже
                if res.score > current_best.score or (
                    res.score == current_best.score
                    and res.created_at > current_best.created_at
                ):
                    best_per_user[user.id] = {"user": user, "result": res}

        # Сортируем: сначала по score по убыванию, затем по created_at по убыванию
        leaders = list(best_per_user.values())
        leaders.sort(
            key=lambda x: (x["result"].score, x["result"].created_at), reverse=True
        )

        total_leaders = len(leaders)
        paginated_leaders = leaders[offset : offset + limit]

        return paginated_leaders, total_leaders
