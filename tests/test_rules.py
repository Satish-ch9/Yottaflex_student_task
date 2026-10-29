from datetime import date
from decimal import Decimal
from app.rules import scholarship_amount, late_fee, invoice_status

def test_scholarship_is_capped_at_eligible_fee():
    assert scholarship_amount(Decimal("100"), "FIXED", Decimal("150")) == Decimal("100.00")

def test_percentage_scholarship():
    assert scholarship_amount(Decimal("800"), "PERCENT", Decimal("25")) == Decimal("200.00")

def test_late_fee():
    assert late_fee(Decimal("1000"), date(2026, 9, 1), date(2026, 10, 2)) == Decimal("20.00")

def test_invoice_status_paid():
    assert invoice_status(Decimal("100"), Decimal("10"), Decimal("90"), date(2026, 9, 1), date(2026, 10, 1)) == "PAID"
