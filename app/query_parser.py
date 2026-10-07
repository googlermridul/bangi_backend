"""
Turns a user's sentence into structured filters.

  "best 5G phone under 25k bdt"  ->  {"category": "smartphone", "max_price": 25000, ...}

Two modes:
  1. If ANTHROPIC_API_KEY is set, an AI model does it (understands almost any phrasing).
  2. Otherwise a simple rule-based parser does it (works offline, free, good for testing).
If the AI call fails for any reason, we fall back to the simple parser.
"""
import json
import os
import re

SYSTEM_PROMPT = """You are the query parser for a shopping website that sells electronics.
Your only job: read the user's shopping question and extract search filters.

Return ONLY a JSON object. No explanation, no markdown, no code fences.

The JSON must have exactly these keys:
{
  "category":  one of "smartphone", "earbuds", "laptop", or null,
  "max_price": number or null,
  "min_price": number or null,
  "currency":  "BDT", "USD", "EUR", "GBP", "INR" or null (ISO code),
  "brand":     string or null,
  "must_have": array of short lowercase keywords, e.g. ["5g", "gaming", "amoled"]
}

Rules:
- Use null for anything the user did not say. Never guess or invent values.
- Prices are plain numbers: "25k" = 25000, "1.5 lakh" = 150000, "$300" = 300.
- "under X" / "below X" / "up to X" -> max_price. "above X" / "at least X" -> min_price.
- Currency symbols: "$" = USD, "tk" / "taka" / "৳" = BDT. If no currency is given, use null.
- must_have holds required features only (network type, usage like gaming, display type).
  Do not put the brand or the budget in must_have.
- If the question is not about buying electronics, return all nulls and an empty must_have.

Examples:
User: best phone under 25k bdt
{"category":"smartphone","max_price":25000,"min_price":null,"currency":"BDT","brand":null,"must_have":[]}

User: gaming phone with 5g below $400
{"category":"smartphone","max_price":400,"min_price":null,"currency":"USD","brand":null,"must_have":["gaming","5g"]}

User: noise cancelling earbuds under 5000 taka
{"category":"earbuds","max_price":5000,"min_price":null,"currency":"BDT","brand":null,"must_have":["noise cancelling"]}
"""

CATEGORY_WORDS = {
    "smartphone": ["phone", "phones", "mobile", "smartphone", "smartphones"],
    "earbuds": ["earbuds", "earphone", "earphones", "headphone", "headphones", "airpods"],
    "laptop": ["laptop", "laptops", "notebook"],
}
FEATURES = ["5g", "gaming", "amoled", "oled", "wireless", "anc", "noise cancelling"]

EMPTY = {
    "category": None,
    "max_price": None,
    "min_price": None,
    "currency": None,
    "brand": None,
    "must_have": [],
}


def _to_number(num: str, k: str | None) -> float:
    value = float(num.replace(",", ""))
    return value * 1000 if k else value


def rule_based_parse(text: str) -> dict:
    t = text.lower()
    f = dict(EMPTY, must_have=[])

    if re.search(r"\bbdt\b|\btaka\b|\btk\b|৳", t):
        f["currency"] = "BDT"
    elif re.search(r"\$|\busd\b|\bdollars?\b", t):
        f["currency"] = "USD"

    for category, words in CATEGORY_WORDS.items():
        if any(re.search(rf"\b{w}\b", t) for w in words):
            f["category"] = category
            break

    between = re.search(
        r"between\s*[$৳]?\s*([\d,.]+)\s*(k)?\s*(?:and|to|-)\s*[$৳]?\s*([\d,.]+)\s*(k)?", t
    )
    under = re.search(
        r"(?:under|below|less than|within|max|upto|up to)\s*[$৳]?\s*([\d,.]+)\s*(k)?", t
    )
    above = re.search(r"(?:above|over|at least|min)\s*[$৳]?\s*([\d,.]+)\s*(k)?", t)
    if between:
        f["min_price"] = _to_number(between.group(1), between.group(2))
        f["max_price"] = _to_number(between.group(3), between.group(4))
    else:
        if under:
            f["max_price"] = _to_number(under.group(1), under.group(2))
        if above:
            f["min_price"] = _to_number(above.group(1), above.group(2))

    for feature in FEATURES:
        if re.search(rf"\b{re.escape(feature)}\b", t):
            f["must_have"].append(feature)
    return f


def _clean(data: dict) -> dict:
    """Make sure the result always has the right keys and types."""
    out = dict(EMPTY, must_have=[])
    for key in ("category", "currency", "brand"):
        value = data.get(key)
        out[key] = value.strip() if isinstance(value, str) and value.strip() else None
    if out["currency"]:
        out["currency"] = out["currency"].upper()
    for key in ("max_price", "min_price"):
        value = data.get(key)
        out[key] = float(value) if isinstance(value, (int, float)) else None
    must = data.get("must_have")
    if isinstance(must, list):
        out["must_have"] = [str(m).lower().strip() for m in must if str(m).strip()]
    return out


def llm_parse(text: str) -> dict:
    import anthropic  # imported here so the app still runs without the package/key

    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    message = client.messages.create(
        model=os.getenv("LLM_MODEL", "claude-haiku-4-5-20251001"),
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = message.content[0].text.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.MULTILINE).strip()
    return json.loads(raw)


def parse_query(text: str) -> dict:
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            return _clean(llm_parse(text))
        except Exception as error:  # noqa: BLE001 - we want to catch everything here
            print(f"[query_parser] AI parsing failed, using simple parser: {error}")
    return _clean(rule_based_parse(text))
