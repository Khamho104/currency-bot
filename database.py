import sqlite3

# Подключение к БД
conn = sqlite3.connect("bot.db")
cursor = conn.cursor()

# Таблица пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    username TEXT
)
""")

# Таблица истории конвертаций
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER,
    amount REAL,
    from_currency TEXT,
    to_currency TEXT,
    result REAL
)
""")

conn.commit()


def add_user(telegram_id, username):
    cursor.execute(
        "INSERT OR IGNORE INTO users (telegram_id, username) VALUES (?, ?)",
        (telegram_id, username)
    )
    conn.commit()


def save_history(telegram_id, amount, from_currency, to_currency, result):
    cursor.execute("""
    INSERT INTO history (
        telegram_id,
        amount,
        from_currency,
        to_currency,
        result
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        telegram_id,
        amount,
        from_currency,
        to_currency,
        result
    ))
    conn.commit()


def get_history(telegram_id):
    cursor.execute("""
    SELECT amount, from_currency, to_currency, result
    FROM history
    WHERE telegram_id = ?
    ORDER BY id DESC
    LIMIT 5
    """, (telegram_id,))

    return cursor.fetchall()