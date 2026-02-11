from flask import Flask, render_template, request, redirect, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect("ngo.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    db = get_db()
    c = db.cursor()

    c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS admin (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS banners (id INTEGER PRIMARY KEY AUTOINCREMENT, image TEXT, title TEXT, description TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS vision_mission (id INTEGER PRIMARY KEY AUTOINCREMENT, vision TEXT, mission TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS statistics (id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT, value TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS initiatives (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, description TEXT)")

    if c.execute("SELECT * FROM admin").fetchone() is None:
        c.execute("INSERT INTO admin VALUES (NULL,'admin','admin123')")

    if c.execute("SELECT * FROM vision_mission").fetchone() is None:
        c.execute("INSERT INTO vision_mission VALUES (NULL,'Better future for all','Helping society through education')")

    db.commit()
    db.close()

init_db()

@app.route('/', methods=['GET', 'POST'])
def auth():
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        c = db.cursor()

        if action == 'login':
            user = c.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            ).fetchone()
            if user:
                session['user'] = username
                db.close()
                return redirect('/home')

        if action == 'register':
            try:
                c.execute(
                    "INSERT INTO users VALUES (NULL,?,?)",
                    (username, password)
                )
                db.commit()
                session['user'] = username
                db.close()
                return redirect('/home')
            except:
                db.close()

        db.close()

    return render_template("auth.html")

@app.route('/home')
def home():
    if 'user' not in session:
        return redirect('/')

    db = get_db()
    c = db.cursor()

    banner = c.execute("SELECT * FROM banners ORDER BY id DESC LIMIT 1").fetchone()
    vm = c.execute("SELECT * FROM vision_mission LIMIT 1").fetchone()
    stats = c.execute("SELECT * FROM statistics").fetchall()
    initiatives = c.execute("SELECT * FROM initiatives").fetchall()

    db.close()

    return render_template(
        "home.html",
        banner=banner,
        vm=vm,
        stats=stats,
        initiatives=initiatives
    )

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        db = get_db()
        c = db.cursor()

        admin = c.execute(
            "SELECT * FROM admin WHERE username=? AND password=?",
            (username, password)
        ).fetchone()

        db.close()

        if admin:
            session['admin'] = True
            return redirect('/admin/dashboard')

    return render_template("admin_login.html")

@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        return redirect('/admin')

    db = get_db()
    c = db.cursor()

    if request.method == 'POST':
        t = request.form.get('type')

        if t == 'banner':
            image = request.files['image']
            filename = image.filename
            image.save(os.path.join(UPLOAD_FOLDER, filename))
            c.execute(
                "INSERT INTO banners VALUES (NULL,?,?,?)",
                (filename, request.form['title'], request.form['description'])
            )

        elif t == 'vision':
            c.execute(
                "UPDATE vision_mission SET vision=?, mission=? WHERE id=1",
                (request.form['vision'], request.form['mission'])
            )

        elif t == 'stat':
            c.execute(
                "INSERT INTO statistics VALUES (NULL,?,?)",
                (request.form['label'], request.form['value'])
            )

        elif t == 'initiative':
            c.execute(
                "INSERT INTO initiatives VALUES (NULL,?,?)",
                (request.form['title'], request.form['description'])
            )

        db.commit()

    banners = c.execute("SELECT * FROM banners").fetchall()
    stats = c.execute("SELECT * FROM statistics").fetchall()
    initiatives = c.execute("SELECT * FROM initiatives").fetchall()
    vm = c.execute("SELECT * FROM vision_mission LIMIT 1").fetchone()

    db.close()

    return render_template(
        "admin_dashboard.html",
        banners=banners,
        stats=stats,
        initiatives=initiatives,
        vm=vm
    )

@app.route('/admin/banner/delete/<int:id>')
def delete_banner(id):
    if 'admin' not in session:
        return redirect('/admin')

    db = get_db()
    c = db.cursor()

    c.execute("DELETE FROM banners WHERE id=?", (id,))
    db.commit()
    db.close()

    return redirect('/admin/dashboard')

@app.route('/admin/banner/edit/<int:id>', methods=['GET', 'POST'])
def edit_banner(id):
    if 'admin' not in session:
        return redirect('/admin')

    db = get_db()
    c = db.cursor()

    if request.method == 'POST':
        c.execute(
            "UPDATE banners SET title=?, description=? WHERE id=?",
            (request.form['title'], request.form['description'], id)
        )
        db.commit()
        db.close()
        return redirect('/admin/dashboard')

    banner = c.execute("SELECT * FROM banners WHERE id=?", (id,)).fetchone()
    db.close()

    return render_template("edit_banner.html", banner=banner)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
