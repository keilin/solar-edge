import csv
import json
from collections import defaultdict
from datetime import date
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

    daily = sorted(
        (row for row in records if row["period"] == "day"),
        key=lambda row: row["date"],
    )

    week = [
        {
            "date": row["date"],
            "energy_kwh": float(row["energy_kwh"]),
        }
        for row in daily[-7:]
    ]

    today = date.today()
    current_year = str(today.year)
    current_month = today.strftime("%m")

    this_month_kwh = monthly.get(current_year, {}).get(current_month, 0)
    this_year_kwh = sum(monthly.get(current_year, {}).values())
    lifetime_kwh = sum(v for year in monthly.values() for v in year.values())

    last_date = max(
        (r["date"] for r in records),
        default=None,
    )

    data = {
        "records": records,
        "count": len(records),
        "monthly": dict(monthly),
        "week": week,
        "summary": {
            "this_month_kwh": round(this_month_kwh, 1),
            "this_year_kwh": round(this_year_kwh, 1),
            "lifetime_kwh": round(lifetime_kwh, 1),
            "last_date": last_date,
        },
        "annual": Performance().annual(),
        "specific_yield": Performance().annual_specific_yield(),
        "anomalies": AnomalyDetector().monthly_anomalies(),
        "analytics": Analytics().summary(),
    }

    Path(output_file).parent.mkdir(exist_ok=True)
    Path(output_file).write_text(json.dumps(data, indent=2))


if __name__ == "__main__":
    build_dashboard()
