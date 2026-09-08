"""
currency.py
Centralized currency configuration and formatting for Archon AI.
All monetary conversions flow through this single module.

To update the exchange rate, change USD_TO_INR_RATE below.
"""


# ── Configurable exchange rate (single source of truth) ──────────────────────
USD_TO_INR_RATE = 85.0   # 1 USD = 85 INR (approximate, update as needed)

CURRENCY_SYMBOL = "₹"
CURRENCY_CODE   = "INR"
INR_CURRENCY    = "INR"   # Alias used across modules


# ── Conversion helpers ────────────────────────────────────────────────────────

def usd_to_inr(amount_usd: float) -> float:
    """Convert a USD amount to INR using the centralized rate."""
    return round(amount_usd * USD_TO_INR_RATE, 2)


def format_inr(amount: float) -> str:
    """
    Format a number using Indian numbering system.
    Examples:
        1000       → ₹1,000
        100000     → ₹1,00,000
        1250000    → ₹12,50,000
        125000000  → ₹12,50,00,000
    """
    if amount is None:
        return f"{CURRENCY_SYMBOL}0"
    if amount < 0:
        return f"-{format_inr(-amount)}"

    amount = round(amount, 2)
    whole = int(amount)
    paise = round((amount - whole) * 100)

    # Indian grouping: last 3 digits, then groups of 2
    s = str(whole)
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        # Group the remaining digits in pairs from the right
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        groups.reverse()
        formatted = ",".join(groups) + "," + last3

    if paise > 0:
        return f"{CURRENCY_SYMBOL}{formatted}.{paise:02d}"
    return f"{CURRENCY_SYMBOL}{formatted}"


def format_inr_short(amount: float) -> str:
    """Short format for large amounts: ₹12.5L, ₹1.2Cr"""
    if amount >= 1_00_00_000:  # 1 Crore
        return f"{CURRENCY_SYMBOL}{amount / 1_00_00_000:.1f}Cr"
    if amount >= 1_00_000:     # 1 Lakh
        return f"{CURRENCY_SYMBOL}{amount / 1_00_000:.1f}L"
    if amount >= 1_000:
        return f"{CURRENCY_SYMBOL}{amount / 1_000:.1f}K"
    return format_inr(amount)


def format_usd_as_inr(amount_usd: float, decimals: int = 0) -> str:
    """
    Convert a USD amount to INR and return a formatted ₹ string.
    Used inline in description strings where prices were originally in USD.

    Examples:
        format_usd_as_inr(30)        → "₹2,550"
        format_usd_as_inr(0.115, 2)  → "₹9.78"
    """
    inr = usd_to_inr(amount_usd)
    if decimals > 0:
        # Show decimal places for small per-unit rates
        return f"{CURRENCY_SYMBOL}{inr:.{decimals}f}"
    return format_inr(inr)


def convert_usd_cost_payload_to_inr(payload: dict) -> dict:
    """
    Convert every numeric cost field in a cost payload from USD → INR.

    Converts the following keys if present:
      compute, database, storage, messaging, networking, monitoring,
      iot, ai_serving, total_monthly, scaling_10x_estimate

    Also converts each item's 'cost' field inside 'breakdown'.
    Sets currency = "INR".
    Leaves non-numeric and non-cost keys unchanged.
    """
    NUMERIC_COST_KEYS = {
        "compute", "database", "storage", "messaging",
        "networking", "monitoring", "iot", "ai_serving",
        "total_monthly", "scaling_10x_estimate",
    }

    result = dict(payload)
    result["currency"] = INR_CURRENCY

    for key in NUMERIC_COST_KEYS:
        if key in result and isinstance(result[key], (int, float)):
            result[key] = round(usd_to_inr(result[key]), 2)

    # Convert breakdown item costs
    if "breakdown" in result and isinstance(result["breakdown"], list):
        converted_breakdown = []
        for item in result["breakdown"]:
            item_copy = dict(item)
            if "cost" in item_copy and isinstance(item_copy["cost"], (int, float)):
                item_copy["cost"] = round(usd_to_inr(item_copy["cost"]), 2)
            converted_breakdown.append(item_copy)
        result["breakdown"] = converted_breakdown

    return result


import re as _re

def convert_usd_mentions_to_inr(text: str) -> str:
    """
    Post-process LLM or rule-based text output to replace any remaining
    USD monetary expressions with INR equivalents.

    Handles patterns such as:
      $120/month  →  ₹10,200/month
      $1,500      →  ₹1,27,500
      USD 500     →  ₹42,500
      $0.09/GB    →  ₹7.65/GB

    This is a safety net — AI prompts already request INR output.
    Does NOT replace $ used in code/template strings (e.g., ${var}).
    """
    if not text:
        return text

    def _dollar_replacer(m: _re.Match) -> str:
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
            inr = usd_to_inr(val)
            return format_inr(inr)
        except ValueError:
            return m.group(0)

    # Match $123, $1,234, $1.50 but NOT ${...}
    # Negative lookbehind for { prevents matching template literals
    text = _re.sub(r'(?<!\{)\$([0-9][0-9,]*(?:\.[0-9]+)?)', _dollar_replacer, text)

    # Match "USD 123" or "USD 1,234"
    def _usd_replacer(m: _re.Match) -> str:
        raw = m.group(1).replace(",", "")
        try:
            val = float(raw)
            inr = usd_to_inr(val)
            return format_inr(inr)
        except ValueError:
            return m.group(0)

    text = _re.sub(r'\bUSD\s+([0-9][0-9,]*(?:\.[0-9]+)?)', _usd_replacer, text)

    # Replace any remaining isolated "USD" label references
    text = text.replace(" USD", " INR")
    text = text.replace("USD ", "INR ")

    return text
