import os
import requests
import matplotlib.pyplot as plt

from datetime import datetime, timedelta
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, executor, types

from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from database import add_user, save_history, get_history

# =========================
# ЗАГРУЗКА ТОКЕНА
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден!")

# =========================
# ЗАПУСК БОТА
# =========================

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# =========================
# КЛАВИАТУРА
# =========================

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

btn_convert = KeyboardButton("💱 Конвертация")
btn_rates = KeyboardButton("📈 Курс валют")
btn_help = KeyboardButton("ℹ️ Помощь")
btn_history = KeyboardButton("📜 История")

keyboard.add(btn_convert, btn_rates)
keyboard.add(btn_help, btn_history)

# =========================
# /START
# =========================

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    add_user(message.from_user.id)

    await message.answer(
        "👋 Добро пожаловать в Currency Converter Bot!\n\n"
        "💱 Введите данные в формате:\n"
        "100 USD EUR",
        reply_markup=keyboard
    )

# =========================
# /HELP
# =========================

@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):
    await message.answer(
        "📌 Доступные команды:\n\n"
        "/start — запуск бота\n"
        "/help — помощь\n\n"
        "💱 Для конвертации используйте формат:\n"
        "100 USD EUR"
    )

# =========================
# КНОПКА КОНВЕРТАЦИЯ
# =========================

@dp.message_handler(
    lambda message: message.text in [
        "Конвертация",
        "💱 Конвертация"
    ]
)
async def convert_button(message: types.Message):
    await message.answer(
        "💱 Введите данные:\n\n"
        "100 USD EUR"
    )

# =========================
# КНОПКА КУРС ВАЛЮТ
# =========================

@dp.message_handler(
    lambda message: message.text in [
        "Курс валют",
        "📈 Курс валют"
    ]
)
async def rates_button(message: types.Message):
    await message.answer(
        "📈 Популярные валюты:\n\n"
        "🇺🇸 USD — Доллар США\n"
        "🇪🇺 EUR — Евро\n"
        "🇷🇺 RUB — Российский рубль\n"
        "🇬🇧 GBP — Фунт стерлингов\n"
        "🇯🇵 JPY — Японская йена\n"
        "🇰🇿 KZT — Тенге"
    )

# =========================
# КНОПКА ПОМОЩЬ
# =========================

@dp.message_handler(
    lambda message: message.text in [
        "Помощь",
        "ℹ️ Помощь"
    ]
)
async def help_button(message: types.Message):
    await message.answer(
        "ℹ️ Пример использования:\n\n"
        "100 USD EUR"
    )

# =========================
# ИСТОРИЯ
# =========================

@dp.message_handler(
    lambda message: message.text in [
        "История",
        "📜 История"
    ]
)
async def history(message: types.Message):
    history_data = get_history(message.from_user.id)

    if not history_data:
        await message.answer("📭 История пуста.")
        return

    text = "📜 Последние конвертации:\n\n"

    for item in history_data:
        text += f"{item}\n"

    await message.answer(text)

# =========================
# КОНВЕРТАЦИЯ ВАЛЮТ
# =========================

@dp.message_handler()
async def convert_currency(message: types.Message):
    try:
        parts = message.text.strip().split()

        if len(parts) != 3:
            raise ValueError

        amount = float(parts[0])

        from_currency = parts[1].upper()
        to_currency = parts[2].upper()

        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

        response = requests.get(url)

        data = response.json()

        if "rates" not in data:
            await message.answer("❌ Неверная валюта.")
            return

        if to_currency not in data["rates"]:
            await message.answer("❌ Валюта не найдена.")
            return

        rate = data["rates"][to_currency]

        result = amount * rate

        result_text = (
            f"💱 {amount:.2f} {from_currency} = "
            f"{result:.2f} {to_currency}"
        )

        save_history(message.from_user.id, result_text)

        # =========================
        # INLINE-КНОПКИ
        # =========================

        inline_kb = InlineKeyboardMarkup(row_width=2)

        btn_reverse = InlineKeyboardButton(
            "🔄 Поменять валюты",
            callback_data=f"reverse_{amount}_{to_currency}_{from_currency}"
        )

        btn_rate = InlineKeyboardButton(
            "📈 Курс",
            callback_data=f"rate_{from_currency}_{to_currency}"
        )

        btn_graph = InlineKeyboardButton(
            "📊 График",
            callback_data=f"graph_{from_currency}_{to_currency}"
        )

        inline_kb.add(btn_reverse, btn_rate)
        inline_kb.add(btn_graph)

        await message.answer(
            result_text,
            reply_markup=inline_kb
        )

    except Exception as e:
        print(e)

        await message.answer(
            "❌ Ошибка.\n\n"
            "Введите данные в формате:\n"
            "100 USD EUR"
        )

# =========================
# REVERSE КНОПКА
# =========================

@dp.callback_query_handler(lambda c: c.data.startswith("reverse_"))
async def reverse_currency(callback: types.CallbackQuery):
    try:
        _, amount, from_currency, to_currency = callback.data.split("_")

        amount = float(amount)

        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

        response = requests.get(url)

        data = response.json()

        rate = data["rates"][to_currency]

        result = amount * rate

        await callback.message.answer(
            f"🔄 {amount:.2f} {from_currency} = "
            f"{result:.2f} {to_currency}"
        )

        await callback.answer()

    except Exception as e:
        print(e)
        await callback.answer("❌ Ошибка")

# =========================
# КНОПКА КУРС
# =========================

@dp.callback_query_handler(lambda c: c.data.startswith("rate_"))
async def show_rate(callback: types.CallbackQuery):
    try:
        _, from_currency, to_currency = callback.data.split("_")

        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

        response = requests.get(url)

        data = response.json()

        rate = data["rates"][to_currency]

        await callback.message.answer(
            f"📈 1 {from_currency} = {rate:.2f} {to_currency}"
        )

        await callback.answer()

    except Exception as e:
        print(e)
        await callback.answer("❌ Ошибка")

# =========================
# КНОПКА ГРАФИК
# =========================

@dp.callback_query_handler(lambda c: c.data.startswith("graph_"))
async def show_graph(callback: types.CallbackQuery):
    try:
        _, from_currency, to_currency = callback.data.split("_")

        dates = []
        rates = []

        # Получаем курс за 7 дней
        for i in range(7):
            date = datetime.now() - timedelta(days=6 - i)

            url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"

            response = requests.get(url)

            data = response.json()

            rate = data["rates"][to_currency]

            dates.append(date.strftime("%d.%m"))
            rates.append(rate)

        # =========================
        # СОЗДАНИЕ ГРАФИКА
        # =========================

        plt.figure(figsize=(8, 4))

        plt.plot(dates, rates, marker="o")

        plt.title(f"{from_currency}/{to_currency} — 7 дней")

        plt.xlabel("Дата")
        plt.ylabel("Курс")

        plt.grid(True)

        # =========================
        # СОХРАНЕНИЕ PNG
        # =========================

        filename = f"{from_currency}_{to_currency}.png"

        plt.savefig(filename)

        plt.close()

        # =========================
        # ОТПРАВКА ГРАФИКА
        # =========================

        with open(filename, "rb") as photo:
            await bot.send_photo(
                callback.from_user.id,
                photo,
                caption=f"📊 График {from_currency}/{to_currency}"
            )

        await callback.answer()

    except Exception as e:
        print(e)
        await callback.answer("❌ Ошибка графика")

# =========================
# ЗАПУСК БОТА
# =========================

if __name__ == "__main__":
    print("🚀 Бот запущен...")
    executor.start_polling(dp, skip_updates=True)