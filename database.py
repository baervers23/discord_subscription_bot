import sqlite3
from datetime import datetime, timedelta
import json
import os

DB_FILE = "subscriptions.db"
CODES_FILE = "codes.json"

def get_connection():
    return sqlite3.connect("subscriptions.db")  # Pfad zu deiner Datenbankdatei

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS subscriptions (
            user_id INTEGER PRIMARY KEY,
            end_date TEXT,
            trial_used INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_subscription(user_id, months, trial=None):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT end_date, trial_used FROM subscriptions WHERE user_id = ?", (user_id,))
    row = c.fetchone()

    if row:
        old_end_date_str, old_trial_used = row
        old_end_date = datetime.fromisoformat(old_end_date_str)
        if old_end_date < datetime.now():
            new_end_date = datetime.now() + timedelta(days=30*months)
        else:
            new_end_date = old_end_date + timedelta(days=30*months)

        new_trial = old_trial_used if trial is None else trial

        c.execute(
            "UPDATE subscriptions SET end_date = ?, trial_used = ? WHERE user_id = ?",
            (new_end_date.isoformat(), new_trial, user_id)
        )
    else:
        new_end_date = datetime.now() + timedelta(days=30*months)
        new_trial = 0 if trial is None else trial
        c.execute(
            "INSERT INTO subscriptions (user_id, end_date, trial_used) VALUES (?, ?, ?)",
            (user_id, new_end_date.isoformat(), new_trial)
        )

    conn.commit()
    conn.close()
    return new_end_date

def get_subscription(user_id):
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT end_date FROM subscriptions WHERE user_id=?", (user_id,))
        row = c.fetchone()
        return datetime.fromisoformat(row[0]) if row else None

def use_trial(user_id):
    now = datetime.utcnow()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM subscriptions WHERE user_id=?", (user_id,))
        row = c.fetchone()
        if row and row[2]:
            return False
        end_date = now + timedelta(days=30)
        if row:
            c.execute("UPDATE subscriptions SET end_date=?, trial_used=1 WHERE user_id=?", (end_date.isoformat(), user_id, 1))
        else:
            c.execute("INSERT INTO subscriptions VALUES (?, ?, ?)", (user_id, end_date.isoformat(), 1))
        conn.commit()
        return True

def redeem_code(user_id, code):
    try:
        with open(CODES_FILE, "r+") as f:
            data = json.load(f)
            if code not in data:
                return "Ungültiger Code."
            if data[code]["used"]:
                return "Dieser Code wurde bereits verwendet."
            months = data[code]["months"]
            data[code]["used"] = True
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
            return add_subscription(user_id, months)
    except:
        return "Fehler beim Einlösen."

def load_codes():
    if not os.path.exists(CODES_FILE):
        return {}
    with open(CODES_FILE, "r") as f:
        return json.load(f)

def save_codes(codes):
    with open(CODES_FILE, "w") as f:
        json.dump(codes, f, indent=4)

def add_code_to_file(code: str, months: int) -> bool:
    codes = load_codes()
    if code in codes:
        return False  # Code existiert bereits

    codes[code] = {
        "months": months,
        "used": False
    }

    save_codes(codes)
    return True

def get_all_subscriptions():
    conn = get_connection()
    c = conn.cursor()
    now_iso = datetime.now().isoformat()
    c.execute("SELECT user_id, end_date FROM subscriptions WHERE end_date > ?", (now_iso,))
    result = c.fetchall()
    conn.close()
    return result

def check_expirations():
    now = datetime.utcnow()
    with sqlite3.connect(DB_FILE) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, end_date FROM subscriptions")
        result = []
        for user_id, end_date in c.fetchall():
            end = datetime.fromisoformat(end_date)
            days_left = (end - now).days
            result.append((user_id, end, days_left))
        return result
    
def delete_subscription(user_id):
    
    # Hole DB-Verbindung & prüfe auf aktives Abo
    sub = get_subscription(user_id)
    if sub is None:
        return "❌ Der Benutzer hat kein aktives Abo."

    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM subscriptions WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

    return "✅ Abo des gewünschten Benutzers gekündigt."
