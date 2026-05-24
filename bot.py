import os
import requests
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from database import add_user, save_history, get_history

# Загрузка .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Запуск бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Кнопки
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

btn_convert = KeyboardButton("Конвертация")
btn_rates = KeyboardButton("Курс валют")
btn_help = KeyboardButton("Помощь")
btn_history = KeyboardButton("История")

keyboard.add(btn_convert, btn_rates)
keyboard.add(btn_help, btn_history)


# Команда /start
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    add_user(message.from_user.id)

    await message.answer(
        "👋 Добро пожаловать в Currency Converter Bot!\n\n"
        "Введите сумму и валюты:\n"
        "Например:\n"
        "100 USD EUR",
        reply_markup=keyboard
    )


# Команда /help
@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.answer(
        "📌 Доступные команды:\n\n"
        "/start — запуск бота\n"
        "/help — помощь\n\n"
        "Для конвертации используйте формат:\n"
        "100 USD EUR"
    )


# Кнопка Конвертация
@dp.message_handler(lambda message: message.text == "Конвертация")
async def convert_button(message: types.Message):
    await message.answer(
        "💱 Введите данные в формате:\n"
        "100 USD EUR"
    )


# Кнопка Курс валют
@dp.message_handler(lambda message: message.text == "Курс валют")
async def rates_button(message: types.Message):
    await message.answer(
        "📈 Популярные валюты:\n\n"
        "USD — Доллар США\n"
        "EUR — Евро\n"
        "RUB — Российский рубль\n"
        "GBP — Фунт стерлингов\n"
        "JPY — Японская йена\n"
        "KZT — Казахстанский тенге"
    )


# Кнопка Помощь
@dp.message_handler(lambda message: message.text == "Помощь")
async def help_button(message: types.Message):
    await message.answer(
        "ℹ️ Пример использования:\n\n"
        "100 USD EUR"
    )


# История
@dp.message_handler(lambda message: message.text == "История")
async def history(message: types.Message):
    history_data = get_history(message.from_user.id)

    if not history_data:
        await message.answer("📭 История пуста.")
        return

    text = "📜 Последние конвертации:\n\n"

    for item in history_data:
        text += f"{item}\n"

    await message.answer(text)


# Конвертация валют
@dp.message_handler(lambda message: len(message.text.split()) == 3)
async def convert_currency(message: types.Message):
    try:
        data = message.text.strip().split()

        amount = float(data[0])
        from_currency = data[1].upper()
        to_currency = data[2].upper()

        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

        response = requests.get(url)

        data_json = response.json()

        if "rates" not in data_json:
            await message.answer("❌ Неверная валюта.")
            return

        if to_currency not in data_json["rates"]:
            await message.answer("❌ Валюта не найдена.")
            return

        rate = data_json["rates"][to_currency]

        result = amount * rate

        result_text = (
            f"💱 {amount:.2f} {from_currency} = "
            f"{result:.2f} {to_currency}"
        )

        save_history(message.from_user.id, result_text)

        await message.answer(result_text)

    except Exception as e:
        print(e)

        await message.answer(
            "❌ Ошибка.\n\n"
            "Введите данные в формате:\n"
            "100 USD EUR"
        )