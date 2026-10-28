"""Database lifecycle shared by API, imports, and training commands."""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.models.database import Base

ROOT = Path(__file__).resolve().parents[3]
load_dotenv(ROOT / ".env")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{(ROOT / 'data/ecommerce.db').as_posix()}")
options = {}
if DATABASE_URL.startswith("sqlite"):
    database = make_url(DATABASE_URL).database
    if database and database != ":memory:":
        Path(database).resolve().parent.mkdir(parents=True, exist_ok=True)
    options["connect_args"] = {"check_same_thread": False, "timeout": 30}
    if not database or database == ":memory:":
        options["poolclass"] = StaticPool
engine = create_engine(DATABASE_URL, **options)
if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(bind=engine, autoflush=False)


def init_db():
    Base.metadata.create_all(engine)


def get_db():
    with SessionLocal() as db:
        yield db


def get_db_session():
    return SessionLocal()


def seed_database(**paths):
    from backend.app.services.upload_service import upload_multiple_csvs

    files = {
        name: str(ROOT / "data" / f"{name}.csv")
        for name in ["customers", "products", "promotions", "events", "orders"]
    }
    files.update({key.removesuffix("_csv"): value for key, value in paths.items()})
    with SessionLocal() as db:
        result = upload_multiple_csvs(db, files)
        if result["errors"]:
            raise ValueError("; ".join(result["errors"]))
        return result


if __name__ == "__main__":
    init_db()
    print(seed_database())
