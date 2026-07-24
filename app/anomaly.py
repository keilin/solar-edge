import csv
from collections import defaultdict


class AnomalyDetector:

    def __init__(self, path="data/production.csv"):
        self.path = path

    def monthly_anomalies(self):
        months = defaultdict(list)

        with open(self.path) as f:
            for row in csv.DictReader(f):
                if row["period"] != "month":
                    continue

                key = row["date"][5:7]
                months[key].append(
                    float(row["energy_kwh"])
                )

        results = []

        for month, values in months.items():
            if len(values) < 3:
                continue

            avg = sum(values[:-1]) / len(values[:-1])
            current = values[-1]

            if current < avg * 0.75:
                results.append(
                    {
                        "month": month,
                        "actual": current,
                        "average": round(avg, 1),
                    }
                )

        return results
