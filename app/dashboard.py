import csv
import json
from pathlib import Path


def build_dashboard(input_file="data/production.csv", output_file="data/dashboard.json"):
    records = []
    path = Path(input_file)
    if path.exists():
        with path.open() as f:
            records = list(csv.DictReader(f))

    Path(output_file).write_text(json.dumps({
        "records": records,
        "count": len(records)
    }, indent=2))


if __name__ == "__main__":
    build_dashboard()
