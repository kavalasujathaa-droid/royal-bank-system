import bcrypt
import random

from app.database.db import get_connection


class AuthService:

    @staticmethod
    def hash_password(password):
        return bcrypt.hashpw(
            password.encode(),
            bcrypt.gensalt()
        ).decode()

    @staticmethod
    def verify_password(password, hashed):
        return bcrypt.checkpw(
            password.encode(),
            hashed.encode()
        )

    @staticmethod
    def generate_account_number():
        return f"ACC{random.randint(100000,999999)}"

    @staticmethod
    def register():

        print("\n=== CREATE ACCOUNT ===")

        full_name = input("Full Name: ")
        username = input("Username: ")
        password = input("Password: ")
        pin = input("4 Digit PIN: ")

        conn = get_connection()
        cursor = conn.cursor()

        try:

            password_hash = AuthService.hash_password(password)

            cursor.execute("""
            INSERT INTO users(
                full_name,
                username,
                password_hash,
                pin
            )
            VALUES (?,?,?,?)
            """, (
                full_name,
                username,
                password_hash,
                pin
            ))

            user_id = cursor.lastrowid

            account_number = AuthService.generate_account_number()

            cursor.execute("""
            INSERT INTO accounts(
                user_id,
                account_number,
                account_type,
                balance
            )
            VALUES (?,?,?,?)
            """, (
                user_id,
                account_number,
                "Savings",
                0
            ))

            conn.commit()

            print("\nAccount Created Successfully")
            print("Account Number:", account_number)

        except Exception as e:
            print("Error:", e)

        finally:
            conn.close()

    @staticmethod
    def login():

        username = input("Username: ")
        password = input("Password: ")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        SELECT
            users.*,
            accounts.account_number,
            accounts.balance,
            accounts.account_type
        FROM users
        JOIN accounts
        ON users.id = accounts.user_id
        WHERE users.username = ?
        """, (username,))

        user = cursor.fetchone()

        conn.close()

        if not user:
            print("User Not Found")
            return None

        if AuthService.verify_password(
            password,
            user["password_hash"]
        ):
            print("\nLogin Successful")
            print("Account Number:", user["account_number"])
            print("Account Type :", user["account_type"])

            return user

        print("Invalid Password")
        return None
    @staticmethod
    def change_pin(user_id):
        current_pin = input(
            "Current PIN: "
        )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT pin
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if user["pin"] != current_pin:
            print("Wrong PIN")
            conn.close()
            return

        new_pin = input(
            "New 4 Digit PIN: "
        )

        cursor.execute(
            """
            UPDATE users
            SET pin = ?
            WHERE id = ?
            """,
            (new_pin, user_id)
        )

        conn.commit()
        conn.close()

        print("PIN Updated Successfully")