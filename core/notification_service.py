from datetime import datetime, timedelta

from models.test_result import TestResult
from models.user import User

ACCESS_PERIOD_DAYS = 358


def get_user_status_text(user) -> str:
    """Возвращает текстовый статус пользователя с countdown"""
    if user.is_admin:
        return "👨‍💼 Администратор"
    elif not user.is_verified or not user.access_granted_at:
        return "⏳ Документ не выдан"
    else:
        expiry = user.access_granted_at + timedelta(days=ACCESS_PERIOD_DAYS)
        days_left = (expiry.date() - datetime.now().date()).days
        if days_left > 7:
            return f"✅ Документ выдан {user.access_granted_at.strftime('%d.%m.%Y')} (осталось {days_left} дн.)"
        elif days_left > 0:
            return f"⚠️ Документ выдан {user.access_granted_at.strftime('%d.%m.%Y')} (осталось {days_left} дн. — истекает!)"
        else:
            return "❌ Допуск истёк"


class NotificationService:
    """Сервис уведомлений"""

    @staticmethod
    def format_admin_notification(user: User, test_result: TestResult) -> str:
        """
        Форматирование уведомления для администратора
        о прохождении теста
        """
        message = (
            f"🎉 Тест пройден успешно!\n\n"
            f"👤 Пользователь: {user.full_name or 'Не указано'}\n"
            f"📧 Email: {user.email}\n"
            f"📱 Telegram: @{user.username or 'Нет username'}\n"
            f"📊 Результат: {test_result.percentage:.1f}% ({test_result.score}/{test_result.total})\n"
            f"📅 Дата: {test_result.passed_at.strftime('%d.%m.%Y %H:%M')}\n"
        )

        return message

    @staticmethod
    def format_admin_user_list(users: list) -> str:
        """Форматирование списка зарегистрированных пользователей"""
        if not users:
            return "Нет зарегистрированных пользователей"

        message = "📋 Зарегистрированные пользователи:\n\n"

        for user in users:
            status = get_user_status_text(user)
            message += (
                f"👤 {user.full_name or 'Не указано'}\n"
                f"📧 {user.email}\n"
                f"📱 @{user.username or 'Нет username'}\n"
                f"📅 {user.created_at.strftime('%d.%m.%Y')}\n"
                f"📌 {status}\n\n"
            )

        return message
