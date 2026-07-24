import csv
from pathlib import Path

DATA_FILE = Path("data/production.csv")


class ProductionStore:
    def __init__(self, path=DATA_FILE):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)

    def _records(self):
        if not self.path.exists():
            return []

        with self.path.open() as f:
            return list(csv.DictReader(f))

    def append(self, record):
        records = self._records()

        key = (
            record["date"],
            record["period"],
            record["source"],
        )

        existing = {
            (
                r["date"],
                r.get("period", ""),
                r["source"],
            )
            for r in records
        }

        if key in existing:
            return

        exists = self.path.exists()

        with self.path.open("a", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "date",
                    "period",
                    "energy_kwh",
                    "source",
                ],
            )

            if not exists:
                writer.writeheader()

            writer.writerow(record)

    def import_csv(self, source):
        with open(source) as f:
            for row in csv.DictReader(f):
                self.append(
                    {
                        "date": f"{row['month']}-01",
                        "period": "month",
                        "energy_kwh": row["energy_kwh"],
                        "source": "legacy",
                    }
                )
