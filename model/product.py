def add_product(db, name, price):
    cursor = db.execute(
        """
        INSERT INTO products
        (name, price, created_at)
        VALUES (?, ?, datetime('now'))
        """,
        (name, price)
    )

    db.commit()

    return cursor.lastrowid


def get_products(db):
    return db.execute(
        """
        SELECT *
        FROM products
        ORDER BY id DESC
        """
    ).fetchall()


def get_product(db, product_id):
    return db.execute(
        """
        SELECT *
        FROM products
        WHERE id = ?
        """,
        (product_id,)
    ).fetchone()