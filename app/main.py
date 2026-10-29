from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from app.config import SAMPLE_DIR
from app.generator import generate_dataset
from app.reconciliation import reconcile
from app.validation import validate_dataset

app = FastAPI(
    title="Tuition & Scholarship Reconciliation API",
    description="Synthetic student billing, scholarship, payment and reconciliation workflow.",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"name":"Tuition & Scholarship Reconciliation System",
            "docs":"/docs",
            "health":"/health"}

@app.get("/health")
def health():
    return {"status":"ok"}

@app.post("/generate")
def generate(students: int = Query(100, ge=1, le=10000),
             invoices: int = Query(300, ge=1, le=30000),
             payments: int = Query(500, ge=1, le=50000),
             seed: int = Query(20261022),
             anomalies: bool = True):
    manifest = generate_dataset(students, invoices, payments, seed, SAMPLE_DIR, anomalies)
    return {"message":"Synthetic dataset generated", "manifest":manifest}

@app.get("/validate")
def validate():
    result = validate_dataset(SAMPLE_DIR)
    return result

@app.get("/reconcile")
def reconciliation():
    if not (SAMPLE_DIR / "invoice.csv").exists():
        raise HTTPException(status_code=404, detail="Generate the dataset first using POST /generate")
    return reconcile(SAMPLE_DIR)

@app.get("/metrics")
def metrics():
    if not (SAMPLE_DIR / "invoice.csv").exists():
        raise HTTPException(status_code=404, detail="Generate the dataset first using POST /generate")
    return reconcile(SAMPLE_DIR)["metrics"]

@app.get("/exceptions")
def exceptions():
    if not (SAMPLE_DIR / "invoice.csv").exists():
        raise HTTPException(status_code=404, detail="Generate the dataset first using POST /generate")
    return {"exceptions": reconcile(SAMPLE_DIR)["exceptions"]}
