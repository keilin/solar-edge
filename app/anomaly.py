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

                energy = float(row["energy_kwh"])

                if energy > 0:
                    months[row["date"][5:7]].append(energy)

        results = []

        for month, values in months.items():

            # Need at least 3 historical comparisons
            if len(values) < 4:
                continue

            current = values[-1]
            history = values[:-1]

            avg = sum(history) / len(history)

            if current < avg * 0.75:
                results.append(
                    {
                        "month": month,
                        "actual": current,
                        "average": round(avg, 1),
                    }
                )
        return results
