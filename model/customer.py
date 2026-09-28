def add_customer(db, name, mobile, address):
    cursor = db.execute(
        """
        INSERT INTO customers
        (name, mobile, address, created_at)
        VALUES (?, ?, ?, datetime('now'))
        """,
        (name, mobile, address)
    )

    db.commit()

    return cursor.lastrowid


def get_customers(db):
    return db.execute(
        """
        SELECT *
        FROM customers
        ORDER BY id DESC
        """
    ).fetchall()


def get_customer(db, customer_id):
    return db.execute(
        """
        SELECT *
        FROM customers
        WHERE id = ?
        """,
        (customer_id,)
    ).fetchone()