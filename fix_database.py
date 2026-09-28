import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE = os.path.join(
    BASE_DIR,
    "database",
    "billing.db"
)

print("=" * 50)
print("DATABASE FIX")
print("=" * 50)
print("Database:", DATABASE)

if not os.path.exists(DATABASE):
    print("❌ billing.db not found!")
    input("Press Enter to exit...")
    exit()

db = sqlite3.connect(
    DATABASE,
    timeout=30
)

try:

    # Check bill_items table
    table = db.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type='table'
        AND name='bill_items'
    """).fetchone()

    if table is None:

        print("❌ bill_items table does not exist.")

        db.execute("""
            CREATE TABLE bill_items (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                user_id INTEGER NOT NULL,

                bill_id INTEGER NOT NULL,

                product_id INTEGER,

                product_name TEXT NOT NULL,

                price REAL NOT NULL,

                quantity INTEGER NOT NULL,

                amount REAL NOT NULL

            )
        """)

        db.commit()

        print("✅ bill_items table created.")

    else:

        # Get columns
        columns = db.execute(
            "PRAGMA table_info(bill_items)"
        ).fetchall()

        column_names = [
            column[1]
            for column in columns
        ]

        print("\nCurrent columns:")
        for name in column_names:
            print(" -", name)

        # Add missing columns
        if "product_id" not in column_names:

            print("\nAdding product_id...")

            db.execute("""
                ALTER TABLE bill_items
                ADD COLUMN product_id INTEGER
            """)

            db.commit()

            print("✅ product_id added.")

        else:

            print("\n✅ product_id already exists.")

    # Final check
    columns = db.execute(
        "PRAGMA table_info(bill_items)"
    ).fetchall()

    print("\nFinal bill_items columns:")

    for column in columns:
        print(
            f" - {column[1]} "
            f"({column[2]})"
        )

    db.commit()

except Exception as e:

    db.rollback()

    print("\n❌ ERROR:")
    print(e)

finally:

    db.close()

print("\n" + "=" * 50)
print("DATABASE FIX COMPLETED")
print("=" * 50)

input("\nPress Enter to close...")