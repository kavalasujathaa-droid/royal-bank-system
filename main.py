from app.database.db import initialize_database
from app.services.auth_service import AuthService
from app.services.bank_service import BankService
import sqlite3
from app.services.bank_service import BankService
import csv


def dashboard(user):
    while True:
        print("\n===== DASHBOARD =====")
        print("1. Deposit")
        print("2. Withdraw")
        print("3. Transfer")
        print("4. Balance")
        print("5. Transaction History")
        print("6. Account Details")
        print("7. Change Username")
        print("8. Change Password")
        print("9.Change PIN")
        print("10.Mini Statement")
        print("11. Logout")

        choice = input("Choice: ")

        account_number = user["account_number"]

        if choice == "1":

            amount = float(input("Amount: "))
            BankService.deposit(account_number, amount)

        elif choice == "2":

            amount = float(input("Amount: "))
            BankService.withdraw(account_number, amount)

        elif choice == "3":

            receiver = input("Receiver Account Number: ")
            amount = float(input("Amount: "))

            BankService.transfer(
                account_number,
                receiver,
                amount
            )

        elif choice == "4":

            BankService.check_balance(
                account_number
            )

        elif choice == "5":

            BankService.transaction_history(
                account_number
            )

        elif choice == "6":

            BankService.account_details(
                account_number
            )

        elif choice == "7":
            AuthService.change_username(
                user["id"]
            )

        elif choice == "8":
            AuthService.change_password(
                user["id"]
            )
        elif choice == "9":
            AuthService.change_pin(
                user["id"]
            )
        elif choice == "10":
            BankService.mini_statement(
                account_number
            )
        elif choice == "11":
            break
        else:
            print("Invalid Choice")
def admin_panel():
    conn = sqlite3.connect("app/database/bank.db")
    cursor = conn.cursor()

    while True:

        print("\n===== ADMIN PANEL =====")
        print("1. View Accounts")
        print("2. View Users")
        print("3. Exit")
        print("4. Total Bank Balance")
        print("5.View All Transactions")
        print("6.Search Accounnt")
        print("7.Export Transactions")
        
        

        choice = input("Choice: ")

        if choice == "1":
            cursor.execute(
                "SELECT account_number,balance FROM accounts"
            )
            rows = cursor.fetchall()


            print("\nAccounts")

            for row in rows:
                print(row)

        elif choice == "2":

            cursor.execute(
                "SELECT id,full_name,username FROM users"
            )

            rows = cursor.fetchall()

            print("\nUsers")

            for row in rows:
                print(row)

        elif choice == "3":
            break
        elif choice == "4":
            cursor.execute(
                "SELECT SUM(balance) FROM accounts"
            )
            total = cursor.fetchone()[0]
            print(f"\nTotal Bank Money: ₹{total}")
        elif choice == "5":

            cursor.execute(
                """
                SELECT *
                FROM transactions
                ORDER BY id DESC
                """
            )

            rows = cursor.fetchall()

            print("\n===== ALL TRANSACTIONS =====")

            for row in rows:
                print(row)
        elif choice == "6":

            account = input(
                "Account Number: "
            )

            cursor.execute(
                """
                SELECT *
                FROM accounts
                WHERE account_number = ?
                """,
                (account,)
            )

            row = cursor.fetchone()

            if row:
                print(row)
            else:
                print("Account Not Found")
        elif choice == "7":

            with open(
                "transactions.csv",
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow(
                    [
                        "ID",
                        "ACCOUNT",
                        "TYPE",
                        "AMOUNT",
                        "RECEIVER",
                        "TIMESTAMP"
                    ]
                )

                cursor.execute(
                    """
                    SELECT *
                    FROM transactions
                    ORDER BY id DESC
                    """
                )

                rows = cursor.fetchall()

                for row in rows:
                    writer.writerow(row)

            print(
                "\nTransactions Exported Successfully"
            )
        else:
            print("Invalid Choice")
            

    conn.close()


def admin_login():
    password = input("Admin Password: ")

    if password == "admin123":
        admin_panel()

    else:
        print("Wrong Password")




def menu():
    while True:

        print("\n===== BANKING SYSTEM =====")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        print("4. Admin")

        choice = input("Choice: ")

        if choice == "1":

            AuthService.register()

        elif choice == "2":
            attempts = 3

            while attempts > 0:

                user = AuthService.login()

                if user:
                    dashboard(user)
                    break

                attempts -= 1

                if attempts > 0:
                    print(f"\nWrong Credentials. Attempts Left: {attempts}")

            if attempts == 0:
                print("\nAccount Locked For This Session")

        elif choice == "3":
            break

        elif choice == "4":
            admin_login()

        else:
            print("Invalid Choice")
            


if __name__ == "__main__":
    initialize_database()
    menu()
