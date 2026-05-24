import os
import asyncio
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

from database import (
    add_user,
    save_history,
    get_history,
    clear_history
)

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
# КЭШ КУРСОВ
# =========================

cached_rates = {}

# =========================
# КЛАВИАТУРА
# =========================

keyboard = ReplyKeyboardMarkup(resize_keyboard=True)

btn_convert = KeyboardButton("💱 Конвертация")
btn_rates = KeyboardButton("📈 Курс валют")
btn_help = KeyboardButton("ℹ️ Помощь")
btn_history = KeyboardButton("📜 История")

btn_usd_eur = KeyboardButton("🇺🇸 USD/EUR")
btn_usd_rub = KeyboardButton("🇺🇸 USD/RUB")
btn_eur_rub = KeyboardButton("🇪🇺 EUR/RUB")
btn_gbp_usd = KeyboardButton("🇬🇧 GBP/USD")

keyboard.add(btn_convert, btn_rates)
keyboard.add(btn_help, btn_history)

keyboard.add(
    btn_usd_eur,
    btn_usd_rub
)

keyboard.add(
    btn_eur_rub,
    btn_gbp_usd
)

# =========================
# ПОЛУЧЕНИЕ КУРСА
# =========================

def get_rate(from_currency, to_currency):

    pair = f"{from_currency}_{to_currency}"

    # =========================
    # КЭШ
    # =========================

    if pair in cached_rates:
        return cached_rates[pair]

    url = (
        f"https://api.frankfurter.app/latest"
        f"?from={from_currency}&to={to_currency}"
    )

    response = requests.get(url)

    data = response.json()

    if "rates" not in data:
        raise ValueError("Ошибка API")

    if to_currency not in data["rates"]:
        raise ValueError("Валюта не найдена")

    rate = data["rates"][to_currency]

    cached_rates[pair] = rate

    return rate

# =========================
# АВТООБНОВЛЕНИЕ КУРСОВ
# =========================

async def update_rates():

    while True:

        try:

            print("🔄 Обновление курсов...")

            pairs = [
                ("USD", "EUR"),
                ("USD", "RUB"),
                ("EUR", "RUB"),
                ("GBP", "USD")
            ]

            for from_currency, to_currency in pairs:

                pair = f"{from_currency}_{to_currency}"

                url = (
                    f"https://api.frankfurter.app/latest"
                    f"?from={from_currency}&to={to_currency}"
                )

                response = requests.get(url)

                data = response.json()

                if "rates" not in data:
                    continue

                rate = data["rates"][to_currency]

                cached_rates[pair] = rate

                print(f"✅ {pair}: {rate}")

            print("✅ Курсы обновлены\n")

        except Exception as e:

            print("❌ Ошибка обновления:", e)

        # =========================
        # КАЖДЫЕ 5 МИНУТ
        # =========================

        await asyncio.sleep(300)

# =========================
# START
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
# HELP
# =========================

@dp.message_handler(commands=["help"])
async def help_command(message: types.Message):

    await message.answer(
        "📌 Доступные команды:\n\n"
        "/start — запуск бота\n"
        "/help — помощь\n\n"
        "💱 Пример:\n"
        "100 USD EUR"
    )

# =========================
# КНОПКА КОНВЕРТАЦИЯ
# =========================

@dp.message_handler(
    text=["Конвертация", "💱 Конвертация"]
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
    text=["Курс валют", "📈 Курс валют"]
)
async def rates_button(message: types.Message):

    try:

        usd_rub = get_rate("USD", "RUB")
        usd_eur = get_rate("USD", "EUR")
        eur_rub = get_rate("EUR", "RUB")

        text = (
            f"📈 Актуальные курсы:\n\n"
            f"🇺🇸 USD/RUB: {usd_rub:.2f}\n"
            f"🇺🇸 USD/EUR: {usd_eur:.4f}\n"
            f"🇪🇺 EUR/RUB: {eur_rub:.2f}"
        )

        await message.answer(text)

    except Exception as e:

        print("Ошибка курса:", e)

        await message.answer(
            "❌ Не удалось получить курсы"
        )

# =========================
# КНОПКА ПОМОЩЬ
# =========================

@dp.message_handler(
    text=["Помощь", "ℹ️ Помощь"]
)
async def help_button(message: types.Message):

    await message.answer(
        "ℹ️ Использование:\n\n"
        "100 USD EUR"
    )

# =========================
# БЫСТРЫЕ КНОПКИ
# =========================

@dp.message_handler(
    text=[
        "🇺🇸 USD/EUR",
        "🇺🇸 USD/RUB",
        "🇪🇺 EUR/RUB",
        "🇬🇧 GBP/USD"
    ]
)
async def quick_rates(message: types.Message):

    try:

        pair = message.text.split(" ")[1]

        from_currency, to_currency = (
            pair.split("/")
        )

        rate = get_rate(
            from_currency,
            to_currency
        )

        text = (
            f"⚡ Быстрый курс\n\n"
            f"💱 {from_currency}/{to_currency}\n\n"
            f"📈 1 {from_currency} = "
            f"{rate:.4f} {to_currency}"
        )

        inline_kb = InlineKeyboardMarkup()

        btn_graph = InlineKeyboardButton(
            "📊 График",
            callback_data=f"graph_{from_currency}_{to_currency}"
        )

        btn_reverse = InlineKeyboardButton(
            "🔄 Поменять",
            callback_data=f"reverse_1_{to_currency}_{from_currency}"
        )

        inline_kb.add(
            btn_graph,
            btn_reverse
        )

        await message.answer(
            text,
            reply_markup=inline_kb
        )

    except Exception as e:

        print("Ошибка быстрого курса:", e)

        await message.answer(
            "❌ Ошибка быстрого курса"
        )

# =========================
# ИСТОРИЯ
# =========================

@dp.message_handler(
    text=["История", "📜 История"]
)
async def history(message: types.Message):

    try:

        history_data = get_history(
            message.from_user.id
        )

        print("История:", history_data)

        if not history_data:

            await message.answer(
                "📭 История пуста."
            )

            return

        text = "📜 Последние конвертации:\n\n"

        for item in history_data:

            text += f"• {item}\n\n"

        inline_kb = InlineKeyboardMarkup()

        btn_clear = InlineKeyboardButton(
            "🗑 Очистить историю",
            callback_data="clear_history"
        )

        inline_kb.add(btn_clear)

        await message.answer(
            text,
            reply_markup=inline_kb
        )

    except Exception as e:

        print("Ошибка истории:", e)

        await message.answer(
            "❌ Ошибка загрузки истории"
        )

# =========================
# КОНВЕРТАЦИЯ
# =========================

@dp.message_handler()
async def convert_currency(message: types.Message):

    try:

        parts = message.text.strip().split()

        if len(parts) != 3:
            return

        amount = float(parts[0])

        from_currency = parts[1].upper()
        to_currency = parts[2].upper()

        rate = get_rate(
            from_currency,
            to_currency
        )

        result = amount * rate

        result_text = (
            f"💱 {amount:.2f} {from_currency} = "
            f"{result:.2f} {to_currency}\n\n"
            f"📈 Курс:\n"
            f"1 {from_currency} = "
            f"{rate:.4f} {to_currency}"
        )

        # =========================
        # СОХРАНЕНИЕ ИСТОРИИ
        # =========================

        save_history(
            message.from_user.id,
            result_text
        )

        print("История сохранена")

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

        print("Ошибка конвертации:", e)

        await message.answer(
            "❌ Ошибка конвертации"
        )

# =========================
# REVERSE
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("reverse_")
)
async def reverse_currency(
    callback: types.CallbackQuery
):

    try:

        _, amount, from_currency, to_currency = (
            callback.data.split("_")
        )

        amount = float(amount)

        rate = get_rate(
            from_currency,
            to_currency
        )

        result = amount * rate

        await callback.message.answer(
            f"🔄 {amount:.2f} {from_currency} = "
            f"{result:.2f} {to_currency}"
        )

        await callback.answer()

    except Exception as e:

        print("Ошибка reverse:", e)

        await callback.answer("❌ Ошибка")

# =========================
# КНОПКА КУРС
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("rate_")
)
async def show_rate(
    callback: types.CallbackQuery
):

    try:

        _, from_currency, to_currency = (
            callback.data.split("_")
        )

        rate = get_rate(
            from_currency,
            to_currency
        )

        await callback.message.answer(
            f"📈 1 {from_currency} = "
            f"{rate:.4f} {to_currency}"
        )

        await callback.answer()

    except Exception as e:

        print("Ошибка rate:", e)

        await callback.answer("❌ Ошибка")

# =========================
# ГРАФИК
# =========================

@dp.callback_query_handler(
    lambda c: c.data.startswith("graph_")
)
async def show_graph(
    callback: types.CallbackQuery
):

    try:

        _, from_currency, to_currency = (
            callback.data.split("_")
        )

        dates = []
        rates = []

        for i in range(7):

            date = (
                datetime.now()
                - timedelta(days=6 - i)
            ).strftime("%Y-%m-%d")

            url = (
                f"https://api.frankfurter.app/{date}"
                f"?from={from_currency}&to={to_currency}"
            )

            response = requests.get(url)

            data = response.json()

            if "rates" not in data:
                continue

            rate = data["rates"][to_currency]

            dates.append(
                datetime.strptime(
                    date,
                    "%Y-%m-%d"
                ).strftime("%d.%m")
            )

            rates.append(rate)

        if not rates:

            await callback.answer(
                "❌ Нет данных"
            )

            return

        first_rate = rates[0]
        last_rate = rates[-1]

        change_percent = (
            (last_rate - first_rate)
            / first_rate
        ) * 100

        min_rate = min(rates)
        max_rate = max(rates)

        color = "green"

        if change_percent < 0:
            color = "red"

        plt.figure(figsize=(10, 5))

        plt.plot(
            dates,
            rates,
            marker="o",
            linewidth=3,
            color=color
        )

        plt.fill_between(
            dates,
            rates,
            alpha=0.2,
            color=color
        )

        plt.title(
            f"{from_currency}/{to_currency} — 7 дней",
            fontsize=16
        )

        plt.xlabel("Дата")
        plt.ylabel("Курс")

        plt.grid(True)

        filename = (
            f"{from_currency}_{to_currency}.png"
        )

        plt.savefig(
            filename,
            bbox_inches="tight"
        )

        plt.close()

        trend = (
            "📈 Рост"
            if change_percent > 0
            else "📉 Падение"
        )

        caption = (
            f"📊 {from_currency}/{to_currency}\n\n"
            f"{trend}: {change_percent:.2f}%\n"
            f"📉 Минимум: {min_rate:.4f}\n"
            f"📈 Максимум: {max_rate:.4f}\n"
            f"💰 Текущий курс: {last_rate:.4f}"
        )

        with open(filename, "rb") as photo:

            await bot.send_photo(
                callback.from_user.id,
                photo,
                caption=caption
            )

        await callback.answer()

    except Exception as e:

        print("Ошибка графика:", e)

        await callback.answer(
            "❌ Ошибка графика"
        )

# =========================
# ОЧИСТКА ИСТОРИИ
# =========================

@dp.callback_query_handler(
    lambda c: c.data == "clear_history"
)
async def clear_history_callback(
    callback: types.CallbackQuery
):

    try:

        clear_history(
            callback.from_user.id
        )

        await callback.message.edit_text(
            "🗑 История очищена."
        )

        await callback.answer()

    except Exception as e:

        print("Ошибка очистки:", e)

        await callback.answer(
            "❌ Ошибка"
        )

# =========================
# ЗАПУСК БОТА
# =========================

async def on_startup(dp):

    asyncio.create_task(
        update_rates()
    )

    print("🤖 Автообновление включено")

if __name__ == "__main__":

    print("🚀 Бот запущен...")

    executor.start_polling(
        dp,
        skip_updates=True,
        on_startup=on_startup
    )