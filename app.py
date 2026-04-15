import os
import sqlite3
import pandas as pd
from flask import Flask, render_template, request, redirect, session, url_for

app = Flask(__name__)

# SECURITY: Uses Render's Environment Variable for sessions
app.secret_key = os.environ.get("SECRET_KEY", "mca11_sainthia_2026")

# PATHING: Ensures the app finds the DB regardless of Render's internal path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS batsmen (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, matches INTEGER, innings INTEGER, runs INTEGER, 
            average REAL, strike_rate REAL, high_score INTEGER
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bowlers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, matches INTEGER, innings INTEGER, 
            wickets INTEGER, economy REAL, best_figures TEXT
        )""")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT, date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit()
    conn.close()

init_db()

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row 
    return conn

# --- USER ROUTES ---

@app.route("/batsmen")
def batsmen():
    try:
        db = get_db()
        players = db.execute("SELECT * FROM batsmen ORDER BY runs DESC").fetchall()
        return render_template("batsmen.html", players=players)
    except Exception as e:
        # If the table doesn't exist yet, show an empty list instead of crashing
        print(f"Error fetching batsmen: {e}")
        return render_template("batsmen.html", players=[])

@app.route("/bowlers")
def bowlers():
    try:
        db = get_db()
        players = db.execute("SELECT * FROM bowlers ORDER BY wickets DESC").fetchall()
        return render_template("bowlers.html", players=players)
    except Exception as e:
        print(f"Error fetching bowlers: {e}")
        return render_template("bowlers.html", players=[])

# --- ADMIN ROUTES ---

@app.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        # Password check (Use Environment Variable on Render for better security)
        if request.form.get("password") == os.environ.get("ADMIN_PASSWORD", "admin123"):
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
    if not session.get("admin_logged_in"): return redirect(url_for("admin"))
    file = request.files.get("file")
    if file:
        df = pd.read_excel(file)
        db = get_db()
        # Logic to replace data (Adjust 'batsmen' or 'bowlers' based on file)
        table = request.form.get("table_type") 
        df.to_sql(table, db, if_exists='replace', index=False)
        db.commit()
    return redirect(url_for("dashboard"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
