"""
Creates the database (if missing) and the tables, using DATABASE_URL from your .env.
Works with a local PostgreSQL and with cloud databases like Neon.
Run from the backend folder:

    python -m scripts.init_db            # create database (if needed) + tables (safe to re-run)
    python -m scripts.init_db --reset    # DELETE all tables and recreate them
"""
import sys
from pathlib import Path

import psycopg
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app.db import DATABASE_URL, get_conn

SCHEMA_FILE = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"


def ensure_database() -> None:
    """Make sure the database itself exists."""
    info = conninfo_to_dict(DATABASE_URL)
    name = info["dbname"]

    # 1) If we can already connect to it, there is nothing to create
    #    (this is the normal case on Neon, where the database exists from the start).
    try:
        with psycopg.connect(DATABASE_URL, connect_timeout=20):
            print(f"Connected to database '{name}'.")
            return
    except psycopg.OperationalError as error:
        if "does not exist" not in str(error):
            raise  # wrong password, server down, etc: report it

    # 2) Otherwise create it (needs permission, fine on a local PostgreSQL).
    admin_conninfo = make_conninfo(**{**info, "dbname": "postgres"})
    with psycopg.connect(admin_conninfo, autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        print(f"Created database '{name}'.")


def create_tables(reset: bool) -> None:
    with get_conn() as conn:
        if reset:
            conn.execute("DROP TABLE IF EXISTS clicks, queries, offers, products CASCADE")
            print("Dropped old tables.")
        has_tables = conn.execute("SELECT to_regclass('public.products') AS t").fetchone()["t"]
        if has_tables:
            print("Tables already exist. (Use --reset to wipe and recreate them.)")
            return
        conn.execute(SCHEMA_FILE.read_text(encoding="utf-8"))
        print("Created tables: products, offers, clicks, queries.")


if __name__ == "__main__":
    try:
        ensure_database()
        create_tables(reset="--reset" in sys.argv)
    except psycopg.OperationalError as error:
        print("\nCould not connect to PostgreSQL:\n", error)
        print("\nCheck: 1) PostgreSQL is running  2) the password in backend/.env is correct")
        sys.exit(1)
