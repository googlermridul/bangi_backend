from .db import get_conn


def search_products(filters: dict, limit: int = 5) -> list[dict]:
    """
    Find products matching the filters. For each product we show its cheapest
    in-stock offer. NOTE: ordering here is a simple placeholder; real
    "best value" ranking is the Week 2 task.
    """
    where = ["o.in_stock = TRUE"]
    params: dict = {"limit": limit}

    if filters.get("category"):
        where.append("p.category = %(category)s")
        params["category"] = filters["category"]
    if filters.get("brand"):
        where.append("p.brand ILIKE %(brand)s")
        params["brand"] = filters["brand"]
    if filters.get("currency"):
        where.append("o.currency = %(currency)s")
        params["currency"] = filters["currency"]
    if filters.get("max_price") is not None:
        where.append("o.price <= %(max_price)s")
        params["max_price"] = filters["max_price"]
    if filters.get("min_price") is not None:
        where.append("o.price >= %(min_price)s")
        params["min_price"] = filters["min_price"]

    # Each required keyword must appear in the product name or specs.
    for i, term in enumerate(filters.get("must_have", [])):
        where.append(f"(p.name || ' ' || p.specs::text) ILIKE %(mh{i})s")
        params[f"mh{i}"] = f"%{term}%"

    sql = f"""
        SELECT * FROM (
            SELECT DISTINCT ON (p.id)
                p.id AS product_id, p.name, p.brand, p.category, p.specs, p.image_url,
                o.id AS offer_id, o.seller, o.price, o.currency
            FROM products p
            JOIN offers o ON o.product_id = p.id
            WHERE {' AND '.join(where)}
            ORDER BY p.id, o.price ASC
        ) cheapest
        ORDER BY price DESC
        LIMIT %(limit)s
    """

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    for row in rows:
        row["price"] = float(row["price"])
    return rows
