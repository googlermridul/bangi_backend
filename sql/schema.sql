-- AI Shopping database schema (PostgreSQL)

-- A product is the thing itself (e.g. "Nova N5"), independent of who sells it.
CREATE TABLE products (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    brand       TEXT,
    category    TEXT NOT NULL,            -- 'smartphone', 'earbuds', ...
    specs       JSONB NOT NULL DEFAULT '{}',  -- flexible: {"ram_gb": 6, "network": "5G"}
    image_url   TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- An offer is one seller's price for one product.
-- One product can have many offers (Star Tech, Daraz, Amazon...).
CREATE TABLE offers (
    id            SERIAL PRIMARY KEY,
    product_id    INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    seller        TEXT NOT NULL,
    price         NUMERIC(12,2) NOT NULL,
    currency      CHAR(3) NOT NULL,       -- 'BDT', 'USD'
    in_stock      BOOLEAN NOT NULL DEFAULT TRUE,
    affiliate_url TEXT NOT NULL,
    last_updated  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Every time a user clicks "Buy", we log it. This is how you learn what works.
CREATE TABLE clicks (
    id          SERIAL PRIMARY KEY,
    offer_id    INTEGER NOT NULL REFERENCES offers(id) ON DELETE CASCADE,
    query_text  TEXT,
    clicked_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Every question users ask, plus what we understood from it.
CREATE TABLE queries (
    id              SERIAL PRIMARY KEY,
    user_text       TEXT NOT NULL,
    parsed_filters  JSONB,
    result_count    INTEGER,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes make searches fast as data grows.
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_offers_product    ON offers(product_id);
CREATE INDEX idx_offers_price      ON offers(currency, price);
