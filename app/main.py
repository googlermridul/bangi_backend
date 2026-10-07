import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from psycopg.types.json import Jsonb
from pydantic import BaseModel

from .db import get_conn
from .query_parser import parse_query
from .search import search_products

app = FastAPI(title="AI Shopping API")

# Which websites may call this API from a browser.
# Set ALLOWED_ORIGINS as a comma-separated list, no trailing slashes, e.g.
#   https://yourdomain.com,https://www.yourdomain.com,http://localhost:3000
ALLOWED_ORIGINS = [
    o.strip().rstrip("/")
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_CURRENCY = os.getenv("DEFAULT_CURRENCY", "BDT")


class SearchRequest(BaseModel):
    query: str


@app.get("/ping")
def ping():
    """Lightweight check that does NOT touch the database (safe for uptime monitors)."""
    return {"status": "ok"}


@app.get("/health")
def health():
    """Quick check that the server and database are alive."""
    with get_conn() as conn:
        conn.execute("SELECT 1")
    return {"status": "ok"}


@app.post("/search")
def search(req: SearchRequest):
    text = req.query.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Query is empty")

    filters = parse_query(text)
    # If the user gave a budget but no currency, assume the default one.
    if not filters["currency"] and (filters["max_price"] or filters["min_price"]):
        filters["currency"] = DEFAULT_CURRENCY

    results = search_products(filters, limit=5)

    with get_conn() as conn:
        conn.execute(
            "INSERT INTO queries (user_text, parsed_filters, result_count) VALUES (%s, %s, %s)",
            (text, Jsonb(filters), len(results)),
        )

    return {"query": text, "filters": filters, "results": results}


@app.get("/go/{offer_id}")
def go(offer_id: int, q: str | None = None):
    """The 'Buy' button points here: we log the click, then redirect to the seller."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT affiliate_url FROM offers WHERE id = %s", (offer_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Offer not found")
        conn.execute(
            "INSERT INTO clicks (offer_id, query_text) VALUES (%s, %s)", (offer_id, q)
        )
    return RedirectResponse(row["affiliate_url"])
