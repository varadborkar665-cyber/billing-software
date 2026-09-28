def create_bill(
    db,
    customer_id,
    total,
    paid,
    remaining,
    payment_status,
    bill_date
):
    cursor = db.execute(
        """
        INSERT INTO bills
        (
            customer_id,
            bill_date,
            total,
            paid,
            remaining,
            payment_status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            customer_id,
            bill_date,
            total,
            paid,
            remaining,
            payment_status
        )
    )

    db.commit()

    return cursor.lastrowid


def add_bill_item(
    db,
    bill_id,
    product_name,
    price,
    quantity,
    amount
):
    db.execute(
        """
        INSERT INTO bill_items
        (
            bill_id,
            product_name,
            price,
            quantity,
            amount
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            bill_id,
            product_name,
            price,
            quantity,
            amount
        )
    )

    db.commit()


def get_bill(db, bill_id):

    bill = db.execute(
        """
        SELECT
            bills.*,
            customers.name AS customer_name,
            customers.mobile,
            customers.address

        FROM bills

        JOIN customers
        ON customers.id = bills.customer_id

        WHERE bills.id = ?
        """,
        (bill_id,)
    ).fetchone()

    items = db.execute(
        """
        SELECT *
        FROM bill_items
        WHERE bill_id = ?
        ORDER BY id
        """,
        (bill_id,)
    ).fetchall()

    return bill, items


def get_all_bills(db):

    return db.execute(
        """
        SELECT
            bills.*,
            customers.name AS customer_name,
            customers.mobile

        FROM bills

        JOIN customers
        ON customers.id = bills.customer_id

        ORDER BY bills.id DESC
        """
    ).fetchall()


def get_pending_bills(db):

    return db.execute(
        """
        SELECT
            bills.*,
            customers.name AS customer_name,
            customers.mobile

        FROM bills

        JOIN customers
        ON customers.id = bills.customer_id

        WHERE bills.remaining > 0

        ORDER BY bills.id DESC
        """
    ).fetchall()