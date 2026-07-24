from collections import defaultdict
import csv

SYSTEM_SIZE_KWP = 3.97


class Performance:

    def __init__(self, path="data/production.csv"):
        self.path = path

    def _records(self):
        records = []

        with open(self.path) as f:
            reader = csv.DictReader(f)

            for row in reader:

                # Handle old schema:
                # date,energy_kwh,source
                if "period" not in row:
                    row = {
                        "date": row["date"],
                        "period": (
                            "month"
                            if row["source"] == "legacy"
                            else "day"
                        ),
                        "energy_kwh": row["energy_kwh"],
                        "source": row["source"],
                    }

                records.append(row)

        return records

    def annual(self):
        totals = defaultdict(float)

        for row in self._records():
            totals[row["date"][:4]] += float(
                row["energy_kwh"]
            )

        return dict(totals)

    def annual_specific_yield(self):
        return {
            year: round(kwh / SYSTEM_SIZE_KWP, 1)
            for year, kwh in self.annual().items()
        }
