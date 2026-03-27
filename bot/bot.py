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
    get_cancel_operation_keyboard,
    get_manage_admins_keyboard,
)
from bot.states import RegistrationForm, FileBrowserState, AdminState
from database import init_db

# Инициализация бота
bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())


# ==================== Command Handlers ====================

@dp.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработчик команды /start"""
    user_id = message.from_user.id

    # Сбрасываем текущее состояние, если есть
    await state.clear()

    if AuthService.is_authorized(user_id):
        await message.answer(
            "👋 Добро пожаловать!\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        # Начинаем пошаговую регистрацию
        await state.set_state(RegistrationForm.waiting_for_email)
        await message.answer(
            "🔐 Регистрация в системе\n\n"
            "Шаг 1/2: Введите ваш корпоративный email\n\n"
            "Пример: ivanov@intellektika.ru",
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
    if current_state == AdminState.changing_code:
        if AuthService.is_admin(message.from_user.id):
            await state.clear()
            await message.answer(
                "🔧 <b>Меню администратора:</b>\n\n"
                "Доступные действия:",
                parse_mode=ParseMode.HTML,
                reply_markup=get_admin_menu_keyboard(),
            )
        else:
            await message.answer("❌ У вас нет прав администратора")
            await state.clear()
    # Если это регистрация
    elif current_state == RegistrationForm.waiting_for_email or current_state == RegistrationForm.waiting_for_code:
        await state.clear()
        await message.answer(
            "❌ Регистрация отменена.\n\n"
            "Для начала регистрации нажмите /start"
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
            "❌ Неверный формат команды\n\n"
            "Используйте: /setcode [новый код]"
        )
        return

    # Обновляем код (это упрощённая версия, в реальном приложении нужно обновлять в БД)
    # Сейчас мы просто сообщаем об изменении
    new_code = args[1].strip()
    await message.answer(f"⚠️ Код безопасности изменён на: {new_code}\n\n"
                       f"❗️ Для постоянного изменения обновите файл .env")


@dp.message(Command("load_docs"))
async def cmd_load_docs(message: Message):
    """Загрузить документы из папки"""
    if not AuthService.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    count = DocumentService.scan_documents_folder()
    await message.answer(f"📚 Добавлено документов: {count}")


@dp.message(Command("load_tests"))
async def cmd_load_tests(message: Message):
    """Загрузить тесты из папки"""
    if not AuthService.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return

    from config import settings
    count = TestService.load_tests_from_json(f"{settings.documents_path}/../tests")
    await message.answer(f"📝 Добавлено тестов: {count}")


# ==================== Registration Handlers ====================

@dp.message(StateFilter(RegistrationForm.waiting_for_email))
async def process_email(message: Message, state: FSMContext):
    """Обработчик ввода email"""
    email = message.text.strip()

    # Проверяем валидность email (без создания пользователя)
    success, msg = AuthService.validate_email(email)

    if success:
        # Сохраняем email в состоянии FSM
        await state.update_data(email=email)
        await state.set_state(RegistrationForm.waiting_for_code)
        await message.answer(
            "✅ Email принят!\n\n"
            "Шаг 2/2: Введите код безопасности\n\n"
            "Код вы должны получить от администратора",
            reply_markup=get_cancel_keyboard(),
        )
    else:
        await message.answer(f"❌ {msg}\n\nПопробуйте ещё раз или нажмите \"Отмена\"")


@dp.message(StateFilter(RegistrationForm.waiting_for_code))
async def process_code(message: Message, state: FSMContext):
    """Обработчик ввода кода безопасности"""
    code = message.text.strip()

    # Получаем email из состояния FSM
    data = await state.get_data()
    email = data.get("email")

    if not email:
        await state.clear()
        await message.answer(
            "❌ Ошибка: email не найден. Начните регистрацию заново командой /start"
        )
        return

    # Создаём и верифицируем пользователя одним действием
    success, msg = AuthService.register_and_verify(
        telegram_id=message.from_user.id,
        email=email,
        code=code,
        full_name=message.from_user.full_name,
        username=message.from_user.username,
    )

    if success:
        await state.clear()
        await message.answer(
            f"✅ {msg}\n\n"
            "👋 Добро пожаловать!\n\n"
            "Выберите действие:",
            reply_markup=get_main_menu_keyboard(),
        )
    else:
        await message.answer(f"❌ {msg}\n\nПопробуйте ещё раз или нажмите \"Отмена\"")


@dp.callback_query(lambda c: c.data == "cancel_registration")
async def callback_cancel_registration(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены регистрации"""
    await state.clear()
    await callback.message.edit_text(
        "❌ Регистрация отменена.\n\n"
        "Для начала регистрации нажмите /start"
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "cancel_operation")
async def callback_cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Обработчик отмены операции (для админских действий)"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    await state.clear()
    await callback.message.edit_text(
        "🔧 <b>Меню администратора:</b>\n\n"
        "Доступные действия:",
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
        reply_markup=get_main_menu_keyboard(),
    )


# ==================== Callback Handlers ====================

@dp.callback_query(lambda c: c.data == "back_to_menu")
async def callback_back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню"""
    await go_back_to_main_menu(callback, state)


@dp.callback_query(lambda c: c.data.startswith("menu_"))
async def callback_menu(callback: CallbackQuery, state: FSMContext):
    """Обработчик главного меню"""
    action = callback.data.split("_")[1]

    # Проверяем админские права для кнопки админ-панели
    if action == "admin_panel":
        if not AuthService.is_admin(callback.from_user.id):
            await callback.answer("❌ У вас нет прав администратора", show_alert=True)
            return

        admin_text = (
            "🔧 <b>Админ-панель:</b>\n\n"
            "Доступные действия:"
        )
        await callback.message.edit_text(
            admin_text,
            parse_mode=ParseMode.HTML,
            reply_markup=get_admin_menu_keyboard(),
        )
        await callback.answer()
    elif action == "documents":
        # Используем динамический файловый браузер
        await state.set_state(FileBrowserState.browsing)
        docs_path = f"{settings.documents_path}"

        # Сохраняем начальные данные в FSM
        import hashlib
        docs_folder = Path(docs_path)

        folders = []
        files = []

        for item in sorted(docs_folder.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
            if item.is_dir():
                name_hash = hashlib.md5(item.name.encode('utf-8')).hexdigest()[:8]
                folders.append((name_hash, item.name, str(item)))
            elif item.is_file():
                name_hash = hashlib.md5(item.name.encode('utf-8')).hexdigest()[:8]
                files.append((name_hash, item.name, str(item)))

        await state.update_data(
            current_path=docs_path,
            relative_path="",  # Пустой путь = корень documents
            folders=folders,
            files=files,
            root_path=docs_path  # Сохраняем корневой путь для ограничения
        )

        await callback.message.edit_text(
            "📚 Документы:\n\nВыберите папку:",
            reply_markup=get_folder_keyboard(docs_path),
        )
    elif action == "tests":
        await callback.message.edit_text(
            "📝 Выберите группу теста:",
            reply_markup=get_test_groups_keyboard(),
        )

    await callback.answer()


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
    group = int(callback.data.split("_")[2])

    test = TestService.get_test_by_group(group)

    if not test:
        await callback.answer(f"❌ Тест для группы {group} не найден", show_alert=True)
        return

    # Сохраняем текущий тест и вопрос в состоянии (упрощённая версия)
    # В реальном приложении используйте FSM (Finite State Machine)
    questions = test.questions

    # Первый вопрос
    first_question = questions[0]
    await callback.message.edit_text(
        f"📝 <b>Тест: Группа {group}</b>\n\n"
        f"❓ Вопрос 1/{len(questions)}:\n"
        f"{first_question['question']}",
        reply_markup=get_test_answers_keyboard(1, first_question["options"]),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("answer_"))
async def callback_answer(callback: CallbackQuery):
    """Обработчик ответа на вопрос теста"""
    parts = callback.data.split("_")
    question_num = int(parts[1])
    answer_num = int(parts[2])

    # Это упрощённая версия - в реальном приложении нужно хранить состояние теста
    # и собирать ответы пользователя
    await callback.answer(f"✅ Выбран ответ {answer_num}")
    await callback.message.edit_text(
        f"✅ Ответ {answer_num} записан\n\n"
        f"❗️ Это упрощённая версия.\n"
        f"В полной версии здесь будет следующий вопрос.",
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
            name_hash = hashlib.md5(item.name.encode('utf-8')).hexdigest()[:8]
            new_folders.append((name_hash, item.name, str(item)))
        elif item.is_file():
            name_hash = hashlib.md5(item.name.encode('utf-8')).hexdigest()[:8]
            new_files.append((name_hash, item.name, str(item)))

    # Обновляем состояние
    await state.update_data(
        current_path=folder_path,
        relative_path=new_relative,
        folders=new_folders,
        files=new_files
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

    try:
        # Сокращаем имя файла для caption (максимум 50 символов)
        max_name_length = 50
        display_name = file_name if len(file_name) <= max_name_length else file_name[:max_name_length] + "..."

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
        parent_relative = str(Path(relative_path).parent) if Path(relative_path).parent != Path(".") else ""

        # Проверяем, что не вышли выше корня
        if parent_path == root_path:
            await go_back_to_main_menu(callback, state)
            return

        parent_name = parent_path.name

        import hashlib
        new_folders = []
        new_files = []

        for item in sorted(parent_path.iterdir(), key=lambda x: (not x.is_dir(), x.name)):
            if item.is_dir():
                name_hash = hashlib.md5(item.name.encode('utf-8')).hexdigest()[:8]
                new_folders.append((name_hash, item.name, str(item)))
            elif item.is_file():
                name_hash = hashlib.md5(item.name.encode('utf-8')).hexdigest()[:8]
                new_files.append((name_hash, item.name, str(item)))

        await state.update_data(
            current_path=str(parent_path),
            relative_path=parent_relative,
            folders=new_folders,
            files=new_files
        )

        await callback.message.edit_text(
            f"📁 {parent_name}\n\nВыберите папку или файл:",
            reply_markup=get_folder_keyboard(str(parent_path), parent_relative),
        )
    else:
        # В корне - возвращаемся в главное меню
        await go_back_to_main_menu(callback, state)

    await callback.answer()


# ==================== Admin Callback Handlers ====================

@dp.callback_query(lambda c: c.data == "admin_users")
async def callback_admin_users(callback: CallbackQuery):
    """Список пользователей"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    from database import UserRepository, SessionLocal

    db = SessionLocal()
    user_repo = UserRepository(db)
    users = user_repo.get_all_users()
    db.close()

    msg = NotificationService.format_admin_user_list(users)
    await callback.message.edit_text(msg, parse_mode=ParseMode.HTML)
    await callback.answer()


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
        await callback.answer("❌ Нет зарегистрированных пользователей", show_alert=True)
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
        await callback.answer("❌ Нельзя снять права администратора у самого себя", show_alert=True)
        return

    user_repo.set_admin(user, is_admin=False)
    users = user_repo.get_all_users()
    db.close()

    await callback.message.edit_text(
        f"❌ <b>Права администратора сняты!</b>\n\n"
        f"👤 {user.full_name or user.email}",
        parse_mode=ParseMode.HTML,
        reply_markup=get_manage_admins_keyboard(users),
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back_to_admin_menu")
async def callback_back_to_admin_menu(callback: CallbackQuery):
    """Возврат в админское меню"""
    await callback.message.edit_text(
        "🔧 <b>Меню администратора:</b>\n\n"
        "Доступные действия:",
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


@dp.callback_query(lambda c: c.data == "admin_load_docs")
async def callback_admin_load_docs(callback: CallbackQuery):
    """Сканировать документы из папки"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    count = DocumentService.scan_documents_folder()
    explanation = (
        "📚 <b>Сканирование документов завершено!</b>\n\n"
        "Добавлено документов в базу данных: {}\n\n"
        "<b>Что это делает:</b>\n"
        "• Сканирует папку data/documents\n"
        "• Находит все файлы и создаёт записи в БД\n"
        "• Позволяет пользователям скачивать документы через бота"
    ).format(count)

    await callback.message.edit_text(
        explanation,
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer(f"📚 Добавлено документов: {count}")


@dp.callback_query(lambda c: c.data == "admin_load_tests")
async def callback_admin_load_tests(callback: CallbackQuery):
    """Сканировать тесты из папки"""
    if not AuthService.is_admin(callback.from_user.id):
        await callback.answer("❌ У вас нет прав администратора", show_alert=True)
        return

    count = TestService.load_tests_from_json(f"{settings.documents_path}/../tests")
    explanation = (
        "📝 <b>Сканирование тестов завершено!</b>\n\n"
        "Добавлено тестов в базу данных: {}\n\n"
        "<b>Что это делает:</b>\n"
        "• Сканирует папку data/tests\n"
        "• Находит все JSON-файлы с тестами\n"
        "• Создаёт записи тестов в БД\n"
        "• Позволяет пользователям проходить тесты через бота"
    ).format(count)

    await callback.message.edit_text(
        explanation,
        parse_mode=ParseMode.HTML,
        reply_markup=get_admin_menu_keyboard(),
    )
    await callback.answer(f"📝 Добавлено тестов: {count}")


# ==================== Entry Point ====================

async def main():
    """Запуск бота"""
    # Инициализируем базу данных
    init_db()

    # Инициализируем настройки из .env при первом запуске
    from core import SettingsService
    SettingsService.initialize_from_env()

    # Удаляем webhook и запускаем long polling
    await bot.delete_webhook(drop_pending_updates=True)
    print("🤖 Бот запущен!")

    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
