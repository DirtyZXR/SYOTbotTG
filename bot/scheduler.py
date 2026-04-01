import asyncio
from datetime import datetime, timedelta, timezone

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

        logger.info(
            f"Scheduler done: expired={len(expired)}, "
            f"7d={len(users_7d)}, 1d={len(users_1d)}"
        )
    finally:
        db.close()
