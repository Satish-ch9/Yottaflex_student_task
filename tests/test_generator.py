import csv
from app.generator import generate_dataset
from app.validation import validate_dataset

def test_generator_creates_files_and_valid_foreign_keys(tmp_path):
    generate_dataset(students=12, invoices=25, payments=30, seed=20261022, output_dir=tmp_path, anomalies=False)
    result = validate_dataset(tmp_path)
    assert result["valid"], result["errors"][:5]
    with (tmp_path / "student.csv").open(encoding="utf-8") as f:
        assert len(list(csv.DictReader(f))) == 12

def test_seed_is_reproducible(tmp_path):
    out1, out2 = tmp_path / "one", tmp_path / "two"
    generate_dataset(8, 12, 15, 20261022, out1, False)
    generate_dataset(8, 12, 15, 20261022, out2, False)
    assert (out1 / "student.csv").read_bytes() == (out2 / "student.csv").read_bytes()
    assert (out1 / "invoice.csv").read_bytes() == (out2 / "invoice.csv").read_bytes()
