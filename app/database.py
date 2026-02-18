import os
from sqlmodel import SQLModel, create_engine, Session

# Konfigurace z environment variables (PostgreSQL produkce / SQLite fallback pro lokální vývoj)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

# SQLite potřebuje check_same_thread=False
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)


def create_db_and_tables():
    """Vytvoří tabulky v databázi podle modelů."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Dependency pro FastAPI - dává nám session pro práci s DB."""
    with Session(engine) as session:
        yield session
