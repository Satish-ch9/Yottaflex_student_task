# Data dictionary

All records are synthetic. Dates use ISO 8601 `YYYY-MM-DD`; monetary amounts are decimal currency units with two decimal places. IDs are immutable strings. Empty optional values are represented as empty CSV fields.

| Entity | Primary key | Important fields and validation |
|---|---|---|
| Student | `student_id` | `STU-000001`; unique email; residency `DOMESTIC/INTERNATIONAL`; income band `LOW/MEDIUM/HIGH`. |
| Program | `program_id` | `PRG-001`; unique program name; active is 0 or 1. |
| FeeSchedule | `fee_schedule_id` | References Program; term and fee code; amount >= 0; effective date range; scholarship eligibility boolean. |
| Enrollment | `enrollment_id` | References Student and Program; one enrollment per student/program/term in the intended domain; status `ACTIVE/WITHDRAWN/CANCELLED`; withdrawal date optional. |
| Invoice | `invoice_id` | References Enrollment and Student; term, invoice date, due date; status `OPEN/PARTIALLY_PAID/PAID/OVERDUE/CANCELLED`; `issue_type` is normally `NONE`. |
| InvoiceLine | `invoice_line_id` | References Invoice and optionally FeeSchedule; positive fee line or negative scholarship waiver; line type `TUITION/FEE/WAIVER/LATE_FEE/ADJUSTMENT`. |
| Scholarship | `scholarship_id` | `SCH-2026-000001`; award type `PERCENT/FIXED`; percent is 0-100 by policy; fixed award >= 0; term and eligibility criteria. |
| Eligibility | `eligibility_id` | References Scholarship, Student and Enrollment; eligible flag; eligible fee base and award amount >= 0; documented decision reason. |
| Payment | `payment_id` | `PAY-000001`; references Student; amount > 0; method `CARD/BANK_TRANSFER/UPI/CASH`; status `SETTLED/PENDING/FAILED/REFUNDED`; unique external reference. |
| PaymentAllocation | `allocation_id` | `ALLOC-<payment-id>-01`; references Payment, Invoice and InvoiceLine; amount > 0; allocation must not exceed settled payment or line balance. |
| Refund | `refund_id` | References Payment and Student; amount > 0; status `REQUESTED/APPROVED/PAID/REJECTED`; cumulative paid refunds cannot exceed net paid amount. |
| LedgerEvent | `event_id` | Immutable event history for invoice issue and allocation; references Student and optionally Invoice; source ID identifies originating transaction. |

## Relationships and cardinality

- Student 1:N Enrollment; Program 1:N Enrollment; Program 1:N FeeSchedule.
- Enrollment 1:N Invoice in the physical schema, but the intended business rule is one active invoice per enrollment and term; duplicate invoices are exceptions.
- Invoice 1:N InvoiceLine.
- Scholarship N:M Enrollment through Eligibility; Eligibility records both eligible and ineligible decisions.
- Payment 1:N PaymentAllocation; Invoice 1:N PaymentAllocation; InvoiceLine 1:N PaymentAllocation.
- Payment 1:N Refund, because a payment may be refunded in multiple partial transactions.
- Student 1:N Payment and Student 1:N Refund.
- LedgerEvent records state-changing events without overwriting prior events.

## Important policy choices

1. A scholarship applies only to eligible fee lines and is capped at eligible fees.
2. Only settled payments are available for allocation.
3. Allocations are auditable by payment, invoice, and invoice line.
4. Refund totals in `APPROVED` or `PAID` states must not exceed the payment's net paid amount.
5. A duplicate invoice is detected by enrollment and term; its row remains present and labelled for review.
6. Anomalies are explicit and labelled in `ground_truth.csv`. Negative test fixtures that would violate valid baseline accounting are documented there rather than silently mixed into ordinary records.
7. The generator uses synthetic example.edu emails and does not use external personal data.
