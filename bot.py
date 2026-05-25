import os
import asyncio
import requests
import matplotlib.pyplot as plt

from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from dotenv import load_dotenv

from database import (
    add_user,
    save_history,
    get_history,
    clear_history,
    save_rate,
    get_rate_history
)

# =========================
# ЗАГРУЗКА .ENV
# =========================

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# =========================
# ИНИЦИАЛИЗАЦИЯ БОТА
# =========================

bot = Bot(token=BOT_TOKEN)

dp = Dispatcher(bot)

# =========================
# КЭШ КУРСОВ
# =========================

cached_rates = {}

POPULAR_PAIRS = [
    "USD_RUB",
    "EUR_RUB",
    "USD_EUR",
    "GBP_USD"
]

# =========================
# КНОПКИ
# =========================

main_keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

main_keyboard.add(
    KeyboardButton("💱 Конвертация"),
    KeyboardButton("📈 Курс валют")
)

main_keyboard.add(
    KeyboardButton("ℹ️ Помощь"),
    KeyboardButton("📜 История")
)

main_keyboard.add(
    KeyboardButton("🇺🇸 USD/EUR"),
    KeyboardButton("🇺🇸 USD/RUB")
)

main_keyboard.add(
    KeyboardButton("🇪🇺 EUR/RUB"),
    KeyboardButton("🇬🇧 GBP/USD")
)

# =========================
# ПОЛУЧЕНИЕ КУРСА
# =========================

def get_rate(from_currency, to_currency):

    pair = f"{from_currency}_{to_currency}"

    if pair in cached_rates:
        return cached_rates[pair]

    url = (
        "https://api.exchangerate.host/convert"
        f"?from={from_currency}"
        f"&to={to_currency}"
    )

    response = requests.get(url)

    data = response.json()

    rate = data.get("result")

    if rate:
        cached_rates[pair] = rate

    return rate

# =========================
# ОБНОВЛЕНИЕ КУРСОВ
# =========================

async def update_rates():

    while True:

        print("🔄 Обновление курсов...")

        for pair in POPULAR_PAIRS:

            try:

                from_currency, to_currency = (
                    pair.split("_")
                )

                rate = get_rate(
                    from_currency,
                    to_currency
                )

                if rate:

                    cached_rates[pair] = rate

                    save_rate(pair, rate)

                    print(
                        f"✅ {pair}: {rate}"
                    )

            except Exception as e:

                print(
                    f"Ошибка {pair}:",
                    e
                )

        await asyncio.sleep(300)

# =========================
# INLINE-КНОПКИ
# =========================

def get_inline_buttons(
    from_currency,
    to_currency
):

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "📊 График",
            callback_data=(
                f"graph_"
                f"{from_currency}_"
                f"{to_currency}"
            )
        ),

        InlineKeyboardButton(
            "📈 Курс",
            callback_data=(
                f"rate_"
                f"{from_currency}_"
                f"{to_currency}"
            )
        )
    )

    return keyboard

# =========================
# /start
# =========================

@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):

    add_user(message.from_user.id)

    text = (
        "👋 Добро пожаловать!\n\n"
        "💱 Отправьте:\n"
        "100 USD EUR\n\n"
        "Или используйте кнопки ниже 👇"
    )

    await message.answer(
        text,
        reply_markup=main_keyboard
    )

# =========================
# ПОМОЩЬ
# =========================

@dp.message_handler(
    lambda message:
    message.text == "ℹ️ Помощь"
)
async def help_command(message: types.Message):

    text = (
        "📘 Примеры:\n\n"
        "100 USD EUR\n"
        "500 EUR RUB\n"
        "1000 RUB USD"
    )

    await message.answer(text)

# =========================
# ИСТОРИЯ
# =========================

@dp.message_handler(
    lambda message:
    message.text == "📜 История"
)
async def history_command(
    message: types.Message
):

    history = get_history(
        message.from_user.id
    )

    if not history:

        await message.answer(
            "📭 История пуста"
        )

        return

    text = "📜 Последние конвертации:\n\n"

    for item in history:

        text += f"• {item}\n"

    keyboard = InlineKeyboardMarkup()

    keyboard.add(
        InlineKeyboardButton(
            "🗑 Очистить",
            callback_data="clear_history"
        )
    )

    await message.answer(
        text,
        reply_markup=keyboard
    )

# =========================
# ОЧИСТКА ИСТОРИИ
# =========================

@dp.callback_query_handler(
    lambda c:
    c.data == "clear_history"
)
async def clear_history_callback(
    callback: types.CallbackQuery
):

    clear_history(
        callback.from_user.id
    )

    await callback.message.edit_text(
        "🗑 История очищена"
    )

# =========================
# КНОПКИ ВАЛЮТ
# =========================

@dp.message_handler(
    lambda message:
    message.text in [
        "🇺🇸 USD/EUR",
        "🇺🇸 USD/RUB",
        "🇪🇺 EUR/RUB",
        "🇬🇧 GBP/USD"
    ]
)
async def quick_pair(
    message: types.Message
):

    pair = (
        message.text
        .replace("🇺🇸 ", "")
        .replace("🇪🇺 ", "")
        .replace("🇬🇧 ", "")
    )

    from_currency, to_currency = (
        pair.split("/")
    )

    rate = get_rate(
        from_currency,
        to_currency
    )

    if not rate:

        await message.answer(
            "❌ Ошибка загрузки курса"
        )

        return

    text = (
        f"⚡ {pair}\n\n"
        f"📈 1 {from_currency} = "
        f"{rate:.4f} {to_currency}"
    )

    await message.answer(
        text,
        reply_markup=get_inline_buttons(
            from_currency,
            to_currency
        )
    )

# =========================
# КУРС ВАЛЮТ
# =========================

@dp.message_handler(
    lambda message:
    message.text == "📈 Курс валют"
)
async def rates_command(
    message: types.Message
):

    text = "📈 Популярные курсы:\n\n"

    for pair in POPULAR_PAIRS:

        try:

            from_currency, to_currency = (
                pair.split("_")
            )

            rate = get_rate(
                from_currency,
                to_currency
            )

            if rate:

                text += (
                    f"💱 "
                    f"1 {from_currency} = "
                    f"{rate:.4f} "
                    f"{to_currency}\n"
                )

        except:
            pass

    await message.answer(text)

# =========================
# INLINE КУРС
# =========================

@dp.callback_query_handler(
    lambda c:
    c.data.startswith("rate_")
)
async def inline_rate(
    callback: types.CallbackQuery
):

    try:

        (
            _,
            from_currency,
            to_currency
        ) = callback.data.split("_")

        rate = get_rate(
            from_currency,
            to_currency
        )

        await callback.answer(
            (
                f"1 {from_currency} = "
                f"{rate:.4f} "
                f"{to_currency}"
            ),
            show_alert=True
        )

    except:

        await callback.answer(
            "Ошибка курса"
        )

# =========================
# ГРАФИК
# =========================

@dp.callback_query_handler(
    lambda c:
    c.data.startswith("graph_")
)
async def show_graph(
    callback: types.CallbackQuery
):

    try:

        (
            _,
            from_currency,
            to_currency
        ) = callback.data.split("_")

        pair = (
            f"{from_currency}_"
            f"{to_currency}"
        )

        history = get_rate_history(pair)

        if len(history) < 2:

            await callback.answer(
                "⏳ Недостаточно данных"
            )

            return

        dates = []
        rates = []

        for rate, created_at in history:

            dates.append(
                created_at[11:16]
            )

            rates.append(rate)

        plt.figure(figsize=(10, 5))

        plt.plot(
            dates,
            rates,
            marker="o",
            linewidth=3
        )

        plt.title(
            f"{from_currency}/{to_currency}"
        )

        plt.xlabel("Время")
        plt.ylabel("Курс")

        plt.grid(True)

        filename = (
            f"{pair}.png"
        )

        plt.savefig(
            filename,
            bbox_inches="tight"
        )

        plt.close()

        with open(
            filename,
            "rb"
        ) as photo:

            await bot.send_photo(
                callback.from_user.id,
                photo,
                caption=(
                    f"📊 Реальный график "
                    f"{from_currency}/"
                    f"{to_currency}"
                )
            )

        await callback.answer()

    except Exception as e:

        print(
            "Ошибка графика:",
            e
        )

        await callback.answer(
            "❌ Ошибка графика"
        )

# =========================
# КОНВЕРТАЦИЯ
# =========================

@dp.message_handler()
async def convert_currency(
    message: types.Message
):

    if message.text == "💱 Конвертация":

        await message.answer(
            "Введите:\n"
            "100 USD EUR"
        )

        return

    try:

        parts = (
            message.text
            .upper()
            .split()
        )

        if len(parts) != 3:
            return

        amount = float(parts[0])

        from_currency = parts[1]

        to_currency = parts[2]

        rate = get_rate(
            from_currency,
            to_currency
        )

        if not rate:

            await message.answer(
                "❌ Ошибка получения курса"
            )

            return

        result = amount * rate

        text = (
            f"💱 {amount} "
            f"{from_currency} = "
            f"{result:.2f} "
            f"{to_currency}"
        )

        save_history(
            message.from_user.id,
            text
        )

        await message.answer(
            text,
            reply_markup=get_inline_buttons(
                from_currency,
                to_currency
            )
        )

    except Exception as e:

        print(e)

        await message.answer(
            "❌ Ошибка конвертации"
        )

# =========================
# ЗАПУСК
# =========================

async def on_startup(_):

    asyncio.create_task(
        update_rates()
    )

    print("🤖 Бот запущен")

if __name__ == "__main__":

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )