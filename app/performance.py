import csv
from collections import defaultdict

SYSTEM_SIZE_KWP = 3.97


class Performance:

    def __init__(self, path="data/production.csv"):
        self.path = path

    def annual(self):
        totals = defaultdict(float)

        with open(self.path) as f:
            for row in csv.DictReader(f):
                year = row["date"][:4]
                totals[year] += float(row["energy_kwh"])

        return dict(totals)

    def annual_specific_yield(self):
        return {
            year: round(kwh / SYSTEM_SIZE_KWP, 1)
            for year, kwh in self.annual().items()
        }
