import sqlite3

# =========================
# БАЗА ДАННЫХ
# =========================

conn = sqlite3.connect(
    "database.db"
)

cursor = conn.cursor()

# =========================
# ТАБЛИЦА USERS
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER
)
""")

# =========================
# ТАБЛИЦА HISTORY
# =========================

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
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
        "INSERT INTO users VALUES (?)",
        (user_id,)
    )

    conn.commit()

# =========================
# СОХРАНИТЬ ИСТОРИЮ
# =========================

def save_history(user_id, text):

    cursor.execute(
        "INSERT INTO history VALUES (?, ?)",
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
        ORDER BY rowid DESC
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