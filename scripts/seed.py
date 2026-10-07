"""
Loads DEMO data so you can test without real stores.
All names, specs, prices and links below are FAKE placeholders.
Run from the backend folder:   python -m scripts.seed
Running it again wipes the tables and reloads (safe while developing).
"""
from psycopg.types.json import Jsonb

from app.db import get_conn

# (name, brand, category, specs, [(seller, price, currency)])
PRODUCTS = [
    ("Nova N5", "Nova", "smartphone", {"ram_gb": 6, "storage_gb": 128, "battery_mah": 5000, "camera_mp": 50, "network": "4G", "tags": ["budget"]},
     [("DemoStore BD", 17990, "BDT")]),
    ("Nova N7 5G", "Nova", "smartphone", {"ram_gb": 8, "storage_gb": 128, "battery_mah": 5000, "camera_mp": 64, "network": "5G", "display": "AMOLED"},
     [("DemoStore BD", 23990, "BDT"), ("DemoMart", 24500, "BDT")]),
    ("Zenix Z3", "Zenix", "smartphone", {"ram_gb": 6, "storage_gb": 128, "battery_mah": 5500, "camera_mp": 50, "network": "4G", "display": "LCD"},
     [("DemoMart", 19990, "BDT")]),
    ("Zenix Z9 Gaming 5G", "Zenix", "smartphone", {"ram_gb": 12, "storage_gb": 256, "battery_mah": 6000, "camera_mp": 50, "network": "5G", "display": "AMOLED", "tags": ["gaming"]},
     [("DemoStore BD", 24990, "BDT"), ("DemoWorld US", 229, "USD")]),
    ("Aero A1", "Aero", "smartphone", {"ram_gb": 4, "storage_gb": 64, "battery_mah": 4500, "camera_mp": 13, "network": "4G"},
     [("DemoMart", 11990, "BDT")]),
    ("Aero A8 Pro 5G", "Aero", "smartphone", {"ram_gb": 8, "storage_gb": 256, "battery_mah": 5000, "camera_mp": 108, "network": "5G", "display": "AMOLED"},
     [("DemoStore BD", 38990, "BDT"), ("DemoWorld US", 349, "USD")]),
    ("Orbit O2 5G", "Orbit", "smartphone", {"ram_gb": 8, "storage_gb": 128, "battery_mah": 5200, "camera_mp": 50, "network": "5G", "display": "AMOLED", "tags": ["gaming"]},
     [("DemoWorld US", 299, "USD")]),
    ("Orbit O5 Ultra", "Orbit", "smartphone", {"ram_gb": 12, "storage_gb": 512, "battery_mah": 5000, "camera_mp": 200, "network": "5G", "display": "AMOLED"},
     [("DemoWorld US", 699, "USD")]),
    ("PodX Lite", "PodX", "earbuds", {"battery_hours": 24, "wireless": True, "anc": False},
     [("DemoMart", 1490, "BDT")]),
    ("PodX Pro ANC", "PodX", "earbuds", {"battery_hours": 30, "wireless": True, "anc": True, "tags": ["noise cancelling"]},
     [("DemoStore BD", 4990, "BDT"), ("DemoWorld US", 59, "USD")]),
    ("Zenix Buds S", "Zenix", "earbuds", {"battery_hours": 20, "wireless": True, "anc": False},
     [("DemoMart", 2290, "BDT")]),
    ("Aero Air ANC", "Aero", "earbuds", {"battery_hours": 28, "wireless": True, "anc": True, "tags": ["noise cancelling"]},
     [("DemoStore BD", 6990, "BDT")]),
]


def main():
    with get_conn() as conn:
        conn.execute("TRUNCATE clicks, queries, offers, products RESTART IDENTITY CASCADE")
        for name, brand, category, specs, offers in PRODUCTS:
            product_id = conn.execute(
                "INSERT INTO products (name, brand, category, specs) VALUES (%s, %s, %s, %s) RETURNING id",
                (name, brand, category, Jsonb(specs)),
            ).fetchone()["id"]
            for seller, price, currency in offers:
                slug = name.lower().replace(" ", "-")
                conn.execute(
                    "INSERT INTO offers (product_id, seller, price, currency, affiliate_url) VALUES (%s, %s, %s, %s, %s)",
                    (product_id, seller, price, currency, f"https://example.com/demo/{slug}"),
                )
    print(f"Seeded {len(PRODUCTS)} demo products.")


if __name__ == "__main__":
    main()
