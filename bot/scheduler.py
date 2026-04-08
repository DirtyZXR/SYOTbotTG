import asyncio
from datetime import datetime, timedelta, timezone

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from core.notification_service import NotificationService
from database import SessionLocal
from database.user_repo import UserRepository
from utils import logger

ACCESS_PERIOD_DAYS = 358
MSK_TZ = timezone(timedelta(hours=3))


async def run_scheduler(bot):
    """Фоновая задача: ежедневно в 08:00 МСК"""
    while True:
        now_msk = datetime.now(MSK_TZ)
        target = now_msk.replace(hour=8, minute=0, second=0, microsecond=0)
        if target <= now_msk:
            target += timedelta(days=1)
        sleep_seconds = (target - now_msk).total_seconds()

        logger.info(f"Scheduler: next check in {sleep_seconds / 3600:.1f} hours")
        await asyncio.sleep(sleep_seconds)

        try:
            await _run_daily_checks(bot)
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)


async def _run_daily_checks(bot):
    """Ежедневная проверка истечения допусков и отправка уведомлений"""
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)

        # 1. Истёкшие — снять верификацию
        expired = user_repo.get_expired_users()
        for user in expired:
            user_repo.unverify_user(user)
            logger.info(f"Expired: {user.full_name} (id={user.telegram_id})")

        # 2. Уведомление за 7 дней
        users_7d = user_repo.get_expiring_users(7, "notified_7d")
        for user in users_7d:
            try:
                await bot.send_message(
                    user.telegram_id,
                    f"{user.full_name}, ваш допуск истекает через 7 дней. "
                    f"Обратитесь к администратору для продления.",
                )
                user_repo.mark_notified(user, "notified_7d")
            except Exception as e:
                logger.warning(f"Failed to notify {user.telegram_id}: {e}")

        # 3. Уведомление за 1 день
        users_1d = user_repo.get_expiring_users(1, "notified_1d")
        for user in users_1d:
            try:
                await bot.send_message(
                    user.telegram_id,
                    f"{user.full_name}, ваш допуск истекает завтра! "
                    f"Срочно обратитесь к администратору.",
                )
                user_repo.mark_notified(user, "notified_1d")
            except Exception as e:
                logger.warning(f"Failed to notify {user.telegram_id}: {e}")

        # 4. Уведомление админов об истечении 3 группы у пользователей
        expired_g3_users = user_repo.get_users_with_expired_group3()
        if expired_g3_users:
            admin_ids = user_repo.get_admin_ids()
            message = NotificationService.format_group3_expiration_notification(
                expired_g3_users
            )
            for admin_id in admin_ids:
                try:
                    await bot.send_message(admin_id, message)
                except Exception as e:
                    logger.warning(f"Failed to notify admin {admin_id}: {e}")

        # 5. Уведомление об открытии 3 группы (за 7 и 1 день)
        for days, days_str, flag in [
            (7, "дней", "notified_3g_7d"),
            (1, "день", "notified_3g_1d"),
        ]:
            users_opening = user_repo.get_users_for_3g_notification(days, flag)
            for user in users_opening:
                try:
                    await bot.send_message(
                        user.telegram_id,
                        f"Через {days} {days_str} у вас откроется тест на III группу до 1000В, его необходимо будет пройти.",
                    )
                    user_repo.mark_notified(user, flag)
                except Exception as e:
                    logger.warning(
                        f"Failed to notify {user.telegram_id} about 3g opening in {days}d: {e}"
                    )

        # 6. Уведомления об истечении 3 группы (за 7 и 1 день)
        admin_ids = user_repo.get_admin_ids()
        for days, days_str, flag in [
            (7, "дней", "notified_3g_exp_7d"),
            (1, "день", "notified_3g_exp_1d"),
        ]:
            users_expiring = user_repo.get_users_for_group3_expiration_warning(db, days)
            for user in users_expiring:
                try:
                    await bot.send_message(
                        user.telegram_id,
                        f"Срок действия удостоверения по электробезопасности на III группу до 1000В заканчивается через {days} {days_str}. Для продления удостоверения просьба обратиться в службу охраны труда.",
                    )

                    keyboard = InlineKeyboardMarkup(
                        inline_keyboard=[
                            [
                                InlineKeyboardButton(
                                    text="Продлить удостоверение",
                                    callback_data=f"admin_grant_document_{user.id}",
                                )
                            ]
                        ]
                    )

                    for admin_id in admin_ids:
                        try:
                            await bot.send_message(
                                admin_id,
                                f"У сотрудника {user.full_name} через {days} {days_str} истекает удостоверение на III группу, нужно обновить.",
                                reply_markup=keyboard,
                            )
                        except Exception as e:
                            logger.warning(
                                f"Failed to notify admin {admin_id} about 3g exp for {user.telegram_id}: {e}"
                            )

                    user_repo.mark_notified(user, flag)
                except Exception as e:
                    logger.warning(
                        f"Failed to notify {user.telegram_id} about 3g exp in {days}d: {e}"
                    )

        # Обновляем лог
        logger.info(
            f"Scheduler done: expired={len(expired)}, "
            f"7d={len(users_7d)}, 1d={len(users_1d)}, "
            f"expired_g3_admins_notified={len(expired_g3_users)}"
        )
    finally:
        db.close()
