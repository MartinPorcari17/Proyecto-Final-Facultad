from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

app = Flask(__name__)
app.secret_key = 'Bonten'

DB_PATH = "database.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS consultas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            service TEXT,
            message TEXT NOT NULL,
            consent INTEGER DEFAULT 0
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    conn.commit()
    conn.close()

#Se implementa persistencia de usuarios con SQLite, separando credenciales de otras entidades.

#Registro de usuarios
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                      (username, password))
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except:
            return "Usuario ya existe"

    return render_template('signup.html')

#Login de usuarios
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return redirect(url_for('home'))
        else:
            return "Credenciales incorrectas"

    return render_template('login.html')

#Ruta de las páginas
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/mis-vis')
def mis_vis():
    return render_template('mis-vis.html')

@app.route('/servicios')
def servicios():
    return render_template('servicios.html')

@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

#Formulario de contacto
@app.route('/submit', methods=['POST'])
def submit():
    try:
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()
        service = request.form.get('service', '').strip()
        message = request.form.get('message', '').strip()
        consent = 1 if request.form.get('consent') else 0

        if not name or not email or not message:
            return redirect(url_for('home', ok=0, err="Faltan campos obligatorios"))

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO consultas (name, email, phone, service, message, consent) VALUES (?, ?, ?, ?, ?, ?)',
                  (name, email, phone, service, message, consent))
        conn.commit()
        conn.close()
        return redirect(url_for('home', ok=1))
    except Exception as e:
        return redirect(url_for('home', ok=0, err=str(e)))

#Logout de usuarios (elimina toda la sesión)
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

#Panel de administración
@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM consultas')
    consultas = c.fetchall()
    conn.close()

    return render_template('admin.html', consultas=consultas)

@app.route('/consulta/<int:id>', methods=['DELETE'])
def delete_consulta(id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM consultas WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return '', 204

@app.route('/consulta/<int:id>', methods=['PUT'])
def update_consulta(id):
    data = request.get_json()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE consultas SET message = ? WHERE id = ?',
              (data['message'], id))
    conn.commit()
    conn.close()
    return '', 204


if __name__ == '__main__':
    init_db()
    app.run(debug=True)
