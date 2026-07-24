import csv
from pathlib import Path

DATA_FILE = Path("data/production.csv")


class ProductionStore:
    def __init__(self, path=DATA_FILE):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)

    def append(self, record):
        existing = set()
        if self.path.exists():
            with self.path.open() as f:
                for row in csv.DictReader(f):
                    existing.add((row["date"], row["source"]))

        key = (record["date"], record["source"])
        if key in existing:
            return

        exists = self.path.exists()
        with self.path.open("a", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["date", "energy_kwh", "source"],
            )
            if not exists:
                writer.writeheader()
            writer.writerow(record)

    def import_csv(self, source):
        with open(source) as f:
            for row in csv.DictReader(f):
                self.append({
                    "date": row["month"],
                    "energy_kwh": row["energy_kwh"],
                    "source": "legacy",
                })
