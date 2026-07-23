import csv
from collections import defaultdict
from pathlib import Path


class ProductionReport:
    def __init__(self, path="data/production.csv"):
        self.path = Path(path)

    def monthly_totals(self):
        totals = defaultdict(float)
        if not self.path.exists():
            return totals

        with self.path.open() as f:
            for row in csv.DictReader(f):
                month = row["date"][:7]
                totals[month] += float(row["energy_kwh"])

        return dict(totals)
