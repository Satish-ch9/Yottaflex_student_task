from decimal import Decimal, ROUND_HALF_UP
from datetime import date

CENT = Decimal("0.01")

def money(value) -> Decimal:
    return Decimal(str(value)).quantize(CENT, rounding=ROUND_HALF_UP)

def scholarship_amount(eligible_fee: Decimal, award_type: str, award_value: Decimal) -> Decimal:
    eligible_fee = money(eligible_fee)
    award_value = money(award_value)
    if award_type == "PERCENT":
        proposed = money(eligible_fee * award_value / Decimal("100"))
    elif award_type == "FIXED":
        proposed = award_value
    else:
        raise ValueError(f"Unsupported award_type: {award_type}")
    return min(max(proposed, Decimal("0.00")), eligible_fee)

def late_fee(balance: Decimal, due_date: date, as_of: date, monthly_rate: Decimal = Decimal("0.01")) -> Decimal:
    balance = max(money(balance), Decimal("0.00"))
    if balance == 0 or as_of <= due_date:
        return Decimal("0.00")
    days_late = (as_of - due_date).days
    # One month-equivalent for every started 30-day period after due date.
    periods = (days_late + 29) // 30
    return money(balance * monthly_rate * periods)

def invoice_status(gross: Decimal, credits: Decimal, allocated: Decimal, due_date: date, as_of: date) -> str:
    net_due = max(money(gross - credits), Decimal("0.00"))
    paid = max(money(allocated), Decimal("0.00"))
    if net_due == 0:
        return "PAID"
    if paid >= net_due:
        return "PAID"
    if paid > 0:
        return "PARTIALLY_PAID"
    if as_of > due_date:
        return "OVERDUE"
    return "OPEN"
