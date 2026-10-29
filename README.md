# Tuition & Scholarship Reconciliation System

A reproducible synthetic-data and reconciliation project for student billing. It demonstrates master data generation, term fee schedules, enrollments, invoices and invoice lines, rule-based scholarship eligibility, payments, allocations, refunds, exception detection, validation, and API endpoints.

## Stack
- Python 3.10+
- FastAPI + Uvicorn
- CSV/JSON synthetic exports
- SQLite schema included in `app/schema.sql`
- Pytest

## Quick start (Windows PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.generator --students 100 --invoices 300 --payments 500 --seed 20261022
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## API
- `GET /health` — health check.
- `POST /generate?students=100&invoices=300&payments=500&seed=20261022` — generate dataset.
- `GET /validate` — primary-key and foreign-key validation.
- `GET /reconcile` — invoice balances and exception details.
- `GET /metrics` — measurable output metrics.
- `GET /exceptions` — anomaly list.

The generated CSVs are in `data/sample/`. Use `--output` to export to another directory. The default dataset is small for development; use the target scale command below for full data.

## Full target-scale generation

```powershell
python -m app.generator --students 10000 --invoices 30000 --payments 50000 --seed 20261022 --output data/exports
```

The specification calls for 15,000 scholarship awards. This generator creates scholarship eligibility/award decisions as derived records per invoice and scholarship, with award amount determined by eligibility rules; inspect `eligibility.csv` and count positive awards to report the realized award count rather than assuming a target. If you need exactly 15,000 positive awards, adjust the eligibility distribution and verify the resulting count before submission.

## Tests

```powershell
pytest -q
```

## Reproducibility

Run the same generator command twice with the same seed and compare the SHA-256 checksums printed at the end. Identical inputs, seed and code version should produce identical CSV content. `source_manifest.json` records the seed, generator, term, and row counts.

## Ground truth and anomaly handling

`ground_truth.csv` is separate from ordinary entity data. It labels expected exceptions such as allocation greater than payment, duplicate invoice, refund exceeding payment, scholarship exceeding eligible fees, and ledger/balance mismatch. The last two negative scenarios are isolated test fixtures, so they do not corrupt valid baseline transactions. Never use ground-truth labels as input features when evaluating a detector.

## Reconciliation rules

- Invoice net due = sum of invoice line amounts, including negative scholarship waiver lines, floored at zero for reporting.
- Allocated amount = sum of allocations to the invoice.
- Balance = net due - allocated amount.
- Payment allocation must not exceed the settled payment amount and must reference a line belonging to the same invoice.
- Refund total in approved/paid states must not exceed payment amount.
- Duplicate invoice candidates are identified by enrollment and term.
- Scholarship award must not exceed eligible fee amount.

## Limitations and extensions

This is a challenge starter, not a production student-finance platform. Before final submission, extend validation to all enum/date/arithmetic rules, add transaction service functions for cancellation/refund state transitions, and add the required full-volume checksums to the submission evidence. Monetary values are stored in decimal strings in CSV to avoid binary floating-point drift.
