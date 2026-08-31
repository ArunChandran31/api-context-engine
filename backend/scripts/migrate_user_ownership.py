from __future__ import annotations

import sqlite3
from pathlib import Path


DATABASE_PATH = (
    Path(__file__).resolve().parents[1]
    / "api_context_engine.db"
)


def main() -> None:
    if not DATABASE_PATH.exists():
        raise SystemExit(
            f"Database not found: {DATABASE_PATH}"
        )

    connection = sqlite3.connect(DATABASE_PATH)

    try:
        cursor = connection.cursor()

        cursor.execute(
            "PRAGMA table_info(api_specifications)"
        )

        columns = {
            row[1]
            for row in cursor.fetchall()
        }

        if "user_id" not in columns:
            print(
                "Adding user_id column to api_specifications..."
            )

            cursor.execute(
                """
                ALTER TABLE api_specifications
                ADD COLUMN user_id VARCHAR(255)
                """
            )

            connection.commit()

            print("user_id column added successfully.")
        else:
            print(
                "user_id column already exists."
            )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
            ix_api_specifications_user_id
            ON api_specifications(user_id)
            """
        )

        connection.commit()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM api_specifications
            WHERE user_id IS NULL
            """
        )

        unowned_count = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM api_specifications
            """
        )

        total_count = cursor.fetchone()[0]

        print()
        print("===== OWNERSHIP MIGRATION STATUS =====")
        print(f"Total specifications: {total_count}")
        print(f"Specifications without owner: {unowned_count}")
        print()
        print(
            "The existing specifications have NOT been assigned "
            "to a user yet."
        )
        print(
            "That will happen after Supabase authentication "
            "is verified."
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()
