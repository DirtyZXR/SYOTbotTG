from sqlalchemy.orm import Session
from models.test import Test
from typing import Optional, List


class TestRepository:
    """Репозиторий для работы с тестами"""

    def __init__(self, db: Session):
        self.db = db

    def create_test(
        self, name: str, group: int, questions: dict
    ) -> Test:
        """Создание теста"""
        test = Test(
            name=name,
            group=group,
            questions=questions,
        )
        self.db.add(test)
        self.db.commit()
        self.db.refresh(test)
        return test

    def get_by_id(self, test_id: int) -> Optional[Test]:
        """Получение теста по ID"""
        return self.db.query(Test).filter(Test.id == test_id).first()

    def get_by_group(self, group: int) -> List[Test]:
        """Получение тестов по группе"""
        return self.db.query(Test).filter(Test.group == group).all()

    def get_all(self) -> List[Test]:
        """Получение всех тестов"""
        return self.db.query(Test).all()

    def delete_test(self, test: Test) -> None:
        """Удаление теста"""
        self.db.delete(test)
        self.db.commit()
