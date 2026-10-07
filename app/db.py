import os

import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://postgres:123456@localhost:5432/bangi"
)


def get_conn():
    """
    Open a database connection. Rows come back as dictionaries.
    connect_timeout is generous because a sleeping cloud database (e.g. Neon free)
    can take a moment to wake up on the first request.
    """
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
