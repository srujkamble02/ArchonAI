"""
workforce_engine.py
Calculates workforce / human resource costs based on team configuration.
All logic is deterministic — no LLM involvement.
"""


from .currency import INR_CURRENCY, format_inr



# ── Conversion assumptions (clearly documented) ─────────────────────────────
HOURS_PER_DAY   = 8     # Standard working hours per day
DAYS_PER_MONTH  = 22    # Standard working days per month
MONTHS_PER_YEAR = 12    # Months per year

CONVERSION_ASSUMPTIONS = [
    f"Working hours per day: {HOURS_PER_DAY}",
    f"Working days per month: {DAYS_PER_MONTH}",
    f"Months per year: {MONTHS_PER_YEAR}",
    f"Hourly → Monthly: wage × {HOURS_PER_DAY} hrs × {DAYS_PER_MONTH} days",
    f"Daily → Monthly: wage × {DAYS_PER_MONTH} days",
    f"Yearly → Monthly: wage ÷ {MONTHS_PER_YEAR} months",
]

# ── Available roles ─────────────────────────────────────────────────────────
AVAILABLE_ROLES = [
    "Project Manager",
    "Software Developers",
    "Backend Developers",
    "Frontend Developers",
    "Full Stack Developers",
    "AI/ML Engineers",
    "DevOps Engineers",
    "Cloud Engineers",
    "UI/UX Designers",
    "QA Engineers",
    "Testers",
    "Security Engineers",
    "Data Engineers",
    "Database Administrators",
    "Other",
]


def calculate_workforce_cost(workforce_config: list, currency: str = INR_CURRENCY) -> dict:
    """
    Calculate workforce costs from a list of role configurations.
    
    Each item in workforce_config should have:
    - role: str
    - count: int (number of employees)
    - wage: float (wage per employee)
    - period: str (hourly | daily | monthly | yearly)
    
    Returns a structured breakdown with per-role costs, totals, and assumptions.
    """
    currency = INR_CURRENCY

    if not workforce_config:
        return {
            "configured": False,
            "roles": [],
            "total_monthly": 0,
            "total_yearly": 0,
            "currency": INR_CURRENCY,
            "assumptions": CONVERSION_ASSUMPTIONS,
            "summary": "No workforce configuration provided.",
        }

    roles_breakdown = []
    total_monthly = 0
    total_yearly = 0
    validation_warnings = []

    for item in workforce_config:
        role = item.get("role", "Unknown Role")
        count = item.get("count", 0)
        wage = item.get("wage", 0)
        period = item.get("period", "monthly").lower()

        # Validation
        if count < 0:
            validation_warnings.append(f"{role}: Employee count cannot be negative. Using 0.")
            count = 0
        if wage < 0:
            validation_warnings.append(f"{role}: Wage cannot be negative. Using 0.")
            wage = 0
        if count == 0 or wage == 0:
            # Skip zero-contribution roles but still include them
            roles_breakdown.append({
                "role": role,
                "count": count,
                "wage": wage,
                "period": period,
                "monthly_per_employee": 0,
                "monthly_total": 0,
                "yearly_total": 0,
                "conversion_note": "No cost (zero employees or zero wage)",
            })
            continue

        # Convert to monthly
        if period == "hourly":
            monthly_per_employee = wage * HOURS_PER_DAY * DAYS_PER_MONTH
            conversion_note = f"{format_inr(wage)}/hr × {HOURS_PER_DAY} hrs/day × {DAYS_PER_MONTH} days/mo"
        elif period == "daily":
            monthly_per_employee = wage * DAYS_PER_MONTH
            conversion_note = f"{format_inr(wage)}/day × {DAYS_PER_MONTH} days/mo"
        elif period == "yearly":
            monthly_per_employee = wage / MONTHS_PER_YEAR
            conversion_note = f"{format_inr(wage)}/yr ÷ {MONTHS_PER_YEAR} months"
        else:  # monthly (default)
            monthly_per_employee = wage
            conversion_note = f"{format_inr(wage)}/mo (direct)"

        monthly_total = monthly_per_employee * count
        yearly_total = monthly_total * MONTHS_PER_YEAR

        total_monthly += monthly_total
        total_yearly += yearly_total

        roles_breakdown.append({
            "role": role,
            "count": count,
            "wage": wage,
            "period": period,
            "monthly_per_employee": round(monthly_per_employee, 2),
            "monthly_total": round(monthly_total, 2),
            "yearly_total": round(yearly_total, 2),
            "conversion_note": conversion_note,
        })

    return {
        "configured": True,
        "roles": roles_breakdown,
        "total_monthly": round(total_monthly, 2),
        "total_yearly": round(total_yearly, 2),
        "total_employees": sum(r["count"] for r in roles_breakdown),
        "currency": INR_CURRENCY,
        "assumptions": CONVERSION_ASSUMPTIONS,
        "validation_warnings": validation_warnings,
        "summary": (
            f"Total workforce: {sum(r['count'] for r in roles_breakdown)} employees across "
            f"{len([r for r in roles_breakdown if r['count'] > 0])} roles. "
            f"Estimated monthly cost: {format_inr(total_monthly)}"
        ),
    }


def calculate_total_cost(infrastructure_cost: dict, workforce_cost: dict) -> dict:
    """
    Combine infrastructure and workforce costs into a unified total.
    """
    infra_monthly = infrastructure_cost.get("total_monthly", 0)
    infra_currency = "INR"

    wf_monthly = workforce_cost.get("total_monthly", 0)
    wf_currency = "INR"

    result = {
        "infrastructure_cost": {
            "monthly": round(infra_monthly, 2),
            "yearly": round(infra_monthly * 12, 2),
            "currency": INR_CURRENCY,
        },
        "workforce_cost": {
            "monthly": round(wf_monthly, 2),
            "yearly": round(wf_monthly * 12, 2),
            "currency": INR_CURRENCY,
        },
    }

    combined_monthly = infra_monthly + wf_monthly
    result["combined"] = {
        "monthly": round(combined_monthly, 2),
        "yearly": round(combined_monthly * 12, 2),
        "currency": INR_CURRENCY,
    }

    return result
