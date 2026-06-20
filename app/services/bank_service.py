from app.database.db import get_connection
 
import bcrypt

class BankService:
    @staticmethod
    def deposit(account_number, amount):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE accounts SET balance = balance + ? WHERE account_number = ?",
            (amount, account_number)
        )


        cursor.execute(
            """
            INSERT INTO transactions
            (account_number, transaction_type, amount)
            VALUES (?, ?, ?)
            """,
            (account_number, "DEPOSIT", amount)
        )

        conn.commit()
        conn.close()

        print("Deposit Successful")

    @staticmethod
    def withdraw(account_number, amount):
        if amount <= 0:
            print("Invalid Amount")
            return

        pin = input("Enter PIN: ")

        cursor = get_connection().cursor()
        cursor.execute(
            """
            SELECT users.pin
            FROM users
            JOIN accounts
            ON users.id = accounts.user_id
            WHERE accounts.account_number = ?
            """,
            (account_number,)
        )

        pin_data = cursor.fetchone()

        if not pin_data or pin_data["pin"] != pin:
            print("Invalid PIN")
            return
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT balance FROM accounts WHERE account_number = ?",
            (account_number,)
        )

        account = cursor.fetchone()

        if not account:
            print("Account Not Found")
            conn.close()
            return
        if account["balance"] < amount:
            print("\nInsufficient Balance")
            print(f"Available Balance: ₹{account['balance']}")
            conn.close()
            return

       

        cursor.execute(
            "UPDATE accounts SET balance = balance - ? WHERE account_number = ?",
            (amount, account_number)
        )

        cursor.execute(
            """
            INSERT INTO transactions
            (account_number, transaction_type, amount)
            VALUES (?, ?, ?)
            """,
            (account_number, "WITHDRAW", amount)
        )

        conn.commit()
        conn.close()

        print("Withdraw Successful")

    @staticmethod
    def check_balance(account_number):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT balance FROM accounts WHERE account_number = ?",
            (account_number,)
        )

        account = cursor.fetchone()

        conn.close()

        if account:
            print("\n===== ACCOUNT BALANCE =====")
            print(f"Account : {account_number}")
            print(f"Balance : ₹{account['balance']}")
        else:
            print("Account Not Found")

    @staticmethod
    def transfer(sender_account, receiver_account, amount):
        if amount <= 0:
            print("Invalid Amount")
            return   
        pin = input("Enter PIN: ")

        temp_conn = get_connection()
        temp_cursor = temp_conn.cursor()

        temp_cursor.execute(
            """
            SELECT users.pin
            FROM users
            JOIN accounts
            ON users.id = accounts.user_id
            WHERE accounts.account_number = ?
            """,
            (sender_account,)
        )

        pin_data = temp_cursor.fetchone()

        temp_conn.close()

        if not pin_data or pin_data["pin"] != pin:
            print("Invalid PIN")
            return
        

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT balance FROM accounts WHERE account_number = ?",
            (sender_account,)
        )

        sender = cursor.fetchone()

        if not sender:
            print("Sender Not Found")
            conn.close()
            return

        if sender["balance"] < amount:
            print("Insufficient Balance")
            conn.close()
            return

        if sender_account == receiver_account:
            print("Cannot Transfer To Same Account")
            conn.close()
            return

        cursor.execute(
            "SELECT * FROM accounts WHERE account_number = ?",
            (receiver_account,)
        )

        receiver = cursor.fetchone()

        if not receiver:
            print("Receiver Not Found")
            conn.close()
            return

        cursor.execute(
            "UPDATE accounts SET balance = balance - ? WHERE account_number = ?",
            (amount, sender_account)
        )

        cursor.execute(
            "UPDATE accounts SET balance = balance + ? WHERE account_number = ?",
            (amount, receiver_account)
        )

        cursor.execute(
            """
            INSERT INTO transactions
            (account_number, transaction_type, amount)
            VALUES (?, ?, ?)
            """,
            (sender_account, "TRANSFER", amount)
        )

        conn.commit()
        conn.close()

        print("Transfer Successful")

    @staticmethod
    def transaction_history(account_number):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT transaction_type, amount, timestamp
            FROM transactions
            WHERE account_number = ?
            ORDER BY id DESC
            """,
            (account_number,)
        )

        rows = cursor.fetchall()

        conn.close()

        print("\n===== TRANSACTION HISTORY =====")

        if not rows:
            print("No Transactions Found")
            return

        for row in rows:

            print(
                f"{row['transaction_type']} | ₹{row['amount']} | {row['timestamp']}"
            )

    @staticmethod
    def account_details(account_number):

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM accounts
            WHERE account_number = ?
            """,
            (account_number,)
        )

        account = cursor.fetchone()

        conn.close()

        if account:

            print("\n===== ACCOUNT DETAILS =====")
            print(f"Account Number : {account['account_number']}")
            print(f"Balance        : ₹{account['balance']}")
            print(f"Type           : {account['account_type']}")

        else:
            print("Account Not Found")

    @staticmethod
    def change_password(user_id):
        old_password = input(
            "Current Password: "
        )

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT password_hash
            FROM users
            WHERE id = ?
            """,
            (user_id,)
        )

        user = cursor.fetchone()

        if not bcrypt.checkpw(
            old_password.encode(),
            user["password_hash"].encode()
        ):
            print("Wrong Password")
            conn.close()
            return

        new_password = input(
            "New Password: "
        )

        hashed = bcrypt.hashpw(
            new_password.encode(),
            bcrypt.gensalt()
        ).decode()

        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?
            WHERE id = ?
            """,
            (hashed, user_id)
        )

        conn.commit()
        conn.close()

        print("Password Updated Successfully")

    @staticmethod
    def change_pin(user_id):
        current_pin = input("Current PIN: ")

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT pin FROM users WHERE id = ?",
            (user_id,)
        )

        user = cursor.fetchone()

        if user["pin"] != current_pin:
            print("Wrong PIN")
            conn.close()
            return

        new_pin = input("New 4 Digit PIN: ")

        cursor.execute(
            "UPDATE users SET pin = ? WHERE id = ?",
            (new_pin, user_id)
        )

        conn.commit()
        conn.close()

        print("PIN Updated Successfully")

    @staticmethod
    def mini_statement(account_number):
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT transaction_type,amount,timestamp
            FROM transactions
            WHERE account_number=?
            ORDER BY id DESC
            LIMIT 5
            """,
            (account_number,)
        )

        rows = cursor.fetchall()

        conn.close()

        print("\n===== MINI STATEMENT =====")

        for row in rows:
            print(
                f"{row['transaction_type']} | ₹{row['amount']} | {row['timestamp']}"
            )
    @staticmethod
    def register_api(full_name, username, password):

        from app.database.db import get_connection
        import random

        conn = get_connection()
        cursor = conn.cursor()

        account_number = "ACC" + str(
            random.randint(100000, 999999)
        )

        cursor.execute(
            """
            INSERT INTO users(
                full_name,
                username,
                password
            )
            VALUES(?,?,?)
            """,
            (
                full_name,
                username,
                password
            )
        )

        user_id = cursor.lastrowid

        cursor.execute(
            """
            INSERT INTO accounts(
                user_id,
                account_number,
                account_type,
                balance
            )
            VALUES(?,?,?,?)
            """,
            (
                user_id,
                account_number,
                "Savings",
                0
            )
        )

        conn.commit()
        conn.close()