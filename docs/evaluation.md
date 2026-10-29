# Evaluation plan

Report metrics from the actual generated dataset rather than hard-coding expected results.

- Referential integrity pass rate: valid foreign-key references / total non-empty references.
- Primary-key uniqueness: unique IDs / total IDs per entity.
- Invoice balance reconciliation rate: invoices whose computed balance is non-negative / total invoices.
- Exception detection precision/recall: compare detected exception IDs/types against `ground_truth.csv`; do not expose ground truth to the detector.
- Coverage: counts for partial payments, overpayments, waivers, withdrawals, duplicate invoices, refund exceptions, and balance-mismatch fixtures.
- Reproducibility: identical SHA-256 checksums for two runs with the same seed and version.

A detected exception is not automatically a confirmed fraud event; it is a record requiring review.
