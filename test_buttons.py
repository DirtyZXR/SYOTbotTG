"""Тест для проверки кнопок бота"""
import sys
import io
sys.path.insert(0, '.')

# Устанавливаем UTF-8 кодировку для консоли Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from bot.keyboards import get_main_menu_keyboard, get_admin_menu_keyboard
from utils import logger

print("=== Тест кнопок ===")
print("\n1. Главное меню (обычный пользователь):")
main_menu = get_main_menu_keyboard()
print(f"Количество кнопок: {len(main_menu.inline_keyboard)}")
for i, row in enumerate(main_menu.inline_keyboard):
    for j, button in enumerate(row):
        print(f"  [{i}][{j}] {button.text} -> {button.callback_data}")

print("\n2. Главное меню (администратор):")
admin_id = 1028552698  # Правильный ID администратора
main_menu_admin = get_main_menu_keyboard(admin_id)
print(f"Количество кнопок: {len(main_menu_admin.inline_keyboard)}")
for i, row in enumerate(main_menu_admin.inline_keyboard):
    for j, button in enumerate(row):
        print(f"  [{i}][{j}] {button.text} -> {button.callback_data}")

print("\n3. Админ меню:")
admin_menu = get_admin_menu_keyboard()
print(f"Количество кнопок: {len(admin_menu.inline_keyboard)}")
for i, row in enumerate(admin_menu.inline_keyboard):
    for j, button in enumerate(row):
        print(f"  [{i}][{j}] {button.text} -> {button.callback_data}")

print("\n4. Проверка callback_data:")
# Проверяем, что callback_data для кнопки админ-панели правильный
expected_callback = "menu_admin_panel"
found = False
for row in main_menu_admin.inline_keyboard:
    for button in row:
        if button.callback_data == expected_callback:
            print(f"✅ Кнопка с callback_data='{expected_callback}' найдена у администратора: {button.text}")
            found = True
            break
    if found:
        break

if not found:
    print(f"❌ Кнопка с callback_data='{expected_callback}' НЕ найдена у администратора!")

# Проверяем, что у обычного пользователя этой кнопки нет
found_regular = False
for row in main_menu.inline_keyboard:
    for button in row:
        if button.callback_data == expected_callback:
            found_regular = True
            break
    if found_regular:
        break

if not found_regular:
    print(f"✅ Кнопка с callback_data='{expected_callback}' НЕ отображается обычным пользователям!")
else:
    print(f"❌ Кнопка с callback_data='{expected_callback}' НЕОЖИДАННО отображается обычным пользователям!")

print("\n4. Тест парсинга action:")
test_callbacks = [
    "menu_admin_panel",
    "menu_documents",
    "menu_tests",
    "admin_users",
    "back_to_menu"
]

for callback_data in test_callbacks:
    if callback_data.startswith("menu_"):
        action = callback_data[5:]  # Убираем префикс "menu_"
        print(f"  {callback_data} -> action: {action}")
    else:
        print(f"  {callback_data} -> не menu_ формат")

print("\n=== Тест завершен ===")