from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
# Секретный ключ для сессий (в продакшене меняй на случайную строку)
app.secret_key = 'supersecretkey_change_me_later_12345'
DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Инициализирует базу. 
    ВАЖНО: Если у тебя в базе УЖЕ есть колонка user_id в fish_spots — 
    этот код НЕ будет её создавать, чтобы не вызвать ошибку. 
    Он просто проверит, что таблицы есть.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Таблица мест. 
    # Мы НЕ добавляем user_id здесь принудительно. 
    # Если он уже есть в твоей базе (из-за старых миграций) — SQLite просто проигнорирует этот CREATE,
    # и структура останется той, что в файле database.db.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fish_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT,
            fish_types TEXT,
            latitude REAL,
            longitude REAL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    init_db()
    conn = get_db_connection()
    # Выбираем все колонки. Если в базе есть user_id — он тоже придёт, но нам он не нужен для карты.
    spots = conn.execute('SELECT * FROM fish_spots').fetchall()
    conn.close()
    
    spots_list = [dict(row) for row in spots]
    return render_template('index.html', spots=spots, spots_json=spots_list)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Привет, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный логин или пароль', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Заполните все поля', 'danger')
            return redirect(url_for('register'))
        
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
            conn.commit()
            flash('Аккаунт создан! Теперь войдите.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Такой пользователь уже существует', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

@app.route('/add', methods=['GET', 'POST'])
def add_spot():
    # Проверка авторизации
    if 'user_id' not in session:
        flash('Сначала войдите в систему', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title')
        location = request.form.get('location')
        fish_types = request.form.get('fish_types')
        description = request.form.get('description')
        
        lat = request.form.get('latitude')
        lon = request.form.get('longitude')
        latitude = float(lat) if lat else None
        longitude = float(lon) if lon else None
        
        # Получаем ID текущего пользователя
        current_user_id = session.get('user_id')
        
        conn = get_db_connection()
        try:
            # ПРОВЕРКА: Пытаемся узнать, есть ли колонка user_id в базе прямо сейчас
            cursor = conn.execute("SELECT * FROM fish_spots LIMIT 1")
            columns = [desc[0] for desc in cursor.description]
            
            if 'user_id' in columns:
                # Вариант А: Колонка ЕСТЬ. Вставляем с user_id
                conn.execute(
                    '''INSERT INTO fish_spots 
                       (title, description, location, fish_types, latitude, longitude, user_id) 
                       VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (title, description, location, fish_types, latitude, longitude, current_user_id)
                )
            else:
                # Вариант Б: Колонки НЕТ. Вставляем без user_id (старый формат)
                conn.execute(
                    '''INSERT INTO fish_spots 
                       (title, description, location, fish_types, latitude, longitude) 
                       VALUES (?, ?, ?, ?, ?, ?)''',
                    (title, description, location, fish_types, latitude, longitude)
                )
            
            conn.commit()
            flash('Место добавлено!', 'success')
            return redirect(url_for('index'))
            
        except sqlite3.Error as e:
            flash(f'Ошибка базы данных: {str(e)}', 'danger')
            conn.rollback()
        finally:
            conn.close()
    
    return render_template('add.html')

if __name__ == '__main__':
    init_db()
    print(f"Сервер запущен. База: {os.path.abspath(DB_NAME)}")
    app.run(debug=True)
