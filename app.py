import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mca11_sainthia_2026_key")

# Database Pathing
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

# --- USER FACING ROUTES ---

@app.route("/")
def home():
    db = get_db()
    update = db.execute("SELECT content FROM updates ORDER BY id DESC LIMIT 1").fetchone()
    return render_template("index.html", latest_update=update['content'] if update else "Welcome to MCA 11!")

@app.route("/batsmen")
def batsmen():
    try:
        db = get_db()
        players = db.execute("SELECT * FROM batsmen ORDER BY runs DESC").fetchall()
        return render_template("batsmen.html", players=players)
    except:
        return render_template("batsmen.html", players=[])

@app.route("/bowlers")
def bowlers():
    try:
        db = get_db()
        players = db.execute("SELECT * FROM bowlers ORDER BY wickets DESC").fetchall()
        return render_template("bowlers.html", players=players)
    except:
        return render_template("bowlers.html", players=[])

# --- ADMIN ROUTES ---

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        password = request.form.get("password")
        if password == os.environ.get("ADMIN_PASSWORD", "admin123"):
            session["admin_logged_in"] = True
            return redirect(url_for("dashboard"))
    return render_template("admin.html")

@app.route("/dashboard")
def dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    return render_template("dashboard.html")

@app.route("/update_stats", methods=["POST"])
def update_stats():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    
    file = request.files.get("file")
    table_type = request.form.get("table_type") # 'batsmen' or 'bowlers'
    
    if file and table_type in ['batsmen', 'bowlers']:
        df = pd.read_excel(file)
        # Ensure column names are lowercase to match HTML
        df.columns = [c.lower().replace(" ", "_") for c in df.columns]
        
        db = get_db()
        df.to_sql(table_type, db, if_exists='replace', index=False)
        db.commit()
    return redirect(url_for("dashboard"))

@app.route("/post_update", methods=["POST"])
def post_update():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin"))
    
    content = request.form.get("update_text")
    if content:
        db = get_db()
        db.execute("INSERT INTO updates (content) VALUES (?)", (content,))
        db.commit()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
