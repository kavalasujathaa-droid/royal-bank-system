from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, os, hashlib
from datetime import datetime

app = Flask(__name__)
CORS(app)  # dashboard.html frontend CORS allow cheyyadam ki

DB = "bank.db"

# ── DB INIT ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_number TEXT UNIQUE NOT NULL,
        username TEXT NOT NULL,
        account_type TEXT DEFAULT "Savings",
        balance REAL DEFAULT 0.0,
        FOREIGN KEY(username) REFERENCES users(username)
    )''')

    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_number TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        description TEXT,
        date TEXT NOT NULL,
        FOREIGN KEY(account_number) REFERENCES accounts(account_number)
    )''')

    # Default user: sai (password: sai123)
    pwd_hash = hashlib.sha256("sai123".encode()).hexdigest()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("sai", pwd_hash))
        c.execute("INSERT INTO accounts (account_number, username, account_type, balance) VALUES (?, ?, ?, ?)",
                  ("RB-0001-SAI", "sai", "Premium Savings", 248500.00))
        # Seed transactions
        seed_tx = [
            ("RB-0001-SAI", "deposit",  85000, "Salary Credit — INFOSYS LTD",    "19 Jun 2026"),
            ("RB-0001-SAI", "withdraw",   840, "Zomato Food Delivery",            "19 Jun 2026"),
            ("RB-0001-SAI", "transfer", 12000, "Transfer to Rahul Sharma",        "18 Jun 2026"),
            ("RB-0001-SAI", "deposit",  25000, "Freelance Payment — Client A",    "17 Jun 2026"),
            ("RB-0001-SAI", "withdraw",  3499, "Amazon India Purchase",           "16 Jun 2026"),
            ("RB-0001-SAI", "transfer",  5500, "Transfer to Priya Nair",          "15 Jun 2026"),
            ("RB-0001-SAI", "deposit",   1842, "Interest Credit",                 "14 Jun 2026"),
            ("RB-0001-SAI", "withdraw",  1650, "BESCOM Electricity Bill",         "13 Jun 2026"),
            ("RB-0001-SAI", "withdraw",   649, "Netflix Subscription",            "12 Jun 2026"),
            ("RB-0001-SAI", "deposit",  10000, "Bonus Credit",                    "10 Jun 2026"),
        ]
        c.executemany(
            "INSERT INTO transactions (account_number, type, amount, description, date) VALUES (?,?,?,?,?)",
            seed_tx
        )
    except sqlite3.IntegrityError:
        pass  # Already seeded

    conn.commit()
    conn.close()


# ── HELPERS ──────────────────────────────────────────────────────────────────
def today():
    return datetime.now().strftime("%d %b %Y")

def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode()).hexdigest()


# ── ROUTES ───────────────────────────────────────────────────────────────────

@app.route("/account/<username>", methods=["GET"])
def get_account(username):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM accounts WHERE username = ?", (username,)
    ).fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Account not found"}), 404
    return jsonify({
        "account_number": row["account_number"],
        "account_type":   row["account_type"],
        "balance":        row["balance"]
    })


@app.route("/transactions/<account_number>", methods=["GET"])
def get_transactions(account_number):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE account_number = ? ORDER BY id DESC",
        (account_number,)
    ).fetchall()
    conn.close()
    return jsonify([
        {"type": r["type"], "amount": r["amount"], "description": r["description"], "date": r["date"]}
        for r in rows
    ])


@app.route("/deposit", methods=["POST"])
def deposit():
    data = request.json
    acc  = data.get("account_number")
    amt  = float(data.get("amount", 0))
    if not acc or amt <= 0:
        return jsonify({"error": "Invalid request"}), 400
    conn = get_db()
    conn.execute("UPDATE accounts SET balance = balance + ? WHERE account_number = ?", (amt, acc))
    conn.execute(
        "INSERT INTO transactions (account_number, type, amount, description, date) VALUES (?,?,?,?,?)",
        (acc, "deposit", amt, "Manual Deposit", today())
    )
    conn.commit()
    row = conn.execute("SELECT balance FROM accounts WHERE account_number = ?", (acc,)).fetchone()
    conn.close()
    return jsonify({"message": f"₹{amt:,.2f} deposited successfully", "balance": row["balance"]})


@app.route("/withdraw", methods=["POST"])
def withdraw():
    data = request.json
    acc  = data.get("account_number")
    amt  = float(data.get("amount", 0))
    if not acc or amt <= 0:
        return jsonify({"error": "Invalid request"}), 400
    conn = get_db()
    row = conn.execute("SELECT balance FROM accounts WHERE account_number = ?", (acc,)).fetchone()
    if not row or row["balance"] < amt:
        conn.close()
        return jsonify({"error": "Insufficient balance"}), 400
    conn.execute("UPDATE accounts SET balance = balance - ? WHERE account_number = ?", (amt, acc))
    conn.execute(
        "INSERT INTO transactions (account_number, type, amount, description, date) VALUES (?,?,?,?,?)",
        (acc, "withdraw", amt, "Manual Withdrawal", today())
    )
    conn.commit()
    updated = conn.execute("SELECT balance FROM accounts WHERE account_number = ?", (acc,)).fetchone()
    conn.close()
    return jsonify({"message": f"₹{amt:,.2f} withdrawn successfully", "balance": updated["balance"]})


@app.route("/transfer", methods=["POST"])
def transfer():
    data     = request.json
    sender   = data.get("sender")
    receiver = data.get("receiver")
    amt      = float(data.get("amount", 0))
    if not sender or not receiver or amt <= 0:
        return jsonify({"error": "Invalid request"}), 400
    conn = get_db()
    sender_row = conn.execute("SELECT balance FROM accounts WHERE account_number = ?", (sender,)).fetchone()
    if not sender_row or sender_row["balance"] < amt:
        conn.close()
        return jsonify({"error": "Insufficient balance"}), 400
    conn.execute("UPDATE accounts SET balance = balance - ? WHERE account_number = ?", (amt, sender))
    conn.execute(
        "INSERT INTO transactions (account_number, type, amount, description, date) VALUES (?,?,?,?,?)",
        (sender, "transfer", amt, f"Transfer to {receiver}", today())
    )
    # Receiver same bank lo unte balance add cheyyadam
    recv_row = conn.execute("SELECT * FROM accounts WHERE account_number = ?", (receiver,)).fetchone()
    if recv_row:
        conn.execute("UPDATE accounts SET balance = balance + ? WHERE account_number = ?", (amt, receiver))
        conn.execute(
            "INSERT INTO transactions (account_number, type, amount, description, date) VALUES (?,?,?,?,?)",
            (receiver, "deposit", amt, f"Transfer from {sender}", today())
        )
    conn.commit()
    updated = conn.execute("SELECT balance FROM accounts WHERE account_number = ?", (sender,)).fetchone()
    conn.close()
    return jsonify({"message": f"₹{amt:,.2f} sent to {receiver}", "balance": updated["balance"]})


@app.route("/change-password", methods=["POST"])
def change_password():
    data     = request.json
    username = data.get("username")
    new_pwd  = data.get("new_password", "")
    if not username or len(new_pwd) < 6:
        return jsonify({"error": "Password must be 6+ characters"}), 400
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "User not found"}), 404
    conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hash_pwd(new_pwd), username))
    conn.commit()
    conn.close()
    return jsonify({"message": "Password updated successfully"})


# ── RUN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    print("✦ Royal Bank Backend running at http://127.0.0.1:5000")
    print("✦ Default login → username: sai | password: sai123")
    app.run(debug=True, port=5000)
