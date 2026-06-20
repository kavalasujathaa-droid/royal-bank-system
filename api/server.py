import sys
import os
import sqlite3
import bcrypt

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

DB_PATH = "app/database/bank.db"
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def home():
    return jsonify({
        "status": "working",
        "message": "Royal Bank API Running"
    })

@app.route("/login", methods=["POST"])
def login():

    try:

        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        conn.close()

        if not user:
            return jsonify({
                "success": False,
                "message": "User Not Found"
            })

        if bcrypt.checkpw(
            password.encode(),
            user["password_hash"].encode()
        ):
            return jsonify({
                "success": True,
                "message": "Login Successful"
            })

        return jsonify({
            "success": False,
            "message": "Invalid Password"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        })

@app.route("/register", methods=["POST"])
def register():

    try:

        data = request.get_json()

        full_name = data.get("full_name")
        username = data.get("username")
        password = data.get("password")

        password_hash = bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO users
            (full_name, username, password_hash, pin)
            VALUES (?, ?, ?, ?)
            """,
            (
                full_name,
                username,
                password_hash,
                "1234"
            )
        )
        cursor.execute(
            "SELECT id FROM users WHERE username=?",
            (username,)
        )

        user = cursor.fetchone()

        import random

        account_number = (
            "ACC" +
            str(
                random.randint(
                    100000,
                    999999
                )
            )
        )

        cursor.execute(
            """
            INSERT INTO accounts
            (
                user_id,
                account_number,
                account_type,
                balance
            )
            VALUES
            (
                ?, ?, ?, ?
            )
            """,
            (
                user["id"],
                account_number,
                "Savings",
                0
            )
        )

        conn.commit()
        conn.close()

        return jsonify({
            "success": True,
            "message": "Registration Successful"
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "message": str(e)
        })
@app.route("/balance/<username>")
def balance(username):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT a.balance
        FROM accounts a
        JOIN users u
        ON a.user_id = u.id
        WHERE u.username = ?
    """, (username,))

    row = cursor.fetchone()

    conn.close()

    if row:
        return jsonify({
            "success": True,
            "balance": row["balance"]
        })

    return jsonify({
        "success": False
    })


@app.route("/account/<username>")
def account(username):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            a.account_number,
            a.account_type,
            a.balance
        FROM accounts a
        JOIN users u
        ON a.user_id = u.id
        WHERE u.username = ?
    """, (username,))

    row = cursor.fetchone()

    conn.close()

    if row:
        return jsonify({
            "success": True,
            "account_number": row["account_number"],
            "account_type": row["account_type"],
            "balance": row["balance"]
        })

    return jsonify({
        "success": False
    })



@app.route("/deposit", methods=["POST"])
def deposit():

    data = request.get_json()

    account_number = data["account_number"]
    amount = float(data["amount"])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE accounts
        SET balance = balance + ?
        WHERE account_number = ?
        """,
        (amount, account_number)
    )

    cursor.execute(
        """
        INSERT INTO transactions
        (
            account_number,
            transaction_type,
            amount
        )
        VALUES
        (
            ?,
            'DEPOSIT',
            ?
        )
        """,
        (account_number, amount)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Deposit Successful"
    })


@app.route("/withdraw", methods=["POST"])
def withdraw():

    data = request.get_json()

    account_number = data["account_number"]
    amount = float(data["amount"])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT balance
        FROM accounts
        WHERE account_number=?
        """,
        (account_number,)
    )

    row = cursor.fetchone()

    if not row:
        return jsonify({
            "success": False,
            "message": "Account Not Found"
        })

    if row["balance"] < amount:
        return jsonify({
            "success": False,
            "message": "Insufficient Balance"
        })
        
        

    cursor.execute(
        """
        UPDATE accounts
        SET balance = balance - ?
        WHERE account_number = ?
        """,
        (amount, account_number)
    )

    cursor.execute(
        """
        INSERT INTO transactions
        (
            account_number,
            transaction_type,
            amount
        )
        VALUES
        (
            ?,
            'WITHDRAW',
            ?
        )
        """,
        (account_number, amount)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Withdraw Successful"
    })

@app.route("/transfer", methods=["POST"])
def transfer():

    data = request.get_json()

    sender = data["sender"]
    receiver = data["receiver"]
    amount = float(data["amount"])

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT balance FROM accounts WHERE account_number=?",
        (sender,)
    )

    row = cursor.fetchone()

    if not row:
        return jsonify({
            "success": False,
            "message": "Sender Not Found"
        })

    if row["balance"] < amount:
        return jsonify({
            "success": False,
            "message": "Insufficient Balance"
        })

    cursor.execute(
        "SELECT balance FROM accounts WHERE account_number=?",
        (receiver,)
    )

    receiver_row = cursor.fetchone()

    if not receiver_row:
        return jsonify({
            "success": False,
            "message": "Receiver Not Found"
        })

    cursor.execute(
        """
        UPDATE accounts
        SET balance = balance - ?
        WHERE account_number = ?
        """,
        (amount, sender)
    )

    cursor.execute(
        """
        UPDATE accounts
        SET balance = balance + ?
        WHERE account_number = ?
        """,
        (amount, receiver)
    )

    cursor.execute(
        """
        INSERT INTO transactions
        (
            account_number,
            transaction_type,
            amount,
            receiver_account
        )
        VALUES
        (
            ?,
            'TRANSFER',
            ?,
            ?
        )
        """,
        (
            sender,
            amount,
            receiver
        )
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Transfer Successful"
    })

@app.route("/transactions/<account_number>")
def get_transactions(account_number):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE account_number = ?
        ORDER BY id DESC
        """,
        (account_number,)
    )

    rows = cursor.fetchall()

    conn.close()

    data = []

    for row in rows:

        data.append({
            "id": row["id"],
            "type": row["transaction_type"],
            "amount": row["amount"],
            "receiver": row["receiver_account"],
            "date": row["timestamp"]
        })

    return jsonify(data)
@app.route("/admin/stats")
def admin_stats():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM accounts")
    accounts = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM transactions")
    transactions = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "users": users,
        "accounts": accounts,
        "transactions": transactions
    })

@app.route(
    "/admin/delete-user/<username>",
    methods=["DELETE"]
)
def delete_user(username):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    if user:

        cursor.execute(
            "DELETE FROM accounts WHERE user_id=?",
            (user["id"],)
        )

        cursor.execute(
            "DELETE FROM users WHERE id=?",
            (user["id"],)
        )

        conn.commit()

    conn.close()

    return jsonify({
        "success": True
    })
@app.route("/change-password", methods=["POST"])
def change_password():

    data = request.get_json()

    username = data["username"]
    new_password = data["new_password"]

    password_hash = bcrypt.hashpw(
        new_password.encode(),
        bcrypt.gensalt()
    ).decode()

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE users
        SET password_hash = ?
        WHERE username = ?
        """,
        (password_hash, username)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Password Changed Successfully"
    })

@app.route("/delete-account", methods=["POST"])
def delete_account():

    data = request.get_json()

    username = data["username"]

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM users WHERE username=?",
        (username,)
    )

    user = cursor.fetchone()

    if not user:

        conn.close()

        return jsonify({
            "success": False,
            "message": "User Not Found"
        })

    user_id = user["id"]

    cursor.execute(
        "DELETE FROM accounts WHERE user_id=?",
        (user_id,)
    )

    cursor.execute(
        "DELETE FROM users WHERE id=?",
        (user_id,)
    )

    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Account Deleted Successfully"
    })
@app.route("/statement/<account_number>")
def statement(account_number):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT *
        FROM transactions
        WHERE account_number=?
        ORDER BY id DESC
        """,
        (account_number,)
    )

    rows = cursor.fetchall()

    conn.close()

    data = []

    for row in rows:

        data.append({
            "type": row["transaction_type"],
            "amount": row["amount"],
            "date": row["timestamp"]
        })

    return jsonify(data)
@app.route("/admin/users")
def admin_users():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
        id,
        username,
        full_name
        FROM users
    """)

    rows = cursor.fetchall()
    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])
@app.route("/admin/accounts")
def admin_accounts():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
        u.username,
        a.account_number,
        a.account_type,
        a.balance
        FROM accounts a
        JOIN users u
        ON a.user_id = u.id
    """)

    rows = cursor.fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])
@app.route("/admin/transactions")
def admin_transactions():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM transactions
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()

    conn.close()

    return jsonify([
        dict(row)
        for row in rows
    ])
@app.route(
    "/admin/login",
    methods=["POST"]
)
def admin_login():

    data = request.get_json()

    if (
        data["username"] == "admin123"
        and
        data["password"] == "rahul2008"
    ):

        return jsonify({
            "success": True
        })

    return jsonify({
        "success": False
    })   
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
    