from sqlalchemy import inspect

from app.database.session import engine


def print_separator():
    print("=" * 60)


def main():
    inspector = inspect(engine)

    print_separator()
    print("API CONTEXT ENGINE DATABASE INSPECTOR")
    print_separator()

    tables = inspector.get_table_names()

    print(f"\nTotal Tables : {len(tables)}")

    if not tables:
        print("\nNo tables found.")
        return

    for table in tables:
        print_separator()
        print(f"TABLE : {table}")
        print_separator()

        print("\nColumns:")

        for column in inspector.get_columns(table):
            print(f"  • {column['name']:<25}" f"{column['type']}")

        print("\nPrimary Key:")

        pk = inspector.get_pk_constraint(table)

        print(f"  {pk['constrained_columns']}")

        fks = inspector.get_foreign_keys(table)

        if fks:
            print("\nForeign Keys:")

            for fk in fks:
                print(f"  {fk['constrained_columns']} " f"-> {fk['referred_table']}")

        else:
            print("\nForeign Keys: None")

    print_separator()


if __name__ == "__main__":
    main()
