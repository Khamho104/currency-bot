import sqlite3

# =========================
# ПОДКЛЮЧЕНИЕ
# =========================

def connect_db():

    return sqlite3.connect(
        "database.db"
    )

# =========================
# СОЗДАНИЕ ТАБЛИЦ
# =========================

conn = connect_db()

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    user_id INTEGER,
    text TEXT
)
""")

conn.commit()

conn.close()

# =========================
# ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ
# =========================

def add_user(user_id):

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO users VALUES (?)",
        (user_id,)
    )

    conn.commit()

    conn.close()

# =========================
# СОХРАНИТЬ ИСТОРИЮ
# =========================

def save_history(user_id, text):

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO history VALUES (?, ?)",
        (user_id, text)
    )

    conn.commit()

    conn.close()

# =========================
# ПОЛУЧИТЬ ИСТОРИЮ
# =========================

def get_history(user_id):

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT text
        FROM history
        WHERE user_id = ?
        ORDER BY rowid DESC
        LIMIT 10
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]

# =========================
# ОЧИСТИТЬ ИСТОРИЮ
# =========================

def clear_history(user_id):

    conn = connect_db()

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM history
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()

    conn.close()