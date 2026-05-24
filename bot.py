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

keyboard = ReplyKeyboardMarkup(
    resize_keyboard=True
)

btn_convert = KeyboardButton(
    "💱 Конвертация"
)

btn_rates = KeyboardButton(
    "📈 Курс валют"
)

btn_help = KeyboardButton(
    "ℹ️ Помощь"
)

btn_history = KeyboardButton(
    "📜 История"
)

btn_usd_eur = KeyboardButton(
    "🇺🇸 USD/EUR"
)

btn_usd_rub = KeyboardButton(
    "🇺🇸 USD/RUB"
)

btn_eur_rub = KeyboardButton(
    "🇪🇺 EUR/RUB"
)

btn_gbp_usd = KeyboardButton(
    "🇬🇧 GBP/USD"
)

keyboard.add(
    btn_convert,
    btn_rates
)

keyboard.add(
    btn_help,
    btn_history
)

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

def get_rate(
    from_currency,
    to_currency
):

    pair = (
        f"{from_currency}_"
        f"{to_currency}"
    )

    if pair in cached_rates:

        return cached_rates[pair]

    url = (
        f"https://open.er-api.com/v6/latest/"
        f"{from_currency}"
    )

    response = requests.get(url)

    data = response.json()

    if data["result"] != "success":

        print("Ошибка API:", data)

        raise ValueError(
            "Ошибка API"
        )

    rates = data["rates"]

    if to_currency not in rates:

        raise ValueError(
            "Валюта не найдена"
        )

    rate = rates[to_currency]

    cached_rates[pair] = rate

    return rate

# =========================
# АВТООБНОВЛЕНИЕ
# =========================

async def update_rates():

    while True:

        try:

            print(
                "🔄 Обновление курсов..."
            )

            pairs = [
                ("USD", "EUR"),
                ("USD", "RUB"),
                ("EUR", "RUB"),
                ("GBP", "USD")
            ]

            for (
                from_currency,
                to_currency
            ) in pairs:

                pair = (
                    f"{from_currency}_"
                    f"{to_currency}"
                )

                rate = get_rate(
                    from_currency,
                    to_currency
                )

                cached_rates[pair] = rate

                print(
                    f"✅ {pair}: {rate}"
                )

            print(
                "✅ Курсы обновлены"
            )

        except Exception as e:

            print(
                "❌ Ошибка обновления:",
                e
            )

        await asyncio.sleep(300)

# =========================
# START
# =========================

@dp.message_handler(
    commands=["start"]
)
async def start(
    message: types.Message
):

    try:

        add_user(
            message.from_user.id
        )

    except Exception as e:

        print(
            "Ошибка add_user:",
            e
        )

    await message.answer(
        "👋 Добро пожаловать!\n\n"
        "💱 Формат:\n"
        "100 USD EUR",
        reply_markup=keyboard
    )

# =========================
# HELP
# =========================

@dp.message_handler(
    commands=["help"]
)
async def help_command(
    message: types.Message
):

    await message.answer(
        "ℹ️ Использование бота:\n\n"
        "💱 Формат конвертации:\n"
        "100 USD EUR\n\n"
        "📈 Возможности:\n"
        "• Конвертация валют\n"
        "• Быстрые курсы\n"
        "• Графики\n"
        "• История\n"
        "• Очистка истории"
    )

# =========================
# КНОПКА ПОМОЩЬ
# =========================

@dp.message_handler(
    text=["Помощь", "ℹ️ Помощь"]
)
async def help_button(
    message: types.Message
):

    await help_command(message)

# =========================
# КОНВЕРТАЦИЯ
# =========================

@dp.message_handler(
    text=["Конвертация", "💱 Конвертация"]
)
async def convert_button(
    message: types.Message
):

    await message.answer(
        "💱 Введите:\n\n"
        "100 USD EUR"
    )

# =========================
# КУРСЫ ВАЛЮТ
# =========================

@dp.message_handler(
    text=["Курс валют", "📈 Курс валют"]
)
async def rates_button(
    message: types.Message
):

    try:

        usd_rub = get_rate(
            "USD",
            "RUB"
        )

        usd_eur = get_rate(
            "USD",
            "EUR"
        )

        eur_rub = get_rate(
            "EUR",
            "RUB"
        )

        text = (
            "📈 Курсы валют:\n\n"
            f"🇺🇸 USD/RUB: "
            f"{usd_rub:.2f}\n"
            f"🇺🇸 USD/EUR: "
            f"{usd_eur:.4f}\n"
            f"🇪🇺 EUR/RUB: "
            f"{eur_rub:.2f}"
        )

        await message.answer(text)

    except Exception as e:

        print(e)

        await message.answer(
            "❌ Ошибка загрузки курсов"
        )

# =========================
# ИСТОРИЯ
# =========================

@dp.message_handler(
    text=["История", "📜 История"]
)
async def history(
    message: types.Message
):

    try:

        history_data = get_history(
            message.from_user.id
        )

        print(
            "История:",
            history_data
        )

        if len(history_data) == 0:

            await message.answer(
                "📭 История пуста"
            )

            return

        text = (
            "📜 Последние "
            "конвертации:\n\n"
        )

        for item in history_data:

            text += f"• {item}\n"

        inline_kb = InlineKeyboardMarkup()

        btn_clear = InlineKeyboardButton(
            "🗑 Очистить",
            callback_data="clear_history"
        )

        inline_kb.add(btn_clear)

        await message.answer(
            text,
            reply_markup=inline_kb
        )

    except Exception as e:

        print(
            "Ошибка истории:",
            e
        )

        await message.answer(
            "❌ Ошибка истории"
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
async def quick_rates(
    message: types.Message
):

    try:

        pair = (
            message.text
            .split(" ")[1]
        )

        (
            from_currency,
            to_currency
        ) = pair.split("/")

        rate = get_rate(
            from_currency,
            to_currency
        )

        text = (
            f"⚡ {from_currency}/"
            f"{to_currency}\n\n"
            f"📈 1 {from_currency} = "
            f"{rate:.4f} "
            f"{to_currency}"
        )

        inline_kb = (
            InlineKeyboardMarkup(
                row_width=2
            )
        )

        btn_graph = (
            InlineKeyboardButton(
                "📊 График",
                callback_data=(
                    f"graph_"
                    f"{from_currency}_"
                    f"{to_currency}"
                )
            )
        )

        btn_rate = (
            InlineKeyboardButton(
                "📈 Курс",
                callback_data=(
                    f"rate_"
                    f"{from_currency}_"
                    f"{to_currency}"
                )
            )
        )

        inline_kb.add(
            btn_graph,
            btn_rate
        )

        await message.answer(
            text,
            reply_markup=inline_kb
        )

    except Exception as e:

        print(e)

        await message.answer(
            "❌ Ошибка"
        )

# =========================
# КОНВЕРТАЦИЯ ВАЛЮТ
# =========================

@dp.message_handler()
async def convert_currency(
    message: types.Message
):

    try:

        parts = (
            message.text
            .strip()
            .split()
        )

        if len(parts) != 3:

            return

        amount = float(parts[0])

        from_currency = (
            parts[1].upper()
        )

        to_currency = (
            parts[2].upper()
        )

        rate = get_rate(
            from_currency,
            to_currency
        )

        result = amount * rate

        result_text = (
            f"💱 {amount:.2f} "
            f"{from_currency} = "
            f"{result:.2f} "
            f"{to_currency}\n\n"
            f"📈 Курс:\n"
            f"1 {from_currency} = "
            f"{rate:.4f} "
            f"{to_currency}"
        )

        # =========================
        # СОХРАНЕНИЕ ИСТОРИИ
        # =========================

        history_text = (
            f"{amount:.2f} "
            f"{from_currency} → "
            f"{result:.2f} "
            f"{to_currency}"
        )

        print(
            "Сохраняем:",
            history_text
        )

        try:

            save_history(
                message.from_user.id,
                history_text
            )

            print(
                "История сохранена"
            )

            print(
                "После сохранения:",
                get_history(
                    message.from_user.id
                )
            )

        except Exception as history_error:

            print(
                "Ошибка истории:",
                history_error
            )

        # =========================
        # INLINE-КНОПКИ
        # =========================

        inline_kb = (
            InlineKeyboardMarkup(
                row_width=2
            )
        )

        btn_graph = (
            InlineKeyboardButton(
                "📊 График",
                callback_data=(
                    f"graph_"
                    f"{from_currency}_"
                    f"{to_currency}"
                )
            )
        )

        btn_rate = (
            InlineKeyboardButton(
                "📈 Курс",
                callback_data=(
                    f"rate_"
                    f"{from_currency}_"
                    f"{to_currency}"
                )
            )
        )

        btn_reverse = (
            InlineKeyboardButton(
                "🔄 Поменять",
                callback_data=(
                    f"reverse_"
                    f"{amount}_"
                    f"{to_currency}_"
                    f"{from_currency}"
                )
            )
        )

        inline_kb.add(
            btn_graph,
            btn_rate
        )

        inline_kb.add(
            btn_reverse
        )

        await message.answer(
            result_text,
            reply_markup=inline_kb
        )

    except Exception as e:

        print(
            "Ошибка конвертации:",
            e
        )

        await message.answer(
            "❌ Ошибка конвертации"
        )

# =========================
# КНОПКА КУРС
# =========================

@dp.callback_query_handler(
    lambda c:
    c.data.startswith("rate_")
)
async def show_rate(
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

        await callback.message.answer(
            f"📈 1 "
            f"{from_currency} = "
            f"{rate:.4f} "
            f"{to_currency}"
        )

        await callback.answer()

    except Exception as e:

        print(
            "Ошибка курса:",
            e
        )

        await callback.answer(
            "❌ Ошибка"
        )

# =========================
# REVERSE
# =========================

@dp.callback_query_handler(
    lambda c:
    c.data.startswith("reverse_")
)
async def reverse_currency(
    callback: types.CallbackQuery
):

    try:

        (
            _,
            amount,
            from_currency,
            to_currency
        ) = callback.data.split("_")

        amount = float(amount)

        rate = get_rate(
            from_currency,
            to_currency
        )

        result = amount * rate

        await callback.message.answer(
            f"🔄 {amount:.2f} "
            f"{from_currency} = "
            f"{result:.2f} "
            f"{to_currency}"
        )

        await callback.answer()

    except Exception as e:

        print(
            "Ошибка reverse:",
            e
        )

        await callback.answer(
            "❌ Ошибка"
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

        dates = []
        rates = []

        for i in range(7):

            fake_rate = (
                get_rate(
                    from_currency,
                    to_currency
                )
                * (
                    1 +
                    (i - 3) * 0.01
                )
            )

            date = (
                datetime.now()
                - timedelta(
                    days=6 - i
                )
            ).strftime("%d.%m")

            dates.append(date)
            rates.append(fake_rate)

        plt.figure(
            figsize=(10, 5)
        )

        plt.plot(
            dates,
            rates,
            marker="o",
            linewidth=3
        )

        plt.title(
            f"{from_currency}/"
            f"{to_currency}"
        )

        plt.xlabel("Дата")
        plt.ylabel("Курс")

        plt.grid(True)

        filename = (
            f"{from_currency}_"
            f"{to_currency}.png"
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
                    f"📊 График "
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
# ОЧИСТКА ИСТОРИИ
# =========================

@dp.callback_query_handler(
    lambda c:
    c.data == "clear_history"
)
async def clear_history_callback(
    callback: types.CallbackQuery
):

    try:

        clear_history(
            callback.from_user.id
        )

        await callback.message.edit_text(
            "🗑 История очищена"
        )

        await callback.answer()

    except Exception as e:

        print(e)

        await callback.answer(
            "❌ Ошибка"
        )

# =========================
# ЗАПУСК
# =========================

async def on_startup(dp):

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