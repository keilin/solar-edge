import csv
import json
from collections import defaultdict
from pathlib import Path

from app.performance import Performance
from app.anomaly import AnomalyDetector
from app.analytics import Analytics

def build_dashboard(
    input_file="data/production.csv",
    output_file="docs/dashboard.json",
):
    monthly = defaultdict(dict)
    records = []

    with open(input_file) as f:
        for row in csv.DictReader(f):
            if "period" not in row:
                row["period"] = (
                    "month" if row.get("source") == "legacy" else "day"
                )

            records.append(row)

            if row["period"] == "month":
                key = row["date"][:7]
                monthly[key[:4]][key[5:7]] = float(row["energy_kwh"])

            elif row["period"] == "day":
                key = row["date"][:7]
                year = key[:4]
                month = key[5:7]
                monthly[year][month] = monthly[year].get(month, 0) + float(row["energy_kwh"])

    data = {
        "records": records,
        "count": len(records),
        "monthly": dict(monthly),
        "annual": Performance().annual(),
        "specific_yield": Performance().annual_specific_yield(),
        "anomalies": AnomalyDetector().monthly_anomalies(),
        "analytics": Analytics().summary(),
    }

    Path(output_file).parent.mkdir(exist_ok=True)
    Path(output_file).write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    build_dashboard()
