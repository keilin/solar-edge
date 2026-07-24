import csv
import json
from pathlib import Path

from app.performance import Performance
from app.anomaly import AnomalyDetector


def build_dashboard(
    input_file="data/production.csv",
    output_file="docs/dashboard.json",
):

    records = []

    with open(input_file) as f:
        records = list(csv.DictReader(f))

    data = {
        "records": records,
        "count": len(records),
        "annual": Performance().annual(),
        "yield": Performance().annual_specific_yield(),
        "anomalies": AnomalyDetector().monthly_anomalies(),
    }

    Path(output_file).write_text(
        json.dumps(data, indent=2)
    )


if __name__ == "__main__":
    build_dashboard()
