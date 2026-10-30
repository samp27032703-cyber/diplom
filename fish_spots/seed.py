import sqlite3

DB_NAME = 'database.db'
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Удаляем старую тестовую точку, если она есть
cursor.execute("DELETE FROM fish_spots WHERE title = ?", ("Тестовый пруд",))

# Вставляем точку. Добавляем user_id=1 (предполагаем, что первый пользователь имеет id 1)
# Если у тебя пользователей ещё нет вообще, используй Вариант 2 ниже.
cursor.execute(
    """INSERT INTO fish_spots (title, location, latitude, longitude, user_id) 
       VALUES (?, ?, ?, ?, ?)""",
    ("Тестовый пруд", "Москва, центр", 55.751244, 37.618423, 1)
)

conn.commit()
conn.close()
print("Готово! Тестовая точка добавлена.")
