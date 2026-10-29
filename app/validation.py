"""Structural and referential integrity checks for CSV datasets."""
import csv
from pathlib import Path

FK_RULES = {
    "feeschedule.csv": [("program_id", "program.csv", "program_id")],
    "enrollment.csv": [("student_id", "student.csv", "student_id"), ("program_id", "program.csv", "program_id")],
    "invoice.csv": [("enrollment_id", "enrollment.csv", "enrollment_id"), ("student_id", "student.csv", "student_id")],
    "invoiceline.csv": [("invoice_id", "invoice.csv", "invoice_id")],
    "eligibility.csv": [("scholarship_id", "scholarship.csv", "scholarship_id"), ("student_id", "student.csv", "student_id"), ("enrollment_id", "enrollment.csv", "enrollment_id")],
    "payment.csv": [("student_id", "student.csv", "student_id")],
    "paymentallocation.csv": [("payment_id", "payment.csv", "payment_id"), ("invoice_id", "invoice.csv", "invoice_id"), ("invoice_line_id", "invoiceline.csv", "invoice_line_id")],
    "refund.csv": [("payment_id", "payment.csv", "payment_id"), ("student_id", "student.csv", "student_id")],
    "ledgerevent.csv": [("student_id", "student.csv", "student_id"), ("invoice_id", "invoice.csv", "invoice_id")]
}
PK_FIELDS = {
    "student.csv":"student_id", "program.csv":"program_id", "feeschedule.csv":"fee_schedule_id",
    "enrollment.csv":"enrollment_id", "invoice.csv":"invoice_id", "invoiceline.csv":"invoice_line_id",
    "scholarship.csv":"scholarship_id", "eligibility.csv":"eligibility_id", "payment.csv":"payment_id",
    "paymentallocation.csv":"allocation_id", "refund.csv":"refund_id", "ledgerevent.csv":"event_id"
}

def load(path):
    with Path(path).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def validate_dataset(data_dir):
    d = Path(data_dir)
    tables = {}
    errors = []
    for filename, pk in PK_FIELDS.items():
        path = d / filename
        if not path.exists():
            errors.append({"check":"FILE_EXISTS","file":filename,"detail":"Missing required CSV"})
            tables[filename] = []
            continue
        rows = load(path)
        tables[filename] = rows
        ids = [r.get(pk, "") for r in rows]
        if any(not x for x in ids):
            errors.append({"check":"PRIMARY_KEY_NOT_NULL","file":filename,"detail":f"Blank {pk}"})
        if len(ids) != len(set(ids)):
            errors.append({"check":"PRIMARY_KEY_UNIQUE","file":filename,"detail":f"Duplicate {pk}"})

    for child, rules in FK_RULES.items():
        for field, parent, parent_pk in rules:
            parent_ids = {r.get(parent_pk, "") for r in tables.get(parent, [])}
            for row in tables.get(child, []):
                value = row.get(field, "")
                if value and value not in parent_ids:
                    errors.append({"check":"FOREIGN_KEY","file":child,"detail":f"{field}={value} missing from {parent}"})
    return {"valid": not errors, "error_count": len(errors), "errors": errors}
