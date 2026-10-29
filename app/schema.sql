PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS Student (
    student_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    residency_status TEXT NOT NULL CHECK(residency_status IN ('DOMESTIC','INTERNATIONAL')),
    household_income_band TEXT NOT NULL CHECK(household_income_band IN ('LOW','MEDIUM','HIGH')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Program (
    program_id TEXT PRIMARY KEY,
    program_name TEXT NOT NULL UNIQUE,
    department TEXT NOT NULL,
    active INTEGER NOT NULL CHECK(active IN (0,1))
);

CREATE TABLE IF NOT EXISTS FeeSchedule (
    fee_schedule_id TEXT PRIMARY KEY,
    program_id TEXT NOT NULL REFERENCES Program(program_id),
    term_id TEXT NOT NULL,
    fee_code TEXT NOT NULL,
    fee_name TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0),
    scholarship_eligible INTEGER NOT NULL CHECK(scholarship_eligible IN (0,1)),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    UNIQUE(program_id, term_id, fee_code)
);

CREATE TABLE IF NOT EXISTS Enrollment (
    enrollment_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES Student(student_id),
    program_id TEXT NOT NULL REFERENCES Program(program_id),
    term_id TEXT NOT NULL,
    enrollment_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('ACTIVE','WITHDRAWN','CANCELLED')),
    withdrawn_at TEXT,
    UNIQUE(student_id, program_id, term_id)
);

CREATE TABLE IF NOT EXISTS Invoice (
    invoice_id TEXT PRIMARY KEY,
    enrollment_id TEXT NOT NULL REFERENCES Enrollment(enrollment_id),
    student_id TEXT NOT NULL REFERENCES Student(student_id),
    term_id TEXT NOT NULL,
    invoice_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('OPEN','PARTIALLY_PAID','PAID','OVERDUE','CANCELLED')),
    issue_type TEXT NOT NULL DEFAULT 'NONE'
);

CREATE TABLE IF NOT EXISTS InvoiceLine (
    invoice_line_id TEXT PRIMARY KEY,
    invoice_id TEXT NOT NULL REFERENCES Invoice(invoice_id),
    fee_schedule_id TEXT REFERENCES FeeSchedule(fee_schedule_id),
    line_code TEXT NOT NULL,
    description TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount >= 0 OR line_type = 'WAIVER'),
    scholarship_eligible INTEGER NOT NULL CHECK(scholarship_eligible IN (0,1)),
    line_type TEXT NOT NULL CHECK(line_type IN ('TUITION','FEE','WAIVER','LATE_FEE','ADJUSTMENT'))
);

CREATE TABLE IF NOT EXISTS Scholarship (
    scholarship_id TEXT PRIMARY KEY,
    scholarship_name TEXT NOT NULL,
    term_id TEXT NOT NULL,
    award_type TEXT NOT NULL CHECK(award_type IN ('PERCENT','FIXED')),
    award_value REAL NOT NULL CHECK(award_value >= 0),
    min_income_band TEXT NOT NULL CHECK(min_income_band IN ('LOW','MEDIUM','HIGH')),
    required_residency TEXT CHECK(required_residency IN ('DOMESTIC','INTERNATIONAL')),
    active INTEGER NOT NULL CHECK(active IN (0,1))
);

CREATE TABLE IF NOT EXISTS Eligibility (
    eligibility_id TEXT PRIMARY KEY,
    scholarship_id TEXT NOT NULL REFERENCES Scholarship(scholarship_id),
    student_id TEXT NOT NULL REFERENCES Student(student_id),
    enrollment_id TEXT NOT NULL REFERENCES Enrollment(enrollment_id),
    eligible INTEGER NOT NULL CHECK(eligible IN (0,1)),
    eligible_fee_amount REAL NOT NULL CHECK(eligible_fee_amount >= 0),
    award_amount REAL NOT NULL CHECK(award_amount >= 0),
    decision_reason TEXT NOT NULL,
    decided_at TEXT NOT NULL,
    UNIQUE(scholarship_id, enrollment_id)
);

CREATE TABLE IF NOT EXISTS Payment (
    payment_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES Student(student_id),
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    method TEXT NOT NULL CHECK(method IN ('CARD','BANK_TRANSFER','UPI','CASH')),
    status TEXT NOT NULL CHECK(status IN ('SETTLED','PENDING','FAILED','REFUNDED')),
    external_reference TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS PaymentAllocation (
    allocation_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL REFERENCES Payment(payment_id),
    invoice_id TEXT NOT NULL REFERENCES Invoice(invoice_id),
    invoice_line_id TEXT NOT NULL REFERENCES InvoiceLine(invoice_line_id),
    amount REAL NOT NULL CHECK(amount > 0),
    allocated_at TEXT NOT NULL,
    issue_type TEXT NOT NULL DEFAULT 'NONE'
);

CREATE TABLE IF NOT EXISTS Refund (
    refund_id TEXT PRIMARY KEY,
    payment_id TEXT NOT NULL REFERENCES Payment(payment_id),
    student_id TEXT NOT NULL REFERENCES Student(student_id),
    refund_date TEXT NOT NULL,
    amount REAL NOT NULL CHECK(amount > 0),
    reason TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('REQUESTED','APPROVED','PAID','REJECTED')),
    issue_type TEXT NOT NULL DEFAULT 'NONE'
);

CREATE TABLE IF NOT EXISTS LedgerEvent (
    event_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES Student(student_id),
    invoice_id TEXT REFERENCES Invoice(invoice_id),
    event_type TEXT NOT NULL,
    amount REAL NOT NULL,
    event_date TEXT NOT NULL,
    source_id TEXT NOT NULL,
    notes TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_enrollment_student_term ON Enrollment(student_id, term_id);
CREATE INDEX IF NOT EXISTS idx_invoice_student ON Invoice(student_id);
CREATE INDEX IF NOT EXISTS idx_allocation_invoice ON PaymentAllocation(invoice_id);
CREATE INDEX IF NOT EXISTS idx_payment_student ON Payment(student_id);
