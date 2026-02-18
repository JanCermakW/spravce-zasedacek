from sqlmodel import SQLModel, create_engine, Session

# Název souboru databáze (vytvoří se sám)
sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# check_same_thread=False je potřeba pro SQLite ve FastAPI
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """Vytvoří tabulky v databázi podle modelů."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependency pro FastAPI - dává nám session pro práci s DB."""
    with Session(engine) as session:
        yield session