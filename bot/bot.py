import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, FSInputFile
from pathlib import Path
from config import settings
from core import (
    AuthService,
    DocumentService,
    TestService,
    NotificationService,
)
from bot.keyboards import (
    get_categories_keyboard,
    get_subcategories_keyboard,
    get_documents_keyboard,
    get_test_groups_keyboard,
    get_test_answers_keyboard,
    get_main_menu_keyboard,
    get_cancel_keyboard,
    get_folder_keyboard,
    get_back_to_menu_button,
    get_admin_menu_keyboard,
    get_admin_approval_keyboard,
    get_cancel_operation_keyboard,
    get_manage_admins_keyboard,
    get_user_search_results_keyboard,
    get_admin_user_keyboard,
    get_admin_delete_confirm_keyboard,
    get_access_date_keyboard,
    get_profile_keyboard,
    get_company_selection_keyboard,
)
from bot.states import RegistrationForm, FileBrowserState, AdminState, ProfileState
from database import init_db
from utils import logger

# Инициализация бота
bot = Bot(
    token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

# Регистрация middleware авторизации
from bot.middleware import AuthMiddleware

dp.message.middleware(AuthMiddleware())
dp.callback_query.middleware(AuthMiddleware())


# ==================== Command Handlers ====================


@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    await state.clear()

    if AuthService.is_authorized(user_id):
        await message.answer(
            "👋 Добро пожаловать!\n\nВыберите действие:",
            reply_markup=get_main_menu_keyboard(user_id),
        )
    elif AuthService.is_pending(user_id):
        await message.answer(
            "⏳ <b>Регистрация на рассмотрении</b>\n\n"
            "Ваша заявка ожидает подтверждения администратора.\n"
            "После одобрения вы получите уведомление.",
            parse_mode=ParseMode.HTML,
        )
    else:
        await state.set_state(RegistrationForm.waiting_for_full_name)
        await message.answer(
            "🔐 Регистрация в системе\n\n"
            "Шаг 1/2: Введите ваше ФИО\n\n"
            "Например: Иванов Иван Иванович",
            reply_markup=get_cancel_keyboard(),
        )


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = (
        "📚 <b>Доступные команды:</b>\n\n"
        "/start - Главное меню / Начать регистрацию\n"
        "/help - Справка\n"
        "/cancel - Отменить текущую операцию\n\n"
        "<b>Для администратора:</b>\n"
        "/admin - Меню администратора"
    )
    await message.answer(help_text)


@dp.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущей операции"""
    current_state = await state.get_state()

    if not current_state:
        await message.answer("❌ Нет активной операции для отмены")
        return

    # Если это админская операция
    if current_state in (
        AdminState.changing_code,
        AdminState.searching_users,
        AdminState.editing_user_full_name,
        AdminState.editing_user_email,
        AdminState.setting_user_access_date,
        AdminState.editing_user_company,
    ):
        if AuthService.is_admin(message.from_user.id):
            await state.clear()
            await message.answer(
                "🔧 <b>Меню администратора:</b>\n\nДоступные действия:",
                parse_mode=ParseMode.HTML,
                reply_markup=get_admin_menu_keyboard(),
            )
        else:
            await message.answer("❌ У вас нет прав администратора")
            await state.clear()
    # Если это редактирование профиля
    elif current_state in (
        ProfileState.editing_full_name,
        ProfileState.editing_email,
    ):
        await state.clear()
        await message.answer("❌ Редактирование отменено.")
    # Если это регистрация
    elif current_state in (
        RegistrationForm.waiting_for_email,
        RegistrationForm.waiting_for_full_name,
        RegistrationForm.waiting_for_company,
    ):
        await state.clear()
        await message.answer(
            "❌ Регистрация отменена.\n\nДля начала регистрации нажмите /start"
        )
    # Другие состояния
    else:
        await state.clear()
        await message.answer("❌ Операция отменена")


# ==================== Admin Commands ====================


@dp.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    """Меню администратора (только для тестов, используйте кнопку в главном меню)"""
    # Проверяем админские права через AuthService
    if not AuthService.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    admin_text = (
        "🔧 <b>Меню администратора:</b>\n\n"
        "Используйте кнопку 'Админ-панель' в главном меню"
    )
    await message.answer(admin_text)


@dp.message(Command("users"))
async def cmd_users(message: Message):
    """Список пользователей"""
    if not AuthService.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    from database import UserRepository
    from database import SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    users = user_repo.get_all_users()
    db.close()

    msg = NotificationService.format_admin_user_list(users)
    await message.answer(msg)


@dp.message(Command("setcode"))
async def cmd_setcode(message: Message):
    """Установить код безопасности"""
    if not AuthService.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "❌ Неверный формат команды\n\nИспользуйте: /setcode [новый код]"
        )
        return

    # Обновляем код (это упрощённая версия, в реальном приложении нужно обновлять в БД)
    # Сейчас мы просто сообщаем об изменении
    new_code = args[1].strip()
    await message.answer(
        f"⚠️ Код безопасности изменён на: {new_code}\n\n"
        f"❗️ Для постоянного изменения обновите файл .env"
    )


@dp.message(Command("load_tests"))
async def cmd_load_tests(message: Message):
    """Загрузить тесты из папки"""
    if not AuthService.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    await message.answer(
        "📝 <b>Система тестирования</b>\n\n"
        "⚠️ В разработке\n\n"
        "Функционал тестирования находится в стадии разработки.",
        parse_mode=ParseMode.HTML,
    )


# ==================== Registration Handlers ====================


@dp.message(StateFilter(RegistrationForm.waiting_for_full_name))
async def process_full_name(message: Message, state: FSMContext):
    """Обработчик ввода ФИО"""
    full_name = message.text.strip()

    if not full_name:
        await message.answer("❌ ФИО не может быть пустым. Попробуйте ещё раз.")
        return

    words = full_name.split()
    if len(words) != 3:
        await message.answer(
            "❌ ФИО должно состоять из 3 слов: Фамилия Имя Отчество\n\n"
            'Попробуйте ещё раз или нажмите "Отмена"'
        )
        return

    # Сохраняем ФИО в состоянии FSM
    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationForm.waiting_for_email)
    await message.answer(
        f"✅ ФИО принято: {full_name}\n\nШаг 2/2: Введите ваш корпоративный email",
        reply_markup=get_cancel_keyboard(),
    )


@dp.message(StateFilter(RegistrationForm.waiting_for_email))
async def process_email(message: Message, state: FSMContext):
    """Обработчик ввода email"""
    email = message.text.strip()

    success, msg = AuthService.validate_email(email)

    if success:
        await state.update_data(email=email)
        await state.set_state(RegistrationForm.waiting_for_company)
        await message.answer(
            "✅ Email принят\n\n🏢 Шаг 3/3: Выберите вашу компанию:",
            reply_markup=get_company_selection_keyboard(),
        )
    else:
        await message.answer(f'❌ {msg}\n\nПопробуйте ещё раз или нажмите "Отмена"')


@dp.callback_query(lambda c: c.data.startswith("reg_company_"))
async def callback_reg_company(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора компании при регистрации"""
    company_key = callback.data.split("reg_company_")[1]

    data = await state.get_data()
    full_name = data.get("full_name")
    email = data.get("email")

    if not full_name or not email:
        await state.clear()
        await callback.message.edit_text(
            "❌ Ошибка регистрации. Начните заново: /start"
        )
        await callback.answer()
        return

    reg_success, reg_msg = AuthService.register_user(
        telegram_id=callback.from_user.id,
        email=email,
        full_name=full_name,
        username=callback.from_user.username,
        company=company_key,
    )

    if reg_success:
        await state.clear()
        company_display = "Компания 1" if company_key == "company1" else "Компания 2"
        await callback.message.edit_text(
            "✅ Заявка отправлена!\n\n"
            "⏳ Ожидайте подтверждения от администратора.\n"
            "После одобрения вы получите уведомление."
        )
        await callback.answer()

        from database import UserRepository, SessionLocal

        db = SessionLocal()
        user_repo = UserRepository(db)
        user = user_repo.get_by_telegram_id(callback.from_user.id)
        admin_ids = user_repo.get_admin_ids()
        db.close()

        if user:
            from bot.bot import bot

            for admin_id in admin_ids:
                try:
                    await bot.send_message(
                        admin_id,
                        f"🔔 <b>Новая заявка на регистрацию</b>\n\n"
                        f"📋 ФИО: {user.full_name or 'Не указано'}\n"
                        f"📧 Email: {user.email}\n"
                        f"🏢 Компания: {company_display}",
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_admin_approval_keyboard(user.id),
                    )
                except Exception:
                    pass
    else:
        await callback.message.edit_text(f"❌ {reg_msg}")
        await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("admin_approve_"))
async def callback_admin_approve(callback: CallbackQuery):
    """Подтверждение регистрации пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    if not user.is_pending:
        db.close()
        await callback.answer("⚠️ Пользователь уже подтверждён", show_alert=True)
        return

    user_repo.approve_user(user)
    db.close()

    try:
        from bot.bot import bot

        await bot.send_message(
            user.telegram_id,
            "✅ <b>Регистрация подтверждена!</b>\n\n"
            "Теперь вам доступны все функции системы.\n"
            "Нажмите /start для начала работы.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    await callback.message.edit_text(
        f"✅ <b>Регистрация подтверждена</b>\n\n"
        f"📋 {user.full_name or 'Не указано'}\n"
        f"📧 {user.email}",
        parse_mode=ParseMode.HTML,
    )
    await callback.answer("✅ Пользователь подтверждён")


@dp.callback_query(lambda c: c.data.startswith("admin_reject_"))
async def callback_admin_reject(callback: CallbackQuery):
    """Отклонение регистрации пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    user_display = f"{user.full_name or 'Не указано'} ({user.email})"
    telegram_id = user.telegram_id
    user_repo.reject_user(user)
    db.close()

    try:
        from bot.bot import bot

        await bot.send_message(
            telegram_id,
            "❌ <b>Регистрация отклонена</b>\n\n"
            "Ваша заявка на регистрацию была отклонена администратором.\n"
            "Для повторной попытки нажмите /start.",
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    await callback.message.edit_text(
        f"❌ <b>Регистрация отклонена</b>\n\n🗑️ {user_display}",
        parse_mode=ParseMode.HTML,
    )
    await callback.answer("❌ Регистрация отклонена")


@dp.callback_query(lambda c: c.data == "cancel_operation")
async def callback_cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены операции (для админских действий)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Меню администратора:</b>\n\nДоступные действия:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()


# ==================== Helper Functions ====================


async def go_back_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Функция для возврата в главное меню"""
    # Сбрасываем состояние файлового браузера, если оно активно
    current_state = await state.get_state()
    if current_state == FileBrowserState.browsing:
        await state.clear()

    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=get_main_menu_keyboard(callback.from_user.id),
    )


# ==================== Callback Handlers ====================


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await go_back_to_main_menu(callback, state)


@dp.callback_query(lambda c: c.data.startswith("menu_"))
async def callback_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик главного меню"""
    try:
        # Убираем префикс "menu_" чтобы получить action
        action = callback.data[5:]  # Убираем первые 5 символов "menu_"
        logger.info(
            f"Menu action received: {action}, User: {callback.from_user.id}, Full data: {callback.data}"
        )

        # Проверяем админские права для кнопки админ-панели
        if action == "admin_panel":
            logger.info(f"Admin panel button pressed by user {callback.from_user.id}")
            is_admin = AuthService.is_admin(callback.from_user.id)
            logger.info(f"User {callback.from_user.id} is admin: {is_admin}")

            if not is_admin:
                logger.warning(
                    f"Unauthorized admin panel access attempt by user {callback.from_user.id}"
                )
                await callback.answer(
                    "❌ У вас нет прав администратора", show_alert=True
                )
                return

            logger.info(f"Showing admin panel to user {callback.from_user.id}")
            admin_text = "🔧 <b>Админ-панель:</b>\n\nДоступные действия:"
            await callback.message.edit_text(
                admin_text,
                parse_mode=ParseMode.HTML,
                reply_markup=get_admin_menu_keyboard(),
            )
            logger.info(
                f"Admin panel shown successfully to user {callback.from_user.id}"
            )
            await callback.answer()
        elif action == "documents":
            # Используем динамический файловый браузер
            user = AuthService.get_user(callback.from_user.id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            # Определяем корневую папку по компании
            base_docs_path = str(settings.documents_path)
            if user.is_admin and not user.company:
                # Админ без компании — видит всё
                docs_path = base_docs_path
            elif user.company and user.company in settings.COMPANY_ROOTS:
                company_folder = settings.COMPANY_ROOTS[user.company]
                docs_path = str(Path(base_docs_path) / company_folder)
            else:
                await callback.answer(
                    "❌ Компания не назначена. Обратитесь к администратору.",
                    show_alert=True,
                )
                return

            # Проверяем что папка существует
            docs_folder = Path(docs_path)
            if not docs_folder.exists():
                docs_folder.mkdir(parents=True, exist_ok=True)

            await state.set_state(FileBrowserState.browsing)

            # Сохраняем начальные данные в FSM
            import hashlib

            folders = []
            files = []

            for item in sorted(
                docs_folder.iterdir(), key=lambda x: (not x.is_dir(), x.name)
            ):
                if item.is_dir():
                    name_hash = hashlib.md5(item.name.encode("utf-8")).hexdigest()[:8]
                    folders.append((name_hash, item.name, str(item)))
                elif item.is_file():
                    name_hash = hashlib.md5(item.name.encode("utf-8")).hexdigest()[:8]
                    files.append((name_hash, item.name, str(item)))

            await state.update_data(
                current_path=docs_path,
                relative_path="",  # Пустой путь = корень documents
                folders=folders,
                files=files,
                root_path=docs_path,  # Корень ограничен папкой компании
            )

            await callback.message.edit_text(
                "📚 Документы:\n\nВыберите папку:",
                reply_markup=get_folder_keyboard(docs_path),
            )
            logger.info(f"Documents browser opened by user {callback.from_user.id}")
            await callback.answer()
        elif action == "tests":
            logger.info(f"Tests button pressed by user {callback.from_user.id}")
            await callback.message.edit_text(
                "📝 <b>Система тестирования</b>\n\n"
                "⚠️ В разработке\n\n"
                "Функционал тестирования находится в стадии разработки.",
                parse_mode=ParseMode.HTML,
            )
            logger.info(
                f"Tests development message shown to user {callback.from_user.id}"
            )
            await callback.answer()
        elif action == "profile":
            user = AuthService.get_user(callback.from_user.id)
            if not user:
                await callback.answer("❌ Пользователь не найден", show_alert=True)
                return

            msg = (
                f"👤 <b>Ваши данные</b>\n\n"
                f"📋 ФИО: {user.full_name or 'Не указано'}\n"
                f"📧 Email: {user.email}\n"
            )
            await callback.message.edit_text(
                msg,
                parse_mode=ParseMode.HTML,
                reply_markup=get_profile_keyboard(),
            )
            await callback.answer()
        else:
            logger.warning(f"Unknown menu action: {action}")
            await callback.answer("❌ Неизвестное действие")

    except Exception as e:
        logger.error(f"Error in callback_menu: {e}", exc_info=True)
        try:
            await callback.answer("❌ Произошла ошибка", show_alert=True)
        except Exception as callback_error:
            logger.error(f"Error answering callback: {callback_error}")


@dp.callback_query(lambda c: c.data.startswith("category_"))
async def callback_category(callback: CallbackQuery):
    """Обработчик категории документов"""
    category = callback.data.split("_")[1]

    await callback.message.edit_text(
        f"📂 {category.upper()}\n\nВыберите подкатегорию:",
        reply_markup=get_subcategories_keyboard(category),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("subcategory_"))
async def callback_subcategory(callback: CallbackQuery):
    """Обработчик подкатегории документов"""
    parts = callback.data.split("_")
    category = parts[1]
    subcategory = "_".join(parts[2:])

    documents = DocumentService.get_documents_by_subcategory(category, subcategory)

    if not documents:
        await callback.answer("❌ Документы не найдены", show_alert=True)
        return

    await callback.message.edit_text(
        f"📂 {category.upper()} / {subcategory}\n\nВыберите документ:",
        reply_markup=get_documents_keyboard(documents),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("document_"))
async def callback_document(callback: CallbackQuery):
    """Обработчик выбора документа"""
    doc_id = int(callback.data.split("_")[1])
    document = DocumentService.get_document_by_id(doc_id)

    if not document:
        await callback.answer("❌ Документ не найден", show_alert=True)
        return

    from pathlib import Path

    file_path = Path(document.file_path)
    if not file_path.exists():
        await callback.answer("❌ Файл не найден", show_alert=True)
        return

    try:
        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=file_path,
            caption=f"📄 {document.name}",
        )
        await callback.answer("✅ Документ отправлен")
    except Exception as e:
        await callback.answer(f"❌ Ошибка отправки: {str(e)}", show_alert=True)


@dp.callback_query(lambda c: c.data.startswith("test_group_"))
async def callback_test_group(callback: CallbackQuery):
    """Обработчик выбора группы теста"""
    await callback.answer("⚠️ В разработке", show_alert=True)
    await callback.message.edit_text(
        "📝 <b>Система тестирования</b>\n\n"
        "⚠️ В разработке\n\n"
        "Функционал тестирования находится в стадии разработки.",
        parse_mode=ParseMode.HTML,
    )


@dp.callback_query(lambda c: c.data.startswith("answer_"))
async def callback_answer(callback: CallbackQuery):
    """Обработчик ответа на вопрос теста"""
    await callback.answer("⚠️ В разработке", show_alert=True)
    await callback.message.edit_text(
        "📝 <b>Система тестирования</b>\n\n"
        "⚠️ В разработке\n\n"
        "Функционал тестирования находится в стадии разработки.",
        parse_mode=ParseMode.HTML,
    )


# ==================== File Browser Handlers ====================


@dp.callback_query(lambda c: c.data.startswith("f_"))
async def callback_folder(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора папки (f_xxxxxxxx - хеш имени папки)"""
    name_hash = callback.data.split("f_")[1]

    data = await state.get_data()
    folders = data.get("folders", [])
    current_relative = data.get("relative_path", "")
    root_path = data.get("root_path", str(settings.documents_path))

    # Ищем папку по хешу
    target_folder = None
    for folder_hash, folder_name, folder_path in folders:
        if folder_hash == name_hash:
            target_folder = (folder_name, folder_path)
            break

    if not target_folder:
        await callback.answer("❌ Папка не найдена", show_alert=True)
        return

    folder_name, folder_path = target_folder
    folder = Path(folder_path)

    if not folder.exists() or not folder.is_dir():
        await callback.answer("❌ Папка не найдена", show_alert=True)
        return

    # Проверяем, что не выходим за пределы root_path
    root_path = data.get("root_path", "")
    if not str(folder_path).startswith(str(root_path)):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    # Формируем новый относительный путь
    if current_relative:
        new_relative = f"{current_relative}/{folder_name}"
    else:
        new_relative = folder_name

    # Получаем содержимое новой папки
    import hashlib

    new_folders = []
    new_files = []

    for item in sorted(folder.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
        if item.is_dir():
            name_hash = hashlib.md5(item.name.encode("utf-8")).hexdigest()[:8]
            new_folders.append((name_hash, item.name, str(item)))
        elif item.is_file():
            name_hash = hashlib.md5(item.name.encode("utf-8")).hexdigest()[:8]
            new_files.append((name_hash, item.name, str(item)))

    # Обновляем состояние
    await state.update_data(
        current_path=folder_path,
        relative_path=new_relative,
        folders=new_folders,
        files=new_files,
    )

    await callback.message.edit_text(
        f"📁 {folder_name}\n\nВыберите папку или файл:",
        reply_markup=get_folder_keyboard(folder_path, new_relative),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("fl_"))
async def callback_file(callback: CallbackQuery, state: FSMContext):
    """Обработчик выбора файла для отправки (fl_xxxxxxxx - хеш имени файла)"""
    name_hash = callback.data.split("fl_")[1]

    data = await state.get_data()
    files = data.get("files", [])

    # Ищем файл по хешу
    target_file = None
    for file_hash, file_name, file_path in files:
        if file_hash == name_hash:
            target_file = (file_name, file_path)
            break

    if not target_file:
        await callback.answer("❌ Файл не найден", show_alert=True)
        return

    file_name, file_path = target_file
    file_obj = Path(file_path)

    if not file_obj.exists() or not file_obj.is_file():
        await callback.answer("❌ Файл не найден", show_alert=True)
        return

    # Проверяем, что не выходим за пределы root_path
    data = await state.get_data()
    root_path = data.get("root_path", "")
    if not str(file_path).startswith(str(root_path)):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    try:
        # Сокращаем имя файла для caption (максимум 50 символов)
        max_name_length = 50
        display_name = (
            file_name
            if len(file_name) <= max_name_length
            else file_name[:max_name_length] + "..."
        )

        # Используем FSInputFile для локальных файлов (aiogram 3.x)
        document_file = FSInputFile(file_obj)

        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=document_file,
            caption=f"📄 {display_name}",
        )
        await callback.answer("✅ Файл отправлен")
    except Exception as e:
        await callback.answer(f"❌ Ошибка отправки: {str(e)}", show_alert=True)


@dp.callback_query(lambda c: c.data == "back_folder")
async def callback_back_folder(callback: CallbackQuery, state: FSMContext):
    """Обработчик кнопки Назад (возвращает в предыдущую папку)"""
    data = await state.get_data()
    current_path = data.get("current_path", "")
    relative_path = data.get("relative_path", "")
    root_path = Path(data.get("root_path", str(settings.documents_path)))

    # Проверяем, что мы не выше корневой папки
    current_obj = Path(current_path)
    if current_obj.parent == root_path:
        # Мы в подпапке корня - возвращаемся в главное меню
        await go_back_to_main_menu(callback, state)
        return

    # Если мы не в корне - возвращаемся на уровень выше
    if relative_path:
        parent_path = current_obj.parent
        parent_relative = (
            str(Path(relative_path).parent)
            if Path(relative_path).parent != Path(".")
            else ""
        )

        # Проверяем, что не вышли выше корня
        if parent_path == root_path:
            await go_back_to_main_menu(callback, state)
            return

        parent_name = parent_path.name

        import hashlib

        new_folders = []
        new_files = []

        for item in sorted(
            parent_path.iterdir(), key=lambda x: (not x.is_dir(), x.name)
        ):
            if item.is_dir():
                name_hash = hashlib.md5(item.name.encode("utf-8")).hexdigest()[:8]
                new_folders.append((name_hash, item.name, str(item)))
            elif item.is_file():
                name_hash = hashlib.md5(item.name.encode("utf-8")).hexdigest()[:8]
                new_files.append((name_hash, item.name, str(item)))

        await state.update_data(
            current_path=str(parent_path),
            relative_path=parent_relative,
            folders=new_folders,
            files=new_files,
        )

        await callback.message.edit_text(
            f"📁 {parent_name}\n\nВыберите папку или файл:",
            reply_markup=get_folder_keyboard(str(parent_path), parent_relative),
        )
    else:
        # В корне - возвращаемся в главное меню
        await go_back_to_main_menu(callback, state)

    await callback.answer()


# ==================== Profile Handlers ====================


@dp.callback_query(lambda c: c.data == "profile_edit_name")
async def callback_profile_edit_name(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования своего ФИО"""
    user = AuthService.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    await state.set_state(ProfileState.editing_full_name)
    await callback.message.edit_text(
        f"✏️ <b>Изменение ФИО</b>\n\n"
        f"Текущее ФИО: {user.full_name or 'Не указано'}\n\n"
        f"Введите новое ФИО (3 слова: Фамилия Имя Отчество):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_operation_keyboard(),
    )
    await callback.answer()


@dp.message(StateFilter(ProfileState.editing_full_name))
async def process_profile_edit_name(message: Message, state: FSMContext):
    """Обработчик ввода нового ФИО (пользователь)"""
    full_name = message.text.strip()

    if not full_name:
        await message.answer("❌ ФИО не может быть пустым. Попробуйте ещё раз.")
        return

    words = full_name.split()
    if len(words) != 3:
        await message.answer(
            "❌ ФИО должно состоять из 3 слов: Фамилия Имя Отчество\n\n"
            'Попробуйте ещё раз или нажмите "Отмена"'
        )
        return

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        db.close()
        await state.clear()
        await message.answer("❌ Пользователь не найден.")
        return

    user_repo.update_full_name(user, full_name)
    db.close()
    await state.clear()

    await message.answer(
        f"✅ ФИО обновлено: {full_name}",
        reply_markup=get_main_menu_keyboard(message.from_user.id),
    )


@dp.callback_query(lambda c: c.data == "profile_edit_email")
async def callback_profile_edit_email(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования своего email"""
    user = AuthService.get_user(callback.from_user.id)
    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    await state.set_state(ProfileState.editing_email)
    await callback.message.edit_text(
        f"📧 <b>Изменение email</b>\n\n"
        f"Текущий email: {user.email}\n\n"
        f"Введите новый email:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_operation_keyboard(),
    )
    await callback.answer()


@dp.message(StateFilter(ProfileState.editing_email))
async def process_profile_edit_email(message: Message, state: FSMContext):
    """Обработчик ввода нового email (пользователь)"""
    email = message.text.strip()

    # Проверяем валидность email (домен + уникальность)
    success, msg = AuthService.validate_email(email)
    if not success:
        await message.answer(f"❌ {msg}\n\nПопробуйте ещё раз.")
        return

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        db.close()
        await state.clear()
        await message.answer("❌ Пользователь не найден.")
        return

    user_repo.update_email(user, email)
    db.close()
    await state.clear()

    await message.answer(
        f"✅ Email обновлён: {email}",
        reply_markup=get_main_menu_keyboard(message.from_user.id),
    )


# ==================== Admin Callback Handlers ====================


@dp.callback_query(lambda c: c.data == "admin_search_users")
async def callback_admin_search_users(callback: CallbackQuery, state: FSMContext):
    """Поиск пользователей — запрос поискового запроса"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await state.set_state(AdminState.searching_users)
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователей</b>\n\nВведите имя или email для поиска:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_operation_keyboard(),
    )
    await callback.answer()


@dp.message(StateFilter(AdminState.searching_users))
async def process_admin_search_users(message: Message, state: FSMContext):
    """Обработчик поискового запроса пользователей"""
    if not AuthService.is_admin(message.from_user.id):
        await state.clear()
        await message.answer("❌ У вас нет прав администратора")
        return

    query = message.text.strip()

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    users = user_repo.search_users(query)
    db.close()

    await state.clear()

    if not users:
        await message.answer(
            f"🔍 По запросу «{query}» ничего не найдено.\n\n",
            reply_markup=get_admin_menu_keyboard(),
        )
        return

    msg = f"🔍 Найдено пользователей: {len(users)}\n\n"
    for user in users:
        from core.notification_service import get_user_status_text

        status = get_user_status_text(user)
        admin_badge = " 👨‍💼" if user.is_admin else ""
        msg += (
            f"👤 {user.full_name or 'Не указано'}{admin_badge}\n"
            f"📧 {user.email}\n"
            f"📌 {status}\n\n"
        )

    await message.answer(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=get_user_search_results_keyboard(users),
    )


@dp.callback_query(lambda c: c.data.startswith("admin_user_"))
async def callback_admin_user(callback: CallbackQuery):
    """Просмотр профиля пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    db.close()

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    from core.notification_service import get_user_status_text

    status = get_user_status_text(user)
    admin_badge = "\n👨‍💼 Администратор" if user.is_admin else ""
    msg = (
        f"👤 <b>Профиль пользователя</b>\n\n"
        f"📋 ФИО: {user.full_name or 'Не указано'}\n"
        f"📧 Email: {user.email}\n"
        f"🏢 Компания: {user.company or 'Не указана'}\n"
        f"📱 Telegram: @{user.username or 'Нет username'}\n"
        f"📅 Дата регистрации: {user.created_at.strftime('%d.%m.%Y')}\n"
        f"📌 {status}{admin_badge}"
    )

    await callback.message.edit_text(
        msg,
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_user_keyboard(user.id),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("admin_edit_name_"))
async def callback_admin_edit_name(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования ФИО пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_user_id=user_id)
    await state.set_state(AdminState.editing_user_full_name)

    await callback.message.edit_text(
        "✏️ <b>Изменение ФИО</b>\n\nВведите новое ФИО (3 слова: Фамилия Имя Отчество):",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_operation_keyboard(),
    )
    await callback.answer()


@dp.message(StateFilter(AdminState.editing_user_full_name))
async def process_admin_edit_name(message: Message, state: FSMContext):
    """Обработчик ввода нового ФИО (админ)"""
    if not AuthService.is_admin(message.from_user.id):
        await state.clear()
        await message.answer("❌ У вас нет прав администратора")
        return

    full_name = message.text.strip()

    if not full_name:
        await message.answer("❌ ФИО не может быть пустым. Попробуйте ещё раз.")
        return

    words = full_name.split()
    if len(words) != 3:
        await message.answer(
            "❌ ФИО должно состоять из 3 слов: Фамилия Имя Отчество\n\n"
            'Попробуйте ещё раз или нажмите "Отмена"'
        )
        return

    data = await state.get_data()
    user_id = data.get("edit_user_id")
    await state.clear()

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await message.answer("❌ Пользователь не найден.")
        return

    user_repo.update_full_name(user, full_name)
    db.close()

    await message.answer(
        f"✅ ФИО обновлено: {full_name}",
        reply_markup=get_admin_menu_keyboard(),
    )


@dp.callback_query(lambda c: c.data.startswith("admin_edit_email_"))
async def callback_admin_edit_email(callback: CallbackQuery, state: FSMContext):
    """Начало редактирования email пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_user_id=user_id)
    await state.set_state(AdminState.editing_user_email)

    await callback.message.edit_text(
        "📧 <b>Изменение email</b>\n\nВведите новый email:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_operation_keyboard(),
    )
    await callback.answer()


@dp.message(StateFilter(AdminState.editing_user_email))
async def process_admin_edit_email(message: Message, state: FSMContext):
    """Обработчик ввода нового email (админ)"""
    if not AuthService.is_admin(message.from_user.id):
        await state.clear()
        await message.answer("❌ У вас нет прав администратора")
        return

    email = message.text.strip()

    # Проверяем валидность email
    success, msg = AuthService.validate_email(email)
    if not success:
        await message.answer(f"❌ {msg}\n\nПопробуйте ещё раз.")
        return

    data = await state.get_data()
    user_id = data.get("edit_user_id")
    await state.clear()

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await message.answer("❌ Пользователь не найден.")
        return

    user_repo.update_email(user, email)
    db.close()

    await message.answer(
        f"✅ Email обновлён: {email}",
        reply_markup=get_admin_menu_keyboard(),
    )


@dp.callback_query(lambda c: c.data.startswith("admin_delete_user_"))
async def callback_admin_delete_user(callback: CallbackQuery):
    """Подтверждение удаления пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)
    db.close()

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ <b>Удаление пользователя</b>\n\n"
        f"Вы уверены, что хотите удалить пользователя?\n"
        f"📋 <b>{user.full_name or 'Не указано'}</b>\n"
        f"📧 {user.email}\n\n"
        f"Будут удалены все результаты тестов этого пользователя.\n"
        f"Действие необратимо.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_delete_confirm_keyboard(user.id),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("admin_confirm_delete_"))
async def callback_admin_confirm_delete(callback: CallbackQuery):
    """Подтверждённое удаление пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    user_display = f"{user.full_name or 'Не указано'} ({user.email})"
    user_repo.delete_user(user)
    db.close()

    await callback.message.edit_text(
        f"✅ <b>Пользователь удалён</b>\n\n"
        f"🗑️ {user_display}\n\n"
        f"Все связанные данные (результаты тестов) также удалены.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("admin_set_access_date_"))
async def callback_admin_set_access_date(callback: CallbackQuery, state: FSMContext):
    """Начало установки даты выдачи документа (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])
    await state.update_data(edit_user_id=user_id)
    await state.set_state(AdminState.setting_user_access_date)

    await callback.message.edit_text(
        "📅 <b>Установка даты выдачи документа</b>\n\n"
        "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
        "или нажмите кнопку «Сегодня»:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_access_date_keyboard(user_id),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("admin_set_today_"))
async def callback_admin_set_today(callback: CallbackQuery, state: FSMContext):
    """Установка сегодняшней даты выдачи документа (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    from datetime import datetime, timedelta

    now = datetime.now()
    expiry = now + timedelta(days=358)
    user_repo.set_access_date(user, now)
    db.close()
    await state.clear()

    await callback.message.edit_text(
        f"✅ <b>Дата выдачи документа установлена</b>\n\n"
        f"📋 {user.full_name or 'Не указано'}\n"
        f"📅 Дата: {now.strftime('%d.%m.%Y')}\n"
        f"⏰ Допуск действителен 358 дней (до {expiry.strftime('%d.%m.%Y')})",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer("✅ Дата установлена")


@dp.message(StateFilter(AdminState.setting_user_access_date))
async def process_admin_access_date(message: Message, state: FSMContext):
    """Обработчик ввода даты выдачи документа (админ)"""
    if not AuthService.is_admin(message.from_user.id):
        await state.clear()
        await message.answer("❌ У вас нет прав администратора")
        return

    date_str = message.text.strip()

    from datetime import datetime

    try:
        date = datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        await message.answer(
            "❌ Неверный формат даты.\n\n"
            "Введите дату в формате <b>ДД.ММ.ГГГГ</b>\n"
            "Например: 15.03.2026",
            parse_mode=ParseMode.HTML,
        )
        return

    data = await state.get_data()
    user_id = data.get("edit_user_id")
    await state.clear()

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await message.answer("❌ Пользователь не найден.")
        return

    user_repo.set_access_date(user, date)
    db.close()

    from datetime import timedelta

    expiry = date + timedelta(days=358)
    await message.answer(
        f"✅ <b>Дата выдачи документа установлена</b>\n\n"
        f"📋 {user.full_name or 'Не указано'}\n"
        f"📅 Дата: {date.strftime('%d.%m.%Y')}\n"
        f"⏰ Допуск действителен 358 дней (до {expiry.strftime('%d.%m.%Y')})",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )


@dp.callback_query(lambda c: c.data.startswith("admin_edit_company_"))
async def callback_admin_edit_company(callback: CallbackQuery, state: FSMContext):
    """Начало изменения компании пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from bot.keyboards.inline import get_admin_company_keyboard

    await callback.message.edit_text(
        "🏢 <b>Выбор компании</b>\n\nВыберите компанию для пользователя:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_company_keyboard(user_id),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("admin_set_company_"))
async def callback_admin_set_company(callback: CallbackQuery):
    """Установка компании пользователя (админ)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    # Parse: admin_set_company_{company_key}_{user_id}
    parts = callback.data.split("_")
    # parts: ["admin", "set", "company", company_key, user_id] or ["admin", "set", "company", "none", user_id]
    company_key = parts[3]
    user_id = int(parts[4])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    if company_key == "none":
        user.company = None
    else:
        user.company = company_key
    db.commit()
    db.refresh(user)

    company_display = {
        "company1": "Компания 1",
        "company2": "Компания 2",
        None: "Не указана",
    }.get(user.company, user.company or "Не указана")

    db.close()

    await callback.message.edit_text(
        f"✅ <b>Компания изменена</b>\n\n"
        f"👤 {user.full_name or 'Не указано'}\n"
        f"🏢 Компания: {company_display}",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_user_keyboard(user.id),
    )
    await callback.answer("✅ Компания обновлена")


@dp.callback_query(lambda c: c.data == "admin_manage_admins")
async def callback_admin_manage_admins(callback: CallbackQuery):
    """Управление администраторами"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    users = user_repo.get_all_users()
    db.close()

    if not users:
        await callback.answer(
            "❌ Нет зарегистрированных пользователей", show_alert=True
        )
        return

    await callback.message.edit_text(
        "👨‍💼 <b>Управление администраторами</b>\n\n"
        "Нажмите на пользователя для назначения/снятия админских прав:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_manage_admins_keyboard(users),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("add_admin_"))
async def callback_add_admin(callback: CallbackQuery):
    """Назначить администратора"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    user_repo.set_admin(user, is_admin=True)
    users = user_repo.get_all_users()
    db.close()

    await callback.message.edit_text(
        f"✅ <b>Пользователь назначен администратором!</b>\n\n"
        f"👤 {user.full_name or user.email}",
        parse_mode=ParseMode.HTML,
        reply_markup=get_manage_admins_keyboard(users),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("remove_admin_"))
async def callback_remove_admin(callback: CallbackQuery):
    """Снять права администратора"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    user_id = int(callback.data.split("_")[-1])

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    user = user_repo.get_by_id(user_id)

    if not user:
        db.close()
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    # Проверяем, что не пытаемся снять права с самого себя
    if user.telegram_id == callback.from_user.id:
        db.close()
        await callback.answer(
            "❌ Нельзя снять права администратора у самого себя", show_alert=True
        )
        return

    user_repo.set_admin(user, is_admin=False)
    users = user_repo.get_all_users()
    db.close()

    await callback.message.edit_text(
        f"❌ <b>Права администратора сняты!</b>\n\n👤 {user.full_name or user.email}",
        parse_mode=ParseMode.HTML,
        reply_markup=get_manage_admins_keyboard(users),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_admin_menu")
async def callback_back_to_admin_menu(callback: CallbackQuery):
    """Возврат в админское меню"""
    await callback.message.edit_text(
        "🔧 <b>Меню администратора:</b>\n\nДоступные действия:",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "admin_change_code")
async def callback_admin_change_code(callback: CallbackQuery, state: FSMContext):
    """Начало смены секретного кода"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await state.set_state(AdminState.changing_code)
    await callback.message.edit_text(
        "🔑 <b>Смена секретного кода</b>\n\n"
        "Введите новый секретный код для регистрации пользователей.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_cancel_operation_keyboard(),
    )
    await callback.answer()


@dp.message(StateFilter(AdminState.changing_code))
async def process_new_code(message: Message, state: FSMContext):
    """Обработчик ввода нового секретного кода"""
    if not AuthService.is_admin(message.from_user.id):
        await state.clear()
        await message.answer("❌ У вас нет прав администратора")
        return

    new_code = message.text.strip()

    # Проверяем, что код не пустой
    if not new_code:
        await message.answer("❌ Код не может быть пустым. Попробуйте ещё раз.")
        return

    # Проверяем, что код не содержит пробелов
    if " " in new_code:
        await message.answer("❌ Код не должен содержать пробелов. Попробуйте ещё раз.")
        return

    # Сохраняем код в БД
    from core import SettingsService

    SettingsService.set_security_code(new_code)

    await state.clear()
    await message.answer(
        f"✅ <b>Секретный код изменён!</b>\n\n"
        f"🔑 Новый код: <code>{new_code}</code>\n\n"
        f"📋 Код сохранен в базе данных и теперь используется для регистрации.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )


@dp.callback_query(lambda c: c.data == "admin_load_tests")
async def callback_admin_load_tests(callback: CallbackQuery):
    """Сканировать тесты из папки"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await callback.message.edit_text(
        "📝 <b>Система тестирования</b>\n\n"
        "⚠️ В разработке\n\n"
        "Функционал тестирования находится в стадии разработки.",
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer()


# ==================== Entry Point ====================


async def main():
    """Запуск бота"""
    try:
        # Инициализируем базу данных
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized successfully")

        # Инициализируем настройки из .env при первом запуске
        logger.info("Initializing settings from environment...")
        from core import SettingsService

        SettingsService.initialize_from_env()
        logger.info("Settings initialized successfully")

        # Запуск планировщика уведомлений
        from bot.scheduler import run_scheduler

        asyncio.create_task(run_scheduler(bot))
        logger.info("Scheduler started")

        # Удаляем webhook и запускаем long polling
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Bot started!")

        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Fatal error in bot: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
