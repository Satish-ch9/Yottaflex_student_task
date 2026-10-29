"""Auditable reconciliation and anomaly checks over generated CSV exports."""
import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

def read_csv(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def reconcile(data_dir):
    data_dir = Path(data_dir)
    invoices = read_csv(data_dir / "invoice.csv")
    lines = read_csv(data_dir / "invoiceline.csv")
    payments = read_csv(data_dir / "payment.csv")
    allocations = read_csv(data_dir / "paymentallocation.csv")
    refunds = read_csv(data_dir / "refund.csv")
    enrollments = read_csv(data_dir / "enrollment.csv")
    eligibilities = read_csv(data_dir / "eligibility.csv")

    invoice_by_id = {x["invoice_id"]: x for x in invoices}
    payment_by_id = {x["payment_id"]: x for x in payments}
    line_by_id = {x["invoice_line_id"]: x for x in lines}
    enrollment_by_id = {x["enrollment_id"]: x for x in enrollments}

    gross_by_invoice = defaultdict(Decimal)
    for line in lines:
        gross_by_invoice[line["invoice_id"]] += Decimal(line["amount"])

    alloc_by_invoice = defaultdict(Decimal)
    alloc_by_payment = defaultdict(Decimal)
    for a in allocations:
        alloc_by_invoice[a["invoice_id"]] += Decimal(a["amount"])
        alloc_by_payment[a["payment_id"]] += Decimal(a["amount"])

    refund_by_payment = defaultdict(Decimal)
    for r in refunds:
        if r["status"] in ("APPROVED", "PAID"):
            refund_by_payment[r["payment_id"]] += Decimal(r["amount"])

    exceptions = []
    for a in allocations:
        p = payment_by_id.get(a["payment_id"])
        if not p:
            exceptions.append({"issue_type":"MISSING_PAYMENT","record_id":a["allocation_id"],"severity":"HIGH"})
        elif Decimal(a["amount"]) > Decimal(p["amount"]):
            exceptions.append({"issue_type":"ALLOCATION_EXCEEDS_PAYMENT","record_id":a["allocation_id"],"severity":"HIGH"})

        line = line_by_id.get(a["invoice_line_id"])
        if not line or line["invoice_id"] != a["invoice_id"]:
            exceptions.append({"issue_type":"ALLOCATION_LINE_INVOICE_MISMATCH","record_id":a["allocation_id"],"severity":"HIGH"})

    for r in refunds:
        if refund_by_payment[r["payment_id"]] > Decimal(payment_by_id[r["payment_id"]]["amount"]):
            exceptions.append({"issue_type":"REFUND_EXCEEDS_NET_PAID","record_id":r["refund_id"],"severity":"HIGH"})

    seen_enrollment_terms = set()
    for inv in invoices:
        key = (inv["enrollment_id"], inv["term_id"])
        if key in seen_enrollment_terms:
            exceptions.append({"issue_type":"DUPLICATE_INVOICE","record_id":inv["invoice_id"],"severity":"HIGH"})
        seen_enrollment_terms.add(key)

    for e in eligibilities:
        if Decimal(e["award_amount"]) > Decimal(e["eligible_fee_amount"]):
            exceptions.append({"issue_type":"SCHOLARSHIP_EXCEEDS_ELIGIBLE_FEES","record_id":e["eligibility_id"],"severity":"HIGH"})

    for inv in invoices:
        if inv["enrollment_id"] not in enrollment_by_id:
            exceptions.append({"issue_type":"MISSING_ENROLLMENT","record_id":inv["invoice_id"],"severity":"HIGH"})

    # Invoice balance is calculated from invoice lines and allocations. This is a reporting value,
    # not an independently generated label.
    invoice_results = []
    for inv in invoices:
        net_due = max(gross_by_invoice[inv["invoice_id"]], Decimal("0"))
        allocated = alloc_by_invoice[inv["invoice_id"]]
        balance = net_due - allocated
        invoice_results.append({
            "invoice_id": inv["invoice_id"], "student_id": inv["student_id"],
            "gross_less_credits": str(net_due.quantize(Decimal("0.01"))),
            "allocated_amount": str(allocated.quantize(Decimal("0.01"))),
            "balance": str(balance.quantize(Decimal("0.01"))),
            "reconciled": "YES" if balance >= 0 else "NO"
        })

    total_due = sum((Decimal(x["gross_less_credits"]) for x in invoice_results), Decimal("0"))
    total_allocated = sum(alloc_by_invoice.values(), Decimal("0"))
    total_refunded = sum(refund_by_payment.values(), Decimal("0"))
    return {
        "metrics": {
            "students_in_scope": len({i["student_id"] for i in invoices}),
            "invoice_count": len(invoices),
            "payment_count": len(payments),
            "allocation_count": len(allocations),
            "refund_count": len(refunds),
            "invoice_total_after_credits": str(total_due.quantize(Decimal("0.01"))),
            "allocated_total": str(total_allocated.quantize(Decimal("0.01"))),
            "refund_total": str(total_refunded.quantize(Decimal("0.01"))),
            "exception_count": len(exceptions),
            "invoices_with_negative_balance": sum(1 for x in invoice_results if Decimal(x["balance"]) < 0),
            "invoice_balance_reconciliation_rate": round(
                100 * sum(1 for x in invoice_results if Decimal(x["balance"]) >= 0) / max(len(invoice_results), 1), 2
            )
        },
        "exceptions": exceptions,
        "invoice_balances": invoice_results
    }
