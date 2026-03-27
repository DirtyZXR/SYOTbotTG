# Архитектура проекта SYOTbotTG

## Обзор системы

SYOTbotTG - это Telegram бот для работы с документами по охране труда и проведения тестов. Система состоит из следующих основных компонентов:

## Компоненты архитектуры

### 1. Telegram Bot Layer (`bot/`)
**Назначение:** Обработка команд и сообщений от пользователей

- `bot.py` - Основной файл бота с хендлерами команд и callback-ов
- `keyboards/` - Inline клавиатуры для навигации

**Основные функции:**
- Обработка команд (/start, /register, /verify, /help)
- Обработка callback-кнопок
- Управление состоянием пользователя

### 2. Core Logic (`core/`)
**Назначение:** Бизнес-логика приложения

#### `auth_service.py`
- Регистрация пользователей с проверкой корпоративного email
- Верификация по коду безопасности
- Проверка авторизации

#### `document_service.py`
- Поиск документов по категориям
- Сканирование папки с документами
- Управление документами

#### `test_service.py`
- Получение тестов по группам
- Проверка ответов
- Форматирование результатов с подсветкой
- Сохранение результатов

#### `notification_service.py`
- Форматирование уведомлений для администратора
- Отправка сообщений о результатах тестов

### 3. Data Models (`models/`)
**Назначение:** Определение структуры данных

- `user.py` - Пользователь системы
- `document.py` - Документ
- `test.py` - Тест
- `test_result.py` - Результат теста

### 4. Database Layer (`database/`)
**Назначение:** Работа с базой данных

- `session.py` - Настройка SQLAlchemy и сессии
- `user_repo.py` - Репозиторий пользователей
- `document_repo.py` - Репозиторий документов
- `test_repo.py` - Репозиторий тестов
- `test_result_repo.py` - Репозиторий результатов

### 5. Configuration (`config/`)
**Назначение:** Конфигурация приложения

- `settings.py` - Настройки бота (Pydantic Settings)
- `categories.py` - Категории документов

### 6. Utils (`utils/`)
**Назначение:** Вспомогательные функции

- `validators.py` - Валидаторы данных (email и т.д.)

## Потоки данных

### Flow 1: Регистрация и верификация
```
Пользователь
  → /register email
    → AuthService.register_user()
      → UserRepository.create_user()
        → [Database]
  → /verify code
    → AuthService.verify_user()
      → Проверка кода (settings.security_code)
        → UserRepository.verify_user()
          → [Database]
```

### Flow 2: Получение документов
```
Пользователь
  → /start (главное меню)
    → Кнопка "Документы"
      → get_categories_keyboard()
        → DocumentService.get_documents_by_category()
          → DocumentRepository.get_by_category()
            → [Database]
        → get_subcategories_keyboard()
        → get_documents_keyboard()
          → bot.send_document()
```

### Flow 3: Прохождение теста
```
Пользователь
  → Кнопка "Тесты"
    → get_test_groups_keyboard()
      → TestService.get_test_by_group()
        → TestRepository.get_by_group()
          → [Database]
    → Ответ на вопросы
      → TestService.check_answers()
        → TestService.format_results()
          → [Подсветка ✅/❌]
    → TestService.save_test_result()
      → TestResultRepository.create_result()
        → [Database]
    → Если ≥90% → NotificationService.format_admin_notification()
      → bot.send_message(admin_id)
```

## Безопасность

### Уровни защиты:

1. **Регистрация с корпоративным email**
   - Проверка домена email
   - Уникальность email

2. **Верификация по коду**
   - Код безопасности устанавливается администратором
   - Может быть изменён в любой момент
   - Хранится в `.env`

3. **Контроль доступа**
   - Проверка `is_verified` перед любым действием
   - Доступ к документам только после верификации

4. **Администраторские функции**
   - Проверка `admin_id` перед выполнением админ-команд
   - Просмотр всех зарегистрированных пользователей

## Технологический стек

| Компонент | Технология | Описание |
|-----------|------------|----------|
| Telegram Bot | aiogram 3.x | Async Telegram Bot API |
| ORM | SQLAlchemy 2.x | Async ORM для работы с БД |
| Database | SQLite | Встроенная БД |
| Validation | Pydantic 2.x | Валидация данных |
| Settings | pydantic-settings | Управление настройками |
| Environment | python-dotenv | Загрузка переменных окружения |

## Масштабирование

### Возможные улучшения:

1. **База данных**
   - Переход на PostgreSQL для высокой нагрузки
   - Добавление миграций (Alembic)

2. **Файловое хранилище**
   - S3 хранилище для документов
   - CDN для быстрой загрузки

3. **State Management**
   - Добавление FSM (Finite State Machine) для тестов
   - Хранение состояния в Redis

4. **Админ-панель**
   - Веб-интерфейс для администратора
   - Графики и статистика

5. **Тесты**
   - Unit-тесты для сервисов
   - Integration тесты для бота

## Обработка ошибок

### Текущая реализация:
- Basic try-except блоки
- Простые сообщения об ошибках

### Рекомендации:
- Логирование ошибок
- Более детальные сообщения
- Обработка сетевых ошибок
- Retry-механизмы

## Мониторинг и логирование

### Добавить:
- Structured logging (loguru / python-logging)
- Metrics (Prometheus)
- Alerting (Sentry для ошибок)

## Безопасность (дополнительно)

### Рекомендации:
- Rate limiting
- Input validation
- SQL injection protection (через SQLAlchemy)
- XSS protection (aiogram handles this)
- HTTPS для вебхуков (если используется)
