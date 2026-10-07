# AI Shopping: Backend Starter (local PostgreSQL, no Docker)

A small working backend: **PostgreSQL** (database) + **FastAPI** (API server).
It understands a question like `best 5G phone under 25k bdt`, filters products in the
database, and returns matching products. It ships with FAKE demo data so you can test
before any affiliate approval.

---

## What each tool is (plain English)

- **PostgreSQL**: the database. Stores products, prices, clicks, and user questions in tables.
- **FastAPI**: the server. Your Next.js site will send questions to it and receive products back.
- **Virtual environment (venv)**: a private folder of Python packages for this project only.
- **.env file**: a settings file for passwords and keys. Never upload it to GitHub.

---

## One-time setup

### 1. Check what you have
- **Python 3.11 or newer**: https://www.python.org/downloads/ (on Windows, tick "Add Python to PATH")
  Check: `python --version` (or `python3 --version` on Mac/Linux)
- **PostgreSQL running** on your PC. You need to know the **password** you set for the `postgres` user
  during installation. (On Windows, if the server is not running: open "Services", find
  `postgresql-x64-NN`, and click Start.)

### 2. Set up Python
Open a terminal in the `backend` folder:
```
cd backend
python -m venv venv
```
Activate it:
- **Windows (PowerShell):** `venv\Scripts\Activate.ps1`
  (if blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once)
- **Windows (cmd):** `venv\Scripts\activate.bat`
- **Mac/Linux:** `source venv/bin/activate`

You should now see `(venv)` at the start of your terminal line. Then:
```
pip install -r requirements.txt
```

### 3. Create your settings file
- **Windows:** `copy .env.example .env`
- **Mac/Linux:** `cp .env.example .env`

Open `.env` in VS Code and replace `YOUR_PASSWORD` with your PostgreSQL password:
```
DATABASE_URL=postgresql://postgres:MyPassword123@localhost:5432/aishop
```
- If your password has special characters like `@ : / # ? %`, URL-encode them (`@` becomes `%40`).
- If your PostgreSQL uses a different port than 5432, change it here.
- Leave `ANTHROPIC_API_KEY` empty for now.

### 4. Create the database and tables (one command)
```
python -m scripts.init_db
```
This creates a database named `aishop` (if it doesn't exist) and all the tables. You should see:
```
Created database 'aishop'.
Created tables: products, offers, clicks, queries.
```
It is safe to run again. To wipe all tables and start fresh: `python -m scripts.init_db --reset`

### 5. Load the demo data
```
python -m scripts.seed
```
You should see: `Seeded 12 demo products.`

### 6. Start the API
```
uvicorn app.main:app --reload
```
Open **http://127.0.0.1:8000/docs** in your browser. This is an automatic test page.

---

## Try it

On the `/docs` page: click **POST /search** -> **Try it out** -> put this in the box -> **Execute**:

```json
{ "query": "best 5G phone under 25k bdt" }
```

You'll see the understood `filters` and a list of `results`. Try these too:
- `gaming phone with 5g below $400`
- `noise cancelling earbuds under 5000 taka`
- `phone between 15k and 25k`

Other endpoints:
- `GET /health` -> checks the server and database
- `GET /go/1` -> logs a click for offer 1 and redirects to its link (this will be your "Buy" button)

---

## Looking inside the database

Easiest: open **pgAdmin** (installed with PostgreSQL) -> Servers -> PostgreSQL -> Databases -> `aishop`
-> Schemas -> Tables -> right-click `products` -> View/Edit Data -> All Rows.

Or in a terminal (if `psql` is in your PATH): `psql -U postgres -d aishop`, then
`SELECT * FROM products;` (type `\q` to exit).

---

## Project map

```
backend/
  sql/schema.sql            the database tables (read the comments)
  scripts/init_db.py        creates the database + tables
  scripts/seed.py           fake demo data (replace with real data later)
  app/
    db.py                   connects to the database
    query_parser.py         sentence -> filters  (contains the AI prompt)
    search.py               filters -> SQL query -> products
    main.py                 the API endpoints
```

How a request flows: `main.py` receives the question -> `query_parser.py` turns it into filters ->
`search.py` queries Postgres -> `main.py` returns JSON.

---

## Turn on the AI parser (optional, later)

1. Create an API key at https://console.anthropic.com
2. Put it in `backend/.env`: `ANTHROPIC_API_KEY=your-key`
3. Restart uvicorn.

Now an AI model reads the questions (using the prompt in `query_parser.py`) and understands
almost any wording. If the AI call fails, the app falls back to the simple parser automatically.
To use Gemini or GPT instead, only the `llm_parse` function needs to change.

---

## Common problems

- **`password authentication failed`**: the password in `backend/.env` is wrong.
- **`Connection refused`**: PostgreSQL is not running (start the service), or the port in `.env` is wrong.
- **`permission denied to create database`**: use the `postgres` user in `DATABASE_URL`, or create an empty database named `aishop` yourself in pgAdmin and run the command again.
- **`ModuleNotFoundError`**: the venv is not active (no `(venv)` in the terminal) or you skipped `pip install -r requirements.txt`.
- **`No module named app` / `No module named scripts`**: run commands from inside the `backend` folder.
- **Changed `schema.sql` but the database didn't change**: tables are only created once. Use `python -m scripts.init_db --reset`.

---

## What's next (Week 1 to 2)

1. Replace `scripts/seed.py` with importers for real sources (one file per store).
2. Add the value-ranking logic in `search.py` (right now it only filters; ordering is a placeholder).
3. Add the "why this pick" explanation step.
4. Connect the Next.js chat UI to `POST /search`.

Note: the search is intentionally simple. Keyword matching on specs is crude, and
that is fine for Week 1.
