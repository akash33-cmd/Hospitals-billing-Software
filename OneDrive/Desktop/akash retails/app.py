from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session
)
from functools import wraps
import sqlite3
import os
import secrets

app = Flask(__name__)

# Used to protect Flask sessions.
# For a permanent project, store this in an environment variable.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "change-this-secret-key-before-production"
)

DATABASE_NAME = "products.db"

# Default login details
ADMIN_USERNAME = "Akash"
ADMIN_PASSWORD = "Trent@456123"


# ---------------------------------------------------------
# DATABASE CONNECTION
# ---------------------------------------------------------

def get_db():
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------
# CREATE DATABASE TABLES
# ---------------------------------------------------------

def init_db():
    conn = get_db()

    # Products table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            barcode TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)

    # Sales table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bill_number TEXT UNIQUE NOT NULL,
            total REAL NOT NULL,
            payment_method TEXT NOT NULL,
            cash_received REAL DEFAULT 0,
            balance REAL DEFAULT 0,
            sale_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    count = conn.execute("""
        SELECT COUNT(*) AS total
        FROM products
    """).fetchone()["total"]

    if count == 0:
        products = [
            ("1001", "Rice", 60.00),
            ("1002", "Milk", 30.00),
            ("1003", "Sugar", 50.00),
            ("1004", "Wheat", 45.00),
            ("1005", "Oil", 120.00),
            ("1006", "Biscuits", 20.00),
            ("1007", "Tea", 90.00),
            ("1008", "Coffee", 150.00)
        ]

        conn.executemany("""
            INSERT INTO products (barcode, name, price)
            VALUES (?, ?, ?)
        """, products)

    conn.commit()
    conn.close()


# ---------------------------------------------------------
# LOGIN REQUIRED DECORATOR
# ---------------------------------------------------------

def login_required(view_function):

    @wraps(view_function)
    def protected_view(*args, **kwargs):

        if not session.get("logged_in"):
            return redirect(url_for("login"))

        return view_function(*args, **kwargs)

    return protected_view


# ---------------------------------------------------------
# CART FUNCTIONS
# ---------------------------------------------------------

def get_cart():
    return session.get("cart", [])


def save_cart(cart):
    session["cart"] = cart
    session.modified = True


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if session.get("logged_in"):
        return redirect(url_for("index"))

    message = ""

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        if (
            secrets.compare_digest(username, ADMIN_USERNAME)
            and secrets.compare_digest(password, ADMIN_PASSWORD)
        ):
            session.clear()

            session["logged_in"] = True
            session["username"] = username
            session["cart"] = []

            # Collections for the current login session
            session["cash_collected"] = 0.0
            session["upi_collected"] = 0.0
            session["bills_completed"] = 0

            return redirect(url_for("index"))

        message = "Invalid username or password."

    return render_template(
        "login.html",
        message=message
    )


# ---------------------------------------------------------
# HOME / BILLING PAGE
# ---------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    cart = get_cart()
    message = ""

    if request.method == "POST":

        barcode = request.form.get("barcode", "").strip()

        if barcode:

            conn = get_db()

            product = conn.execute("""
                SELECT *
                FROM products
                WHERE barcode = ?
            """, (barcode,)).fetchone()

            conn.close()

            if product:

                cart.append({
                    "barcode": product["barcode"],
                    "name": product["name"],
                    "price": float(product["price"])
                })

                save_cart(cart)

                message = f"{product['name']} added to cart."

            else:
                message = "Product not found."

        else:
            message = "Please enter a barcode."

    total = sum(item["price"] for item in cart)

    return render_template(
        "index.html",
        cart=cart,
        total=total,
        message=message,
        bill=None,
        username=session.get("username"),
        cash_collected=session.get("cash_collected", 0),
        upi_collected=session.get("upi_collected", 0),
        bills_completed=session.get("bills_completed", 0)
    )


# ---------------------------------------------------------
# PAYMENT
# ---------------------------------------------------------

@app.route("/payment", methods=["POST"])
@login_required
def payment():

    cart = get_cart()
    total = sum(item["price"] for item in cart)

    payment_method = request.form.get(
        "payment_method",
        ""
    ).strip().lower()

    if not cart:

        return render_template(
            "index.html",
            cart=[],
            total=0,
            message="Cart is empty.",
            bill=None,
            username=session.get("username"),
            cash_collected=session.get("cash_collected", 0),
            upi_collected=session.get("upi_collected", 0),
            bills_completed=session.get("bills_completed", 0)
        )

    if payment_method not in ["cash", "upi"]:

        return render_template(
            "index.html",
            cart=cart,
            total=total,
            message="Please select Cash or UPI.",
            bill=None,
            username=session.get("username"),
            cash_collected=session.get("cash_collected", 0),
            upi_collected=session.get("upi_collected", 0),
            bills_completed=session.get("bills_completed", 0)
        )

    cash_received = 0.0
    balance = 0.0

    # CASH PAYMENT
    if payment_method == "cash":

        cash_text = request.form.get("cash", "").strip()

        try:
            cash_received = float(cash_text)

            if cash_received < 0:
                raise ValueError

        except (ValueError, TypeError):

            return render_template(
                "index.html",
                cart=cart,
                total=total,
                message="Please enter a valid cash amount.",
                bill=None,
                username=session.get("username"),
                cash_collected=session.get("cash_collected", 0),
                upi_collected=session.get("upi_collected", 0),
                bills_completed=session.get("bills_completed", 0)
            )

        if cash_received < total:

            return render_template(
                "index.html",
                cart=cart,
                total=total,
                message="Insufficient cash.",
                bill=None,
                username=session.get("username"),
                cash_collected=session.get("cash_collected", 0),
                upi_collected=session.get("upi_collected", 0),
                bills_completed=session.get("bills_completed", 0)
            )

        balance = cash_received - total

        # Only sale total is counted as collected.
        # The customer's balance is not counted.
        session["cash_collected"] = round(
            session.get("cash_collected", 0) + total,
            2
        )

    # UPI PAYMENT
    elif payment_method == "upi":

        session["upi_collected"] = round(
            session.get("upi_collected", 0) + total,
            2
        )

    session["bills_completed"] = (
        session.get("bills_completed", 0) + 1
    )

    bill_number = "BILL-" + secrets.token_hex(4).upper()

    # Save sale in database
    conn = get_db()

    conn.execute("""
        INSERT INTO sales (
            bill_number,
            total,
            payment_method,
            cash_received,
            balance
        )
        VALUES (?, ?, ?, ?, ?)
    """, (
        bill_number,
        total,
        payment_method.upper(),
        cash_received,
        balance
    ))

    conn.commit()
    conn.close()

    bill = {
        "bill_number": bill_number,
        "items": cart.copy(),
        "total": total,
        "payment_method": payment_method.upper(),
        "cash_paid": cash_received,
        "balance": balance
    }

    # Clear cart after payment
    save_cart([])

    return render_template(
        "index.html",
        cart=[],
        total=0,
        message="Payment successful!",
        bill=bill,
        username=session.get("username"),
        cash_collected=session.get("cash_collected", 0),
        upi_collected=session.get("upi_collected", 0),
        bills_completed=session.get("bills_completed", 0)
    )


# ---------------------------------------------------------
# CLEAR CART
# ---------------------------------------------------------

@app.route("/clear")
@login_required
def clear_cart():

    save_cart([])

    return redirect(url_for("index"))


# ---------------------------------------------------------
# REMOVE ITEM
# ---------------------------------------------------------

@app.route("/remove/<int:item_index>")
@login_required
def remove_item(item_index):

    cart = get_cart()

    if 0 <= item_index < len(cart):
        cart.pop(item_index)
        save_cart(cart)

    return redirect(url_for("index"))


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout", methods=["POST"])
@login_required
def logout():

    username = session.get("username", "Admin")
    cash_collected = float(
        session.get("cash_collected", 0)
    )
    upi_collected = float(
        session.get("upi_collected", 0)
    )
    bills_completed = int(
        session.get("bills_completed", 0)
    )

    grand_total = cash_collected + upi_collected

    # Delete login and billing session
    session.clear()

    return render_template(
        "logout_summary.html",
        username=username,
        cash_collected=cash_collected,
        upi_collected=upi_collected,
        grand_total=grand_total,
        bills_completed=bills_completed
    )


# ---------------------------------------------------------
# START APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":

    init_db()

    print("-----------------------------------------")
    print("       RETAIL BILLING SYSTEM")
    print("-----------------------------------------")
    print("Username: admin")
    print("Password: 1234")
    print("Database: products.db")
    print("Server: http://127.0.0.1:5000")
    print("-----------------------------------------")

    app.run(debug=True)