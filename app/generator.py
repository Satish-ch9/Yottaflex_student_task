
"""Deterministic synthetic data generator. Never use real student information."""

import argparse
import csv
import json
import random
import hashlib
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from app.config import DEFAULT_SEED, TERM_ID, SAMPLE_DIR
from app.rules import money, scholarship_amount


PROGRAM_COUNT = 20
TARGET_POSITIVE_SCHOLARSHIP_AWARDS = 15000

INCOME_BANDS = ("LOW", "MEDIUM", "HIGH")
RESIDENCIES = ("DOMESTIC", "INTERNATIONAL")
METHODS = ("CARD", "BANK_TRANSFER", "UPI", "CASH")

FIRST_NAMES = (
    "Aarav", "Aditi", "Ananya", "Arjun", "Diya", "Ishaan",
    "Kavya", "Meera", "Neel", "Riya", "Sana", "Vihaan"
)
LAST_NAMES = (
    "Sharma", "Reddy", "Patel", "Rao", "Kumar",
    "Gupta", "Nair", "Singh", "Das", "Iyer"
)


def iso(d):
    return d.isoformat()


def deterministic_id(prefix, n, width=6):
    return f"{prefix}-{n:0{width}d}"


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)

    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def generate_dataset(
    students=100,
    invoices=300,
    payments=500,
    seed=DEFAULT_SEED,
    output_dir=SAMPLE_DIR,
    anomalies=True
):
    """Generate deterministic synthetic tuition and payment CSV files."""

    if students < 1 or invoices < 1 or payments < 1:
        raise ValueError(
            "students, invoices, and payments must be positive"
        )

    rng = random.Random(seed)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    today = date(2026, 10, 28)
    term_start = date(2026, 8, 1)
    due_date = date(2026, 9, 15)

    # ---------------------------------------------------------
    # Programs
    # ---------------------------------------------------------
    programs = []

    for i in range(1, PROGRAM_COUNT + 1):
        programs.append({
            "program_id": f"PRG-{i:03d}",
            "program_name": f"Program {i:02d}",
            "department": (
                "Engineering", "Business", "Arts", "Science"
            )[(i - 1) % 4],
            "active": 1
        })

    # ---------------------------------------------------------
    # Fee schedules
    # ---------------------------------------------------------
    fees = []

    fee_definitions = [
        ("TUITION", "Tuition", 1.0, 1),
        ("LAB", "Laboratory Fee", 0.12, 1),
        ("LIBRARY", "Library Fee", 0.04, 0)
    ]

    for p_idx, program in enumerate(programs, 1):
        base = 1800 + (p_idx * 125)

        for j, (code, name, fraction, eligible) in enumerate(
            fee_definitions, 1
        ):
            fees.append({
                "fee_schedule_id": f"FEE-{p_idx:03d}-{j:02d}",
                "program_id": program["program_id"],
                "term_id": TERM_ID,
                "fee_code": code,
                "fee_name": name,
                "amount": str(
                    money(Decimal(base) * Decimal(str(fraction)))
                ),
                "scholarship_eligible": eligible,
                "effective_from": iso(term_start),
                "effective_to": "2026-12-31"
            })

    # ---------------------------------------------------------
    # Students
    # ---------------------------------------------------------
    students_rows = []

    for i in range(1, students + 1):
        students_rows.append({
            "student_id": deterministic_id("STU", i),
            "first_name": rng.choice(FIRST_NAMES),
            "last_name": rng.choice(LAST_NAMES),
            "email": f"student{i:06d}@example.edu",
            "residency_status": rng.choice(RESIDENCIES),
            "household_income_band": rng.choices(
                INCOME_BANDS,
                weights=(4, 4, 2),
                k=1
            )[0],
            "created_at": "2026-07-15"
        })

    # ---------------------------------------------------------
    # Enrollments
    # ---------------------------------------------------------
    enrollments = []
    enrollment_count = max(students, invoices)

    for i in range(1, enrollment_count + 1):
        student_num = ((i - 1) % students) + 1
        program_num = rng.randint(1, PROGRAM_COUNT)

        status_roll = rng.random()

        if status_roll < 0.035:
            status = "WITHDRAWN"
        elif status_roll < 0.045:
            status = "CANCELLED"
        else:
            status = "ACTIVE"

        enrollments.append({
            "enrollment_id": f"ENR-{i:07d}",
            "student_id": deterministic_id("STU", student_num),
            "program_id": f"PRG-{program_num:03d}",
            "term_id": TERM_ID,
            "enrollment_date": iso(
                term_start + timedelta(days=rng.randint(0, 20))
            ),
            "status": status,
            "withdrawn_at": (
                iso(date(2026, 9, 1))
                if status == "WITHDRAWN"
                else ""
            )
        })

    # ---------------------------------------------------------
    # Scholarship definitions
    # ---------------------------------------------------------
    scholarship_rows = [
        {
            "scholarship_id": "SCH-2026-000001",
            "scholarship_name": "Access Grant",
            "term_id": TERM_ID,
            "award_type": "PERCENT",
            "award_value": "25",
            "min_income_band": "LOW",
            "required_residency": "",
            "active": 1
        },
        {
            "scholarship_id": "SCH-2026-000002",
            "scholarship_name": "Domestic Support Award",
            "term_id": TERM_ID,
            "award_type": "FIXED",
            "award_value": "500",
            "min_income_band": "MEDIUM",
            "required_residency": "DOMESTIC",
            "active": 1
        },
        {
            "scholarship_id": "SCH-2026-000003",
            "scholarship_name": "Need-Based Award",
            "term_id": TERM_ID,
            "award_type": "PERCENT",
            "award_value": "15",
            "min_income_band": "LOW",
            "required_residency": "",
            "active": 1
        }
    ]

    fee_by_program = {}

    for fee in fees:
        fee_by_program.setdefault(
            fee["program_id"], []
        ).append(fee)

    student_by_id = {
        student["student_id"]: student
        for student in students_rows
    }

    # ---------------------------------------------------------
    # Invoices, invoice lines, scholarships, and ledger
    # ---------------------------------------------------------
    invoices_rows = []
    lines_rows = []
    eligibility_rows = []
    ledger_rows = []
    invoice_specs = []

    positive_awards_count = 0

    for i in range(1, invoices + 1):
        enrollment = enrollments[(i - 1) % len(enrollments)]
        invoice_issue = "NONE"

        # Inject a labelled duplicate-invoice candidate.
        if (
            anomalies
            and i == max(2, invoices // 5)
            and invoice_specs
        ):
            enrollment = invoice_specs[-1][1]
            invoice_issue = "DUPLICATE_INVOICE"

        invoice_id = (
            f"INV-{enrollment['student_id']}-2026-{i:06d}"
        )

        invoice_date = term_start + timedelta(
            days=rng.randint(0, 25)
        )

        invoice = {
            "invoice_id": invoice_id,
            "enrollment_id": enrollment["enrollment_id"],
            "student_id": enrollment["student_id"],
            "term_id": TERM_ID,
            "invoice_date": iso(invoice_date),
            "due_date": iso(due_date),
            "status": "OPEN",
            "issue_type": invoice_issue
        }

        invoices_rows.append(invoice)
        invoice_specs.append((invoice, enrollment))

        line_total = Decimal("0")
        line_index = 0

        # Create normal fee lines.
        for fee in fee_by_program[enrollment["program_id"]]:
            line_index += 1
            amount = money(fee["amount"])

            lines_rows.append({
                "invoice_line_id": (
                    f"LINE-{i:07d}-{line_index:02d}"
                ),
                "invoice_id": invoice_id,
                "fee_schedule_id": fee["fee_schedule_id"],
                "line_code": fee["fee_code"],
                "description": fee["fee_name"],
                "amount": str(amount),
                "scholarship_eligible": (
                    fee["scholarship_eligible"]
                ),
                "line_type": (
                    "TUITION"
                    if fee["fee_code"] == "TUITION"
                    else "FEE"
                )
            })

            line_total += amount

        student = student_by_id[enrollment["student_id"]]

        # Only eligible fee lines are used to calculate awards.
        eligible_total = sum(
            (
                money(line["amount"])
                for line in lines_rows
                if (
                    line["invoice_id"] == invoice_id
                    and int(line["scholarship_eligible"]) == 1
                    and Decimal(line["amount"]) > 0
                )
            ),
            Decimal("0")
        )

        # This value decreases after each award so combined
        # scholarship credits cannot exceed eligible fees.
        remaining_eligible_fees = eligible_total

        for s_idx, scholarship in enumerate(
            scholarship_rows, 1
        ):
            is_eligible = (
                scholarship["active"] == 1
                and student["household_income_band"]
                in ("LOW", "MEDIUM")
                and (
                    student["household_income_band"]
                    == scholarship["min_income_band"]
                    or (
                        scholarship["min_income_band"] == "LOW"
                        and student["household_income_band"] == "LOW"
                    )
                )
                and (
                    not scholarship["required_residency"]
                    or student["residency_status"]
                    == scholarship["required_residency"]
                )
                and enrollment["status"] == "ACTIVE"
            )

            award = Decimal("0")
            decision_reason = "CRITERIA_NOT_MET"

            if is_eligible:
                if (
                    positive_awards_count
                    >= TARGET_POSITIVE_SCHOLARSHIP_AWARDS
                ):
                    decision_reason = "AWARD_TARGET_REACHED"

                elif remaining_eligible_fees <= 0:
                    decision_reason = (
                        "NO_ELIGIBLE_FEES_REMAINING"
                    )

                else:
                    calculated_award = scholarship_amount(
                        eligible_total,
                        scholarship["award_type"],
                        Decimal(scholarship["award_value"])
                    )

                    award = min(
                        money(calculated_award),
                        remaining_eligible_fees
                    )

                    if award > 0:
                        positive_awards_count += 1
                        remaining_eligible_fees -= award
                        decision_reason = "ELIGIBLE_BY_RULE"
                    else:
                        decision_reason = (
                            "NO_ELIGIBLE_FEES_REMAINING"
                        )

            eligibility_rows.append({
                "eligibility_id": (
                    f"ELIG-{i:07d}-{s_idx:02d}"
                ),
                "scholarship_id": scholarship["scholarship_id"],
                "student_id": enrollment["student_id"],
                "enrollment_id": enrollment["enrollment_id"],
                "eligible": int(is_eligible),
                "eligible_fee_amount": str(eligible_total),
                "award_amount": str(award),
                "decision_reason": decision_reason,
                "decided_at": iso(invoice_date)
            })

            if award > 0:
                line_index += 1

                lines_rows.append({
                    "invoice_line_id": (
                        f"LINE-{i:07d}-{line_index:02d}"
                    ),
                    "invoice_id": invoice_id,
                    "fee_schedule_id": "",
                    "line_code": f"SCH-{s_idx:02d}",
                    "description": scholarship["scholarship_name"],
                    "amount": str(-award),
                    "scholarship_eligible": 0,
                    "line_type": "WAIVER"
                })

                line_total -= award

        # Final invoice amount and invoice ledger event.
        net = max(line_total, Decimal("0"))

        invoice["status"] = (
            "OVERDUE"
            if today > due_date and net > 0
            else "OPEN"
        )

        invoice["issue_type"] = invoice_issue

        ledger_rows.append({
            "event_id": f"EVT-INV-{i:07d}",
            "student_id": enrollment["student_id"],
            "invoice_id": invoice_id,
            "event_type": "INVOICE_ISSUED",
            "amount": str(net),
            "event_date": iso(invoice_date),
            "source_id": invoice_id,
            "notes": (
                "Invoice total after approved scholarship credits"
            )
        })

    # ---------------------------------------------------------
    # Payment allocation candidates
    # ---------------------------------------------------------
    positive_lines_by_student = {}
    invoice_by_id = {
        invoice["invoice_id"]: invoice
        for invoice in invoices_rows
    }

    for line in lines_rows:
        if (
            Decimal(line["amount"]) > 0
            and line["line_type"] != "WAIVER"
        ):
            student_id = invoice_by_id[
                line["invoice_id"]
            ]["student_id"]

            positive_lines_by_student.setdefault(
                student_id, []
            ).append(line)

    # ---------------------------------------------------------
    # Payments and allocations
    # ---------------------------------------------------------
    payments_rows = []
    allocations_rows = []
    refunds_rows = []

    for i in range(1, payments + 1):
        student_num = rng.randint(1, students)
        student_id = deterministic_id("STU", student_num)

        payment_date = term_start + timedelta(
            days=rng.randint(5, 95)
        )

        amount = money(Decimal(rng.randint(100, 1800)))

        status = rng.choices(
            ("SETTLED", "PENDING", "FAILED"),
            weights=(88, 8, 4),
            k=1
        )[0]

        payment_id = deterministic_id("PAY", i)

        payments_rows.append({
            "payment_id": payment_id,
            "student_id": student_id,
            "payment_date": iso(payment_date),
            "amount": str(amount),
            "method": rng.choice(METHODS),
            "status": status,
            "external_reference": (
                f"EXT-{seed}-{i:07d}"
            )
        })

        if status == "SETTLED":
            candidates = positive_lines_by_student.get(
                student_id, []
            )

            if candidates:
                line = rng.choice(candidates)
                invoice_for_payment = invoice_by_id[
                    line["invoice_id"]
                ]

                allocation_amount = min(
                    amount,
                    money(line["amount"])
                )

                allocation_issue = "NONE"

                # Inject an over-allocation anomaly.
                if (
                    anomalies
                    and i == max(1, payments // 7)
                ):
                    allocation_amount = (
                        amount + Decimal("25.00")
                    )
                    allocation_issue = (
                        "ALLOCATION_EXCEEDS_PAYMENT"
                    )

                allocations_rows.append({
                    "allocation_id": (
                        f"ALLOC-{payment_id}-01"
                    ),
                    "payment_id": payment_id,
                    "invoice_id": (
                        invoice_for_payment["invoice_id"]
                    ),
                    "invoice_line_id": line["invoice_line_id"],
                    "amount": str(allocation_amount),
                    "allocated_at": iso(payment_date),
                    "issue_type": allocation_issue
                })

                ledger_rows.append({
                    "event_id": f"EVT-ALLOC-{i:07d}",
                    "student_id": student_id,
                    "invoice_id": (
                        invoice_for_payment["invoice_id"]
                    ),
                    "event_type": "PAYMENT_ALLOCATION",
                    "amount": str(allocation_amount),
                    "event_date": iso(payment_date),
                    "source_id": payment_id,
                    "notes": (
                        "Allocation event; negative amounts "
                        "are not used"
                    )
                })

    # ---------------------------------------------------------
    # Refunds
    # ---------------------------------------------------------
    settled_payments = [
        payment for payment in payments_rows
        if payment["status"] == "SETTLED"
    ]

    for idx, payment in enumerate(settled_payments, 1):
        if (
            (anomalies and idx == 1)
            or rng.random() < 0.025
        ):
            refund_amount = money(
                Decimal(payment["amount"]) * Decimal("0.25")
            )

            refund_issue = "NONE"

            # Inject one refund-overpayment anomaly.
            if anomalies and idx == 1:
                refund_amount = money(
                    Decimal(payment["amount"])
                    + Decimal("50")
                )
                refund_issue = "REFUND_EXCEEDS_NET_PAID"

            refunds_rows.append({
                "refund_id": f"REF-{idx:07d}",
                "payment_id": payment["payment_id"],
                "student_id": payment["student_id"],
                "refund_date": iso(
                    date.fromisoformat(payment["payment_date"])
                    + timedelta(days=2)
                ),
                "amount": str(refund_amount),
                "reason": "WITHDRAWAL_OR_DUPLICATE_PAYMENT",
                "status": "PAID",
                "issue_type": refund_issue
            })

    # ---------------------------------------------------------
    # Ground truth for anomaly detection
    # ---------------------------------------------------------
    ground_truth = []

    if anomalies:
        anomaly_specs = [
            (
                "ALLOCATION_EXCEEDS_PAYMENT",
                "Payment allocation exceeds its source payment.",
                "PaymentAllocation",
                allocations_rows
            ),
            (
                "DUPLICATE_INVOICE",
                "A duplicate invoice candidate was labelled for review.",
                "Invoice",
                invoices_rows
            ),
            (
                "REFUND_EXCEEDS_NET_PAID",
                "Refund exceeds the payment amount before other refunds.",
                "Refund",
                refunds_rows
            )
        ]

        id_fields = {
            "PaymentAllocation": "allocation_id",
            "Invoice": "invoice_id",
            "Refund": "refund_id"
        }

        for issue_type, description, table, rows in anomaly_specs:
            for row in rows:
                if row.get("issue_type") == issue_type:
                    ground_truth.append({
                        "issue_id": (
                            f"GT-{len(ground_truth) + 1:05d}"
                        ),
                        "entity": table,
                        "record_id": row[id_fields[table]],
                        "issue_type": issue_type,
                        "expected_decision": "FLAG_FOR_REVIEW",
                        "description": description
                    })

        ground_truth.append({
            "issue_id": f"GT-{len(ground_truth) + 1:05d}",
            "entity": "Eligibility",
            "record_id": "TEST-SCHOLARSHIP-OVER-ELIGIBLE-FEES",
            "issue_type": "SCHOLARSHIP_EXCEEDS_ELIGIBLE_FEES",
            "expected_decision": "REJECT_OR_CAP_AWARD",
            "description": (
                "Synthetic negative test fixture; not part of "
                "valid baseline transaction tables."
            )
        })

        ground_truth.append({
            "issue_id": f"GT-{len(ground_truth) + 1:05d}",
            "entity": "Ledger",
            "record_id": "TEST-BALANCE-MISMATCH",
            "issue_type": "BALANCE_DISAGREES_WITH_LEDGER",
            "expected_decision": "FLAG_FOR_REVIEW",
            "description": (
                "Synthetic negative test fixture; reconciliation "
                "must detect a deliberately altered expected balance."
            )
        })

    # ---------------------------------------------------------
    # Write generated tables
    # ---------------------------------------------------------
    data = {
        "Student": students_rows,
        "Program": programs,
        "FeeSchedule": fees,
        "Enrollment": enrollments,
        "Invoice": invoices_rows,
        "InvoiceLine": lines_rows,
        "Scholarship": scholarship_rows,
        "Eligibility": eligibility_rows,
        "Payment": payments_rows,
        "PaymentAllocation": allocations_rows,
        "Refund": refunds_rows,
        "LedgerEvent": ledger_rows
    }

    for table, rows in data.items():
        write_csv(
            output_dir / f"{table.lower()}.csv",
            rows
        )

    write_csv(
        output_dir / "ground_truth.csv",
        ground_truth
    )

    manifest = {
        "generator": "app.generator.generate_dataset",
        "seed": seed,
        "term_id": TERM_ID,
        "generated_on": "2026-10-28",
        "synthetic_only": True,
        "anomalies_enabled": anomalies,
        "row_counts": {
            table: len(rows)
            for table, rows in data.items()
        },
        "ground_truth_rows": len(ground_truth)
    }

    (
        output_dir / "source_manifest.json"
    ).write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8"
    )

    return manifest


def checksums(directory: Path):
    """Calculate SHA-256 checksums for generated CSV files."""

    result = {}

    for path in sorted(Path(directory).glob("*.csv")):
        result[path.name] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic tuition data"
    )

    parser.add_argument("--students", type=int, default=100)
    parser.add_argument("--invoices", type=int, default=300)
    parser.add_argument("--payments", type=int, default=500)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", default=str(SAMPLE_DIR))
    parser.add_argument(
        "--no-anomalies",
        action="store_true"
    )

    args = parser.parse_args()

    manifest = generate_dataset(
        students=args.students,
        invoices=args.invoices,
        payments=args.payments,
        seed=args.seed,
        output_dir=args.output,
        anomalies=not args.no_anomalies
    )

    print(json.dumps(manifest, indent=2))
    print("Checksums:")
    print(json.dumps(checksums(Path(args.output)), indent=2))


if __name__ == "__main__":
    main()
