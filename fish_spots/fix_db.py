import sqlite3

DB_NAME = 'database.db'
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

print("Начинаю исправление базы данных...")

# 1. Проверяем, есть ли колонка user_id. Если нет — добавляем её.
# Если она уже есть, эта команда просто ничего не сделает (не вызовет ошибку).
try:
    cursor.execute("ALTER TABLE fish_spots ADD COLUMN user_id INTEGER DEFAULT NULL")
    print("Колонка user_id добавлена.")
except sqlite3.OperationalError:
    # OperationalError значит, что колонка уже существует. Это нормально.
    print("Колонка user_id уже существует, пропускаем добавление.")

# 2. ВАЖНО: Заполняем пустые user_id значением 1 (для старых записей, если они были)
# Это нужно, чтобы снять ошибку NOT NULL, если мы потом решим сделать колонку NOT NULL.
cursor.execute("UPDATE fish_spots SET user_id = 1 WHERE user_id IS NULL")

# 3. Теперь делаем колонку обязательной (NOT NULL), но так как мы только что заполнили пустоты,
# база не будет ругаться.
try:
    # В SQLite нельзя сделать ALTER COLUMN, поэтому мы делаем хитрость:
    # Создаем новую таблицу, копируем данные, удаляем старую, переименовываем новую.
    
    print("Пересоздаю таблицу fish_spots с обязательным user_id...")
    
    # Сохраняем текущие данные во временную таблицу
    cursor.execute("CREATE TEMP TABLE temp_fish_spots AS SELECT * FROM fish_spots")
    
    # Удаляем старую таблицу
    cursor.execute("DROP TABLE fish_spots")
    
    # Создаем заново с правильным ограничением
    cursor.execute('''
        CREATE TABLE fish_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            fish_types TEXT,
            latitude REAL,
            longitude REAL,
            user_id INTEGER NOT NULL
        )
    ''')
    
    # Возвращаем данные обратно, подставляя user_id=1 там, где его не было
    cursor.execute('''
        INSERT INTO fish_spots (title, description, location, fish_types, latitude, longitude, user_id)
        SELECT title, description, location, fish_types, latitude, longitude, COALESCE(user_id, 1)
        FROM temp_fish_spots
    ''')
    
    print("Таблица успешно пересоздана с обязательным user_id.")

except Exception as e:
    print(f"Произошла ошибка при пересоздании таблицы: {e}")
    print("Скорее всего, таблица уже имеет правильную структуру, продолжаем...")

conn.commit()
conn.close()
print("✅ Готово! База данных исправлена.")
