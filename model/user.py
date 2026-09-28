from werkzeug.security import generate_password_hash, check_password_hash


def create_user(db, username, password, role="admin"):
    password_hash = generate_password_hash(password)

    db.execute(
        """
        INSERT INTO users
        (username, password, role)
        VALUES (?, ?, ?)
        """,
        (
            username,
            password_hash,
            role
        )
    )

    db.commit()


def verify_user(db, username, password):

    user = db.execute(
        """
        SELECT *
        FROM users
        WHERE username = ?
        """,
        (username,)
    ).fetchone()

    if user:

        if check_password_hash(
            user["password"],
            password
        ):
            return user

    return None