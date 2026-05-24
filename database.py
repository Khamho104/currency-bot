import sqlite3

# Подключение
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# Создание таблицы пользователей
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER
)
""")

# Создание таблицы истории
cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    user_id INTEGER,
    result TEXT
)
""")

conn.commit()


# Добавление пользователя
def add_user(user_id):
    cursor.execute(
        "INSERT INTO users (user_id) VALUES (?)",
        (user_id,)
    )

    conn.commit()


# Сохранение истории
def save_history(user_id, result):
    cursor.execute(
        "INSERT INTO history (user_id, result) VALUES (?, ?)",
        (user_id, result)
    )

    conn.commit()


# Получение истории
def get_history(user_id):
    cursor.execute(
        "SELECT result FROM history WHERE user_id = ? ORDER BY ROWID DESC LIMIT 5",
        (user_id,)
    )

    rows = cursor.fetchall()

    return [row[0] for row in rows]