import json
import random
from pathlib import Path
from typing import List, Dict, Optional

TESTS_FILE = Path("data/tests/test.json")
QUESTIONS_PER_TEST = 15
GROUP3_UNLOCK_DAYS = 90  # 3 месяца


def load_questions(group: int) -> List[Dict]:
    """Загрузить все вопросы группы из test.json"""
    if not TESTS_FILE.exists():
        return []
    with open(TESTS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    group_key = f"group{group}"
    group_data = data.get(group_key, {})
    all_questions = []
    for ticket_name, questions in group_data.items():
        all_questions.extend(questions)
    return all_questions


def get_unique_questions(group: int) -> List[Dict]:
    """Получить уникальные вопросы (дедупликация по тексту)"""
    questions = load_questions(group)
    seen = set()
    unique = []
    for q in questions:
        if q["question"] not in seen:
            seen.add(q["question"])
            unique.append(q)
    return unique


def select_random_questions(group: int, count: int = QUESTIONS_PER_TEST) -> List[Dict]:
    """Выбрать случайные уникальные вопросы для теста"""
    unique = get_unique_questions(group)
    count = min(count, len(unique))
    return random.sample(unique, count)


def check_answer(question: Dict, selected_option: str) -> bool:
    """Проверить правильность ответа"""
    return selected_option == question["correct_answer"]


def calculate_results(questions: List[Dict], answers: Dict[int, str]) -> Dict:
    """Рассчитать результаты теста"""
    correct = 0
    details = []
    for i, q in enumerate(questions):
        user_answer = answers.get(str(i), "")  # Answers keys are strings from FSM
        is_correct = check_answer(q, user_answer)
        if is_correct:
            correct += 1
        details.append(
            {
                "question": q["question"],
                "user_answer": user_answer,
                "correct_answer": q["correct_answer"],
                "is_correct": is_correct,
            }
        )
    total = len(questions)
    percentage = (correct / total * 100) if total > 0 else 0
    passed = percentage >= 90
    return {
        "correct": correct,
        "total": total,
        "percentage": percentage,
        "passed": passed,
        "details": details,
    }


def format_results_message(results: Dict, user_name: str, group: int) -> str:
    """Форматировать сообщение с результатами"""
    status = "✅ СДАНО" if results["passed"] else "❌ НЕ СДАНО"
    msg = (
        f"📝 <b>Результаты теста — Группа {group}</b>\n"
        f"👤 {user_name}\n"
        f"📊 {results['correct']}/{results['total']} ({results['percentage']:.1f}%) — {status}\n\n"
    )
    for i, d in enumerate(results["details"], 1):
        icon = "✅" if d["is_correct"] else "❌"
        msg += f"{icon} <b>Вопрос {i}:</b> {d['question']}\n"
        if d["is_correct"]:
            msg += f"   Ответ: {d['user_answer']}\n"
        else:
            msg += f"   Ваш ответ: {d['user_answer'] or 'Нет ответа'}\n"
            msg += f"   Правильный: {d['correct_answer']}\n"
        msg += "\n"
    return msg


def is_group_available(user, group: int) -> bool:
    """Проверить доступность группы для пользователя"""
    from datetime import datetime, timedelta

    if not user or user.company != "intellectika":
        return False

    if group == 2:
        return user.group2_passed_at is None
    elif group == 3:
        if user.group3_passed_at is not None:
            return False
        if user.group2_passed_at is None:
            return False
        if not user.access_granted_at:
            return False
        unlock_date = user.access_granted_at + timedelta(days=GROUP3_UNLOCK_DAYS)
        return datetime.now() >= unlock_date
    return False


def get_group3_unlock_date(user) -> Optional[object]:
    """Получить дату открытия группы 3"""
    from datetime import timedelta

    if user and user.access_granted_at:
        return user.access_granted_at + timedelta(days=GROUP3_UNLOCK_DAYS)
    return None
