from app.database.base import Base
from app.database.session import engine


def main():
    print("Dropping all tables...")

    Base.metadata.drop_all(bind=engine)

    print("Creating all tables...")

    Base.metadata.create_all(bind=engine)

    print("Database successfully reset.")


if __name__ == "__main__":
    main()
