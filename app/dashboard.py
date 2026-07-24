import csv
import json
from collections import defaultdict
from pathlib import Path

from app.performance import Performance
from app.anomaly import AnomalyDetector


def build_dashboard(
    input_file="data/production.csv",
    output_file="docs/dashboard.json",
):
    monthly = defaultdict(dict)
    records = []

    with open(input_file) as f:
        for row in csv.DictReader(f):

            # Support old schema
            if "period" not in row:
                row["period"] = (
                    "month"
                    if row["source"] == "legacy"
                    else "day"
                )

            records.append(row)

            if row["period"] == "month":
                year = row["date"][:4]
                month = row["date"][5:7]

                monthly[year][month] = float(
                    row["energy_kwh"]
                )

    data = {
        "records": records,
        "count": len(records),
        "monthly": dict(monthly),
        "annual": Performance().annual(),
        "specific_yield": Performance().annual_specific_yield(),
        "anomalies": AnomalyDetector().monthly_anomalies(),
    }

    Path(output_file).parent.mkdir(
        exist_ok=True
    )

    Path(output_file).write_text(
        json.dumps(data, indent=2)
    )


if __name__ == "__main__":
    build_dashboard()
