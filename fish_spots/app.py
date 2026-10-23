from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = 'supersecretkey_change_this_in_production'

DB_NAME = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Создает таблицы, если их нет"""
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS fish_spots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            location TEXT NOT NULL,
            fish_types TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    spots = conn.execute('SELECT * FROM fish_spots ORDER BY created_at DESC').fetchall()
    conn.close()

    spots_with_images = [
        spot for spot in spots
        if spot['image_url'] and str(spot['image_url']).strip() != ''
    ]

    return render_template('index.html', spots=spots, spots_with_images=spots_with_images)

# --- ОТДЕЛЬНЫЙ РОУТ ДЛЯ ВХОДА ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash('Вы вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            # ТОЛЬКО для входа: ошибка неверного логина/пароля
            flash('Неверный логин или пароль', 'danger')
    
    return render_template('login.html', mode='login')

# --- ОТДЕЛЬНЫЙ РОУТ ДЛЯ РЕГИСТРАЦИИ ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Простая проверка длины пароля (минимум 6 символов)
        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов', 'warning')
            return render_template('login.html', mode='register')

        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                         (username, password_hash))
            conn.commit()
            flash('Регистрация успешна! Теперь войдите.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            # ЧЁТКОЕ сообщение именно для регистрации
            flash('Такой пользователь уже существует, выберите другой логин', 'danger')
        finally:
            conn.close()
    
    return render_template('login.html', mode='register')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
def add_spot():
    if 'user_id' not in session:
        flash('Сначала войдите в систему', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        location = request.form['location']
        fish_types = request.form['fish_types']
        image_url = request.form.get('image_url', '')
        user_id = session['user_id']

        conn = get_db_connection()
        conn.execute(
            'INSERT INTO fish_spots (title, description, location, fish_types, image_url, user_id) VALUES (?, ?, ?, ?, ?, ?)',
            (title, description, location, fish_types, image_url, user_id)
        )
        conn.commit()
        conn.close()
        flash('Рыбное место добавлено!', 'success')
        return redirect(url_for('index'))
    
    return render_template('add.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
