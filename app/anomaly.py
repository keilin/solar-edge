import csv
from collections import defaultdict


class AnomalyDetector:

    def __init__(self, path="data/production.csv"):
        self.path = path

    def monthly_anomalies(self):
        months = defaultdict(list)

        with open(self.path) as f:
            for row in csv.DictReader(f):

                if "period" not in row:
                    period = (
                        "month"
                        if row["source"] == "legacy"
                        else "day"
                    )
                else:
                    period = row["period"]

                if period != "month":
                    continue

                months[row["date"][5:7]].append(
                    float(row["energy_kwh"])
                )

        results = []

        for month, values in months.items():
            if len(values) < 3:
                continue

            avg = sum(values[:-1]) / len(values[:-1])

            if values[-1] < avg * 0.75:
                results.append({
                    "month": month,
                    "actual": values[-1],
                    "average": round(avg, 1),
                })

        return results
