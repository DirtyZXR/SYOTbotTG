# Система логирования SYOTbotTG

## Обзор
Проект использует стандартную библиотеку Python `logging` с ротацией файлов.

## Файл конфигурации
`utils/logger.py` - настройки логирования

## Уровни логирования
- **DEBUG**: Подробная информация для отладки
- **INFO**: Общая информация о работе бота
- **WARNING**: Предупреждения о потенциальных проблемах
- **ERROR**: Ошибки, которые не останавливают работу бота
- **CRITICAL**: Критические ошибки

## Использование

```python
from utils import logger

# Информационное сообщение
logger.info("Bot started successfully")

# Предупреждение
logger.warning("User attempted unauthorized access")

# Ошибка
logger.error(f"Failed to send message: {e}", exc_info=True)

# Отладка
logger.debug(f"Processing callback: {callback_data}")
```

## Локация логов
- **Консоль**: Вывод в stdout в реальном времени
- **Файл**: `logs/bot.log` с ротацией (максимум 5 файлов по 10MB)

## Формат логов
```
2026-03-27 17:00:28 - SYOTbot - INFO - Bot started!
```

## Настройка уровня логирования
Измените уровень в `utils/logger.py`:

```python
logger = setup_logger("SYOTbot", logging.DEBUG)  # Для отладки
logger = setup_logger("SYOTbot", logging.INFO)   # Обычный режим
```

## Примеры логирования в коде

### В обработчиках сообщений
```python
@dp.message(Command("start"))
async def cmd_start(message: Message):
    logger.info(f"User {message.from_user.id} pressed /start")
    # ... код обработчика
```

### При ошибках
```python
try:
    # Опасная операция
    await some_operation()
except Exception as e:
    logger.error(f"Error in some_operation: {e}", exc_info=True)
```

### Отслеживание действий пользователей
```python
logger.info(f"Admin panel opened by user {callback.from_user.id}")
logger.warning(f"Unauthorized access attempt by user {user_id}")
```

## Логирование ошибок с трассировкой
Для полного отслеживания ошибок используйте `exc_info=True`:

```python
logger.error("Database connection failed", exc_info=True)
```

Это выведет полный стек вызовов, что полезно для отладки.