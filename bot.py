import logging
import requests
import sqlite3

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv
import os

# =========================
# ЗАГРУЗКА .ENV
# =========================
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

logging.basicConfig(level=logging.INFO)

# =========================
# БАЗА ДАННЫХ
# =========================
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Таблица пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    username TEXT
)
""")

# Таблица истории
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    request TEXT,
    result TEXT
)
""")

conn.commit()

# =========================
# ФУНКЦИИ БАЗЫ ДАННЫХ
# =========================

def add_user(user_id, username):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)",
        (user_id, username)
    )
    conn.commit()


def save_history(user_id, request, result):
    cursor.execute(
        "INSERT INTO history (user_id, request, result) VALUES (?, ?, ?)",
        (user_id, request, result)
    )
    conn.commit()


def get_history(user_id):
    cursor.execute(
        """
        SELECT request, result
        FROM history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
        """,
        (user_id,)
    )

    return cursor.fetchall()

# =========================
# КЛАВИАТУРА
# =========================
main_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

btn_convert = KeyboardButton("💱 Конвертация")
btn_help = KeyboardButton("ℹ️ Помощь")
btn_rates = KeyboardButton("📈 Курсы валют")
btn_history = KeyboardButton("🕘 История")

main_keyboard.add(btn_convert)
main_keyboard.row(btn_help, btn_rates)
main_keyboard.add(btn_history)

# =========================
# СПИСОК ВАЛЮТ
# =========================
currencies_text = """
💵 Доступные валюты:

USD — Доллар США
EUR — Евро
RUB — Российский рубль
GBP — Фунт стерлингов
JPY — Японская йена
CNY — Китайский юань
KZT — Казахстанский тенге
UAH — Украинская гривна
"""

# =========================
# /START
# =========================
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):

    # Сохранение пользователя
    add_user(
        message.from_user.id,
        message.from_user.username
    )

    text = (
        "👋 <b>Добро пожаловать в Currency Converter Bot!</b>\n\n"
        "💱 <b>Формат конвертации:</b>\n"
        "<code>100 USD EUR</code>\n\n"
        "📌 <b>Пример:</b>\n"
        "<code>250 EUR RUB</code>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_keyboard
    )

# =========================
# /HELP
# =========================
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):

    text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "Бот умеет конвертировать валюты.\n\n"
        "💱 Формат:\n"
        "<code>100 USD EUR</code>\n\n"
        "📌 Пример:\n"
        "<code>250 EUR RUB</code>\n\n"
        "📈 Используй кнопку 'Курсы валют', "
        "чтобы посмотреть список валют.\n\n"
        "🕘 Кнопка 'История' показывает последние 5 запросов."
    )

    await message.answer(
        text,
        parse_mode="HTML"
    )

# =========================
# КНОПКА ПОМОЩЬ
# =========================
@dp.message_handler(lambda message: message.text == "ℹ️ Помощь")
async def help_button(message: types.Message):

    await help_command(message)

# =========================
# КНОПКА КУРСЫ ВАЛЮТ
# =========================
@dp.message_handler(lambda message: message.text == "📈 Курсы валют")
async def currencies_button(message: types.Message):

    await message.answer(currencies_text)

# =========================
# КНОПКА КОНВЕРТАЦИЯ
# =========================
@dp.message_handler(lambda message: message.text == "💱 Конвертация")
async def convert_info(message: types.Message):

    text = (
        "💱 Введите сумму и валюты:\n\n"
        "<code>100 USD EUR</code>"
    )

    await message.answer(
        text,
        parse_mode="HTML"
    )

# =========================
# КНОПКА ИСТОРИЯ
# =========================
@dp.message_handler(lambda message: message.text == "🕘 История")
async def history_button(message: types.Message):

    history = get_history(message.from_user.id)

    if not history:
        await message.answer("❌ История пуста.")
        return

    text = "🕘 <b>Последние конвертации:</b>\n\n"

    for req, result in history:

        text += (
            f"💱 <code>{req}</code>\n"
            f"✅ {result}\n\n"
        )

    await message.answer(
        text,
        parse_mode="HTML"
    )

# =========================
# КОНВЕРТАЦИЯ ВАЛЮТ
# =========================
@dp.message_handler()
async def convert_currency(message: types.Message):

    try:
        data = message.text.upper().split()

        if len(data) != 3:
            await message.answer(
                "❌ Неверный формат.\n\n"
                "Введите:\n"
                "<code>100 USD EUR</code>",
                parse_mode="HTML"
            )
            return

        amount = float(data[0])
        from_currency = data[1]
        to_currency = data[2]

        # API запрос
        url = (
            f"https://api.exchangerate.host/convert"
            f"?from={from_currency}"
            f"&to={to_currency}"
            f"&amount={amount}"
        )

        response = requests.get(url)
        result = response.json()

        converted = result["result"]

        # Сохранение истории
        save_history(
            message.from_user.id,
            message.text,
            f"{converted:.2f} {to_currency}"
        )

        answer = (
            f"💱 <b>Конвертация валют</b>\n\n"
            f"💵 {amount} {from_currency}\n"
            f"➡️ {converted:.2f} {to_currency}"
        )

        await message.answer(
            answer,
            parse_mode="HTML"
        )

    except Exception as e:

        print(e)

        await message.answer(
            "❌ Ошибка.\n\n"
            "Введите данные в формате:\n"
            "<code>100 USD EUR</code>",
            parse_mode="HTML"
        )

# =========================
# ЗАПУСК БОТА
# =========================
if __name__ == "__main__":

    print("Бот запущен")

    executor.start_polling(
        dp,
        skip_updates=True
    )