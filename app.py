import os
from datetime import datetime
from functools import wraps
from urllib.parse import quote

import mysql.connector
from mysql.connector import Error

from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

import config


# =========================================================
# FLASK APP
# =========================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "templates"),
    static_folder=os.path.join(BASE_DIR, "static")
)

app.secret_key = config.SECRET_KEY


# =========================================================
# MYSQL CONNECTION
# =========================================================

def get_db():

    return mysql.connector.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        connection_timeout=15
    )


# =========================================================
# DATABASE HELPERS
# =========================================================

def fetch_one(db, sql, params=()):

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        sql,
        params
    )

    row = cursor.fetchone()

    cursor.close()

    return row


def fetch_all(db, sql, params=()):

    cursor = db.cursor(dictionary=True)

    cursor.execute(
        sql,
        params
    )

    rows = cursor.fetchall()

    cursor.close()

    return rows


def execute_db(db, sql, params=()):

    cursor = db.cursor()

    cursor.execute(
        sql,
        params
    )

    last_id = cursor.lastrowid

    cursor.close()

    return last_id


# =========================================================
# LOGIN REQUIRED
# =========================================================

def login_required(function):

    @wraps(function)
    def wrapper(*args, **kwargs):

        if "user_id" not in session:

            return redirect(
                url_for("login")
            )

        return function(
            *args,
            **kwargs
        )

    return wrapper


# =========================================================
# LOGIN
# =========================================================

@app.route(
    "/",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        if not username or not password:

            flash(
                "Please enter username and password.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        db = None

        try:

            db = get_db()

            user = fetch_one(
                db,
                """
                SELECT *
                FROM users
                WHERE username = %s
                """,
                (username,)
            )

            if user:

                if check_password_hash(
                    user["password"],
                    password
                ):

                    session.clear()

                    session["user_id"] = user["id"]

                    session["username"] = user["username"]

                    return redirect(
                        url_for("dashboard")
                    )

            flash(
                "Invalid username or password.",
                "error"
            )

        except Error as e:

            flash(
                "Database error: " + str(e),
                "error"
            )

        finally:

            if db and db.is_connected():

                db.close()

    return render_template(
        "login.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        username = request.form.get(
            "username",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )

        if len(username) < 3:

            flash(
                "Username must contain at least 3 characters.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if len(password) < 6:

            flash(
                "Password must contain at least 6 characters.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        if password != confirm_password:

            flash(
                "Passwords do not match.",
                "error"
            )

            return redirect(
                url_for("register")
            )

        db = None

        try:

            db = get_db()

            existing = fetch_one(
                db,
                """
                SELECT id
                FROM users
                WHERE username = %s
                """,
                (username,)
            )

            if existing:

                flash(
                    "Username already exists.",
                    "error"
                )

                return redirect(
                    url_for("register")
                )

            password_hash = generate_password_hash(
                password
            )

            execute_db(
                db,
                """
                INSERT INTO users
                (
                    username,
                    password,
                    created_at
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    username,
                    password_hash,
                    datetime.now()
                )
            )

            db.commit()

            flash(
                "Account created successfully. Please login.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Error as e:

            if db:

                db.rollback()

            flash(
                "Database error: " + str(e),
                "error"
            )

        finally:

            if db and db.is_connected():

                db.close()

    return render_template(
        "register.html"
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        url_for("login")
    )


# =========================================================
# DASHBOARD
# =========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    user_id = session["user_id"]

    db = get_db()

    try:

        customer_count = fetch_one(
            db,
            """
            SELECT COUNT(*) AS total
            FROM customers
            WHERE user_id = %s
            """,
            (user_id,)
        )["total"]

        product_count = fetch_one(
            db,
            """
            SELECT COUNT(*) AS total
            FROM products
            WHERE user_id = %s
            """,
            (user_id,)
        )["total"]

        bill_count = fetch_one(
            db,
            """
            SELECT COUNT(*) AS total
            FROM bills
            WHERE user_id = %s
            """,
            (user_id,)
        )["total"]

        today = datetime.now().strftime(
            "%Y-%m-%d"
        )

        today_sales = fetch_one(
            db,
            """
            SELECT COALESCE(
                SUM(paid),
                0
            ) AS total

            FROM bills

            WHERE user_id = %s
            AND bill_date = %s
            """,
            (
                user_id,
                today
            )
        )["total"]

        pending_amount = fetch_one(
            db,
            """
            SELECT COALESCE(
                SUM(remaining),
                0
            ) AS total

            FROM bills

            WHERE user_id = %s
            AND remaining > 0
            """,
            (user_id,)
        )["total"]

        return render_template(
            "dashboard.html",

            customer_count=customer_count,

            product_count=product_count,

            bill_count=bill_count,

            today_sales=today_sales,

            pending=pending_amount
        )

    finally:

        db.close()


# =========================================================
# CUSTOMERS
# =========================================================

@app.route("/customers")
@login_required
def customers():

    user_id = session["user_id"]

    db = get_db()

    try:

        rows = fetch_all(
            db,
            """
            SELECT *
            FROM customers
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,)
        )

        return render_template(
            "customers.html",
            customers=rows
        )

    finally:

        db.close()


# =========================================================
# ADD CUSTOMER
# =========================================================

@app.route(
    "/customers/add",
    methods=["GET", "POST"]
)
@login_required
def add_customer():

    if request.method == "POST":

        user_id = session["user_id"]

        name = request.form.get(
            "name",
            ""
        ).strip()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        if not name:

            flash(
                "Customer name is required.",
                "error"
            )

            return redirect(
                url_for("add_customer")
            )

        if not mobile.isdigit() or len(mobile) != 10:

            flash(
                "Enter a valid 10 digit mobile number.",
                "error"
            )

            return redirect(
                url_for("add_customer")
            )

        db = get_db()

        try:

            execute_db(
                db,
                """
                INSERT INTO customers
                (
                    name,
                    mobile,
                    address,
                    created_at,
                    user_id
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    name,
                    mobile,
                    address,
                    datetime.now(),
                    user_id
                )
            )

            db.commit()

            flash(
                "Customer added successfully.",
                "success"
            )

        except Error as e:

            db.rollback()

            flash(
                "Database error: " + str(e),
                "error"
            )

        finally:

            db.close()

        return redirect(
            url_for("customers")
        )

    return render_template(
        "add_customer.html"
    )


# =========================================================
# PRODUCTS
# =========================================================

@app.route("/products")
@login_required
def products():

    user_id = session["user_id"]

    db = get_db()

    try:

        rows = fetch_all(
            db,
            """
            SELECT *
            FROM products
            WHERE user_id = %s
            ORDER BY id DESC
            """,
            (user_id,)
        )

        return render_template(
            "products.html",
            products=rows
        )

    finally:

        db.close()


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route(
    "/products/add",
    methods=["POST"]
)
@login_required
def add_product():

    user_id = session["user_id"]

    name = request.form.get(
        "name",
        ""
    ).strip()

    price_text = request.form.get(
        "price",
        "0"
    )

    try:

        price = float(
            price_text
        )

    except ValueError:

        flash(
            "Invalid product price.",
            "error"
        )

        return redirect(
            url_for("products")
        )

    if not name:

        flash(
            "Product name is required.",
            "error"
        )

        return redirect(
            url_for("products")
        )

    if price < 0:

        flash(
            "Price cannot be negative.",
            "error"
        )

        return redirect(
            url_for("products")
        )

    db = get_db()

    try:

        execute_db(
            db,
            """
            INSERT INTO products
            (
                name,
                price,
                created_at,
                user_id
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                name,
                price,
                datetime.now(),
                user_id
            )
        )

        db.commit()

        flash(
            "Product added successfully.",
            "success"
        )

    except Error as e:

        db.rollback()

        flash(
            "Database error: " + str(e),
            "error"
        )

    finally:

        db.close()

    return redirect(
        url_for("products")
    )


# =========================================================
# DELETE PRODUCT
# =========================================================

@app.route(
    "/products/delete/<int:product_id>",
    methods=["POST"]
)
@login_required
def delete_product(product_id):

    user_id = session["user_id"]

    db = get_db()

    try:

        cursor = db.cursor()

        cursor.execute(
            """
            DELETE FROM products

            WHERE id = %s
            AND user_id = %s
            """,
            (
                product_id,
                user_id
            )
        )

        db.commit()

        cursor.close()

        flash(
            "Product deleted.",
            "success"
        )

    except Error as e:

        db.rollback()

        flash(
            "Database error: " + str(e),
            "error"
        )

    finally:

        db.close()

    return redirect(
        url_for("products")
    )


# =========================================================
# CREATE BILL
# =========================================================

@app.route(
    "/create-bill",
    methods=["GET", "POST"]
)
@login_required
def create_bill():

    user_id = session["user_id"]

    db = get_db()

    if request.method == "POST":

        try:

            customer_id = int(
                request.form.get(
                    "customer_id",
                    "0"
                )
            )

        except ValueError:

            db.close()

            flash(
                "Please select a customer.",
                "error"
            )

            return redirect(
                url_for("create_bill")
            )

        customer = fetch_one(
            db,
            """
            SELECT *
            FROM customers

            WHERE id = %s
            AND user_id = %s
            """,
            (
                customer_id,
                user_id
            )
        )

        if customer is None:

            db.close()

            flash(
                "Please select a valid customer.",
                "error"
            )

            return redirect(
                url_for("create_bill")
            )

        product_ids = request.form.getlist(
            "product_id[]"
        )

        product_names = request.form.getlist(
            "product_name[]"
        )

        prices = request.form.getlist(
            "price[]"
        )

        quantities = request.form.getlist(
            "quantity[]"
        )

        bill_items = []

        total = 0.0

        for i in range(
            len(product_names)
        ):

            name = product_names[i].strip()

            if not name:

                continue

            try:

                price = float(
                    prices[i]
                )

                quantity = int(
                    quantities[i]
                )

            except (
                ValueError,
                IndexError
            ):

                continue

            if price < 0:

                continue

            if quantity <= 0:

                continue

            product_id = None

            if i < len(product_ids):

                try:

                    product_id = int(
                        product_ids[i]
                    )

                except ValueError:

                    product_id = None

            amount = price * quantity

            total += amount

            bill_items.append(
                (
                    product_id,
                    name,
                    price,
                    quantity,
                    amount
                )
            )

        if not bill_items:

            db.close()

            flash(
                "Please add at least one product.",
                "error"
            )

            return redirect(
                url_for("create_bill")
            )

        try:

            paid = float(
                request.form.get(
                    "paid",
                    "0"
                )
            )

        except ValueError:

            paid = 0.0

        if paid < 0:

            paid = 0.0

        if paid > total:

            paid = total

        remaining = total - paid

        if remaining <= 0:

            remaining = 0.0

            payment_status = "PAID"

        else:

            payment_status = "PENDING"

        bill_date = datetime.now().strftime(
            "%Y-%m-%d"
        )

        try:

            bill_id = execute_db(
                db,
                """
                INSERT INTO bills
                (
                    customer_id,
                    bill_date,
                    total,
                    paid,
                    remaining,
                    payment_status,
                    user_id
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    customer_id,
                    bill_date,
                    total,
                    paid,
                    remaining,
                    payment_status,
                    user_id
                )
            )

            for item in bill_items:

                execute_db(
                    db,
                    """
                    INSERT INTO bill_items
                    (
                        bill_id,
                        product_name,
                        price,
                        quantity,
                        amount,
                        user_id,
                        product_id
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        bill_id,
                        item[1],
                        item[2],
                        item[3],
                        item[4],
                        user_id,
                        item[0]
                    )
                )

            db.commit()

            db.close()

            return redirect(
                url_for(
                    "view_bill",
                    bill_id=bill_id
                )
            )

        except Error as e:

            db.rollback()

            db.close()

            flash(
                "Database error: " + str(e),
                "error"
            )

            return redirect(
                url_for("create_bill")
            )

    customers_list = fetch_all(
        db,
        """
        SELECT *
        FROM customers

        WHERE user_id = %s

        ORDER BY name
        """,
        (user_id,)
    )

    products_list = fetch_all(
        db,
        """
        SELECT *
        FROM products

        WHERE user_id = %s

        ORDER BY name
        """,
        (user_id,)
    )

    db.close()

    return render_template(
        "create_bill.html",
        customers=customers_list,
        products=products_list
    )


# =========================================================
# ALL BILLS
# =========================================================

@app.route("/bills")
@login_required
def bills():

    user_id = session["user_id"]

    db = get_db()

    try:

        rows = fetch_all(
            db,
            """
            SELECT
                bills.*,
                customers.name AS customer_name,
                customers.mobile AS mobile

            FROM bills

            JOIN customers
            ON customers.id = bills.customer_id

            WHERE bills.user_id = %s
            AND customers.user_id = %s

            ORDER BY bills.id DESC
            """,
            (
                user_id,
                user_id
            )
        )

        return render_template(
            "bills.html",
            bills=rows
        )

    finally:

        db.close()


# =========================================================
# VIEW BILL
# =========================================================

@app.route(
    "/bill/<int:bill_id>"
)
@login_required
def view_bill(bill_id):

    user_id = session["user_id"]

    db = get_db()

    bill = fetch_one(
        db,
        """
        SELECT
            bills.*,
            customers.name AS customer_name,
            customers.mobile AS mobile,
            customers.address AS address

        FROM bills

        JOIN customers
        ON customers.id = bills.customer_id

        WHERE bills.id = %s
        AND bills.user_id = %s
        AND customers.user_id = %s
        """,
        (
            bill_id,
            user_id,
            user_id
        )
    )

    if bill is None:

        db.close()

        flash(
            "Bill not found.",
            "error"
        )

        return redirect(
            url_for("bills")
        )

    items = fetch_all(
        db,
        """
        SELECT *
        FROM bill_items

        WHERE bill_id = %s
        AND user_id = %s

        ORDER BY id
        """,
        (
            bill_id,
            user_id
        )
    )

    db.close()

    whatsapp_message = (
        f"Hello {bill['customer_name']},\n\n"
        f"Your bill #{bill['id']}\n"
        f"Total: ₹{float(bill['total']):.2f}\n"
        f"Paid: ₹{float(bill['paid']):.2f}\n"
        f"Remaining: ₹{float(bill['remaining']):.2f}\n\n"
        f"Thank you."
    )

    whatsapp_url = (
        "https://wa.me/"
        + str(bill["mobile"])
        + "?text="
        + quote(whatsapp_message)
    )

    return render_template(
        "bill.html",
        bill=bill,
        items=items,
        whatsapp_url=whatsapp_url
    )


# =========================================================
# PENDING PAYMENTS
# =========================================================

@app.route("/pending")
@login_required
def pending():

    user_id = session["user_id"]

    db = get_db()

    try:

        pending_bills = fetch_all(
            db,
            """
            SELECT
                bills.*,
                customers.name AS customer_name,
                customers.mobile AS mobile

            FROM bills

            JOIN customers
            ON customers.id = bills.customer_id

            WHERE bills.user_id = %s
            AND customers.user_id = %s
            AND bills.remaining > 0

            ORDER BY bills.id DESC
            """,
            (
                user_id,
                user_id
            )
        )

        total_pending = fetch_one(
            db,
            """
            SELECT COALESCE(
                SUM(remaining),
                0
            ) AS total

            FROM bills

            WHERE user_id = %s
            AND remaining > 0
            """,
            (user_id,)
        )["total"]

        return render_template(
            "pending.html",
            bills=pending_bills,
            total_pending=total_pending
        )

    finally:

        db.close()


# =========================================================
# MARK AS PAID
# =========================================================

@app.route(
    "/bill/<int:bill_id>/paid",
    methods=["POST"]
)
@login_required
def mark_paid(bill_id):

    user_id = session["user_id"]

    db = get_db()

    try:

        bill = fetch_one(
            db,
            """
            SELECT *
            FROM bills

            WHERE id = %s
            AND user_id = %s
            """,
            (
                bill_id,
                user_id
            )
        )

        if bill is None:

            flash(
                "Bill not found.",
                "error"
            )

            return redirect(
                url_for("bills")
            )

        if float(
            bill["remaining"]
        ) <= 0:

            flash(
                "This bill is already fully paid.",
                "success"
            )

            return redirect(
                url_for("bills")
            )

        execute_db(
            db,
            """
            UPDATE bills

            SET
                paid = total,
                remaining = 0,
                payment_status = 'PAID'

            WHERE id = %s
            AND user_id = %s
            """,
            (
                bill_id,
                user_id
            )
        )

        db.commit()

        flash(
            f"Bill #{bill_id} payment completed successfully.",
            "success"
        )

    except Error as e:

        db.rollback()

        flash(
            "Database error: " + str(e),
            "error"
        )

    finally:

        db.close()

    return redirect(
        url_for("bills")
    )


# =========================================================
# TEST DATABASE
# =========================================================

@app.route("/test-db")
def test_db():

    db = None

    try:

        db = get_db()

        result = fetch_one(
            db,
            "SELECT 1 AS test"
        )

        if result:

            return """
            <h2>Database Connected Successfully ✅</h2>
            <p>MySQL connection is working.</p>
            """

    except Error as e:

        return f"""
        <h2>Database Connection Failed ❌</h2>
        <p>{e}</p>
        """

    finally:

        if db and db.is_connected():

            db.close()

    return "Database test failed."


# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    print("=" * 60)

    print(
        "SMART BILLING SOFTWARE"
    )

    print(
        "MYSQL VERSION"
    )

    print("=" * 60)

    print(
        "Database:",
        config.DB_NAME
    )

    print(
        "Server: http://127.0.0.1:5000"
    )

    print("=" * 60)

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )