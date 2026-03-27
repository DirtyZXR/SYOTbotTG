from typing import List, Dict, Optional
from database import SessionLocal, TestRepository, TestResultRepository
from models.test import Test
from models.test_result import TestResult
from models.user import User


class TestService:
    """Сервис работы с тестами"""

    def __init__(self):
        pass

    @staticmethod
    def get_test_by_group(group: int) -> Optional[Test]:
        """Получение теста по группе"""
        db = SessionLocal()
        test_repo = TestRepository(db)

        tests = test_repo.get_by_group(group)
        db.close()
        return tests[0] if tests else None

    @staticmethod
    def get_all_tests() -> List[Test]:
        """Получение всех тестов"""
        db = SessionLocal()
        test_repo = TestRepository(db)

        tests = test_repo.get_all()
        db.close()
        return tests

    @staticmethod
    def check_answers(
        test: Test, user_answers: Dict[int, int]
    ) -> tuple[int, int, float, List[Dict]]:
        """
        Проверка ответов пользователя
        Возвращает (correct, total, percentage, detailed_results)
        """
        questions = test.questions
        total = len(questions)
        correct = 0
        detailed_results = []

        for idx, question in enumerate(questions):
            question_num = idx + 1
            user_answer = user_answers.get(question_num)
            correct_answer = question["correct_answer"]

            is_correct = user_answer == correct_answer
            if is_correct:
                correct += 1

            detailed_results.append(
                {
                    "question": question["question"],
                    "user_answer": user_answer,
                    "correct_answer": correct_answer,
                    "is_correct": is_correct,
                    "options": question["options"],
                }
            )

        percentage = (correct / total * 100) if total > 0 else 0
        return correct, total, percentage, detailed_results

    @staticmethod
    def format_results(
        correct: int, total: int, percentage: float, detailed_results: List[Dict]
    ) -> str:
        """Форматирование результатов с подсветкой"""
        result_text = f"📊 Результаты теста:\n\n"
        result_text += f"Правильных ответов: {correct}/{total}\n"
        result_text += f"Процент: {percentage:.1f}%\n\n"

        if percentage >= 90:
            result_text += "✅ Тест пройден успешно!\n\n"
        else:
            result_text += "❌ Тест не пройден (нужно ≥90%)\n\n"

        result_text += "Детали:\n"

        for idx, detail in enumerate(detailed_results):
            icon = "✅" if detail["is_correct"] else "❌"
            result_text += f"\n{idx + 1}. {icon} {detail['question']}\n"
            result_text += f"   Ваш ответ: {detail['user_answer']}\n"
            if not detail["is_correct"]:
                result_text += f"   Правильный ответ: {detail['correct_answer']}\n"

        return result_text

    @staticmethod
    def save_test_result(
        user: User, test: Test, correct: int, total: int, percentage: float
    ) -> TestResult:
        """Сохранение результата теста"""
        db = SessionLocal()
        result_repo = TestResultRepository(db)

        passed = 1 if percentage >= 90 else 0

        result = result_repo.create_result(
            user_id=user.id,
            test_id=test.id,
            score=correct,
            total=total,
            percentage=percentage,
            passed=passed,
        )

        db.close()
        return result

    @staticmethod
    def get_user_results(user_id: int) -> List[TestResult]:
        """Получение результатов пользователя"""
        db = SessionLocal()
        result_repo = TestResultRepository(db)

        results = result_repo.get_by_user(user_id)
        db.close()
        return results

    @staticmethod
    def load_tests_from_json(folder_path: str) -> int:
        """Загрузка тестов из JSON файлов в папке"""
        import json
        from pathlib import Path

        db = SessionLocal()
        test_repo = TestRepository(db)

        added_count = 0
        test_folder = Path(folder_path)

        if not test_folder.exists():
            db.close()
            return 0

        for json_file in test_folder.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    test_data = json.load(f)

                # Проверяем формат
                if not all(
                    key in test_data
                    for key in ["name", "group", "questions"]
                ):
                    continue

                test_repo.create_test(
                    name=test_data["name"],
                    group=test_data["group"],
                    questions=test_data["questions"],
                )
                added_count += 1
            except Exception:
                continue

        db.close()
        return added_count
