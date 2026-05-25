import sqlite3

# =========================
# ПОДКЛЮЧЕНИЕ К БАЗЕ
# =========================

conn = sqlite3.connect(
    "database.db",
    check_same_thread=False
)

cursor = conn.cursor()

# =========================
# СОЗДАНИЕ ТАБЛИЦ
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    text TEXT
)
""")

conn.commit()

# =========================
# ДОБАВИТЬ ПОЛЬЗОВАТЕЛЯ
# =========================

def add_user(user_id):

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (user_id)
        VALUES (?)
        """,
        (user_id,)
    )

    conn.commit()

# =========================
# СОХРАНИТЬ ИСТОРИЮ
# =========================

def save_history(user_id, text):

    cursor.execute(
        """
        INSERT INTO history (user_id, text)
        VALUES (?, ?)
        """,
        (user_id, text)
    )

    conn.commit()

# =========================
# ПОЛУЧИТЬ ИСТОРИЮ
# =========================

def get_history(user_id):

    cursor.execute(
        """
        SELECT text
        FROM history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 10
        """,
        (user_id,)
    )

    rows = cursor.fetchall()

    return [row[0] for row in rows]

# =========================
# ОЧИСТИТЬ ИСТОРИЮ
# =========================

def clear_history(user_id):

    cursor.execute(
        """
        DELETE FROM history
        WHERE user_id = ?
        """,
        (user_id,)
    )

    conn.commit()