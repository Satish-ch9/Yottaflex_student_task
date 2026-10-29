# Schema and lifecycle notes

The relational DDL is in `app/schema.sql`. It defines primary keys, foreign keys, allowed states, uniqueness constraints, and indexes.

## Lifecycle examples

- Enrollment: `ACTIVE -> WITHDRAWN` or `ACTIVE -> CANCELLED`.
- Payment: `PENDING -> SETTLED` or `PENDING -> FAILED`; a settled payment may later have partial refunds.
- Refund: `REQUESTED -> APPROVED -> PAID`, or `REQUESTED -> REJECTED`.
- Invoice: `OPEN -> PARTIALLY_PAID -> PAID`; unpaid invoices may become `OVERDUE`; cancelled invoices should retain their history.

Production implementations should enforce state transitions in service functions and append LedgerEvent rows for each transition. This challenge implementation retains source rows and event rows in generated CSVs, and demonstrates anomaly checks with explicit exception reports.
