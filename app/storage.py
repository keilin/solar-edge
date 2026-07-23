import csv
from pathlib import Path
from datetime import datetime

DATA_FILE = Path("data/production.csv")


class ProductionStore:
    def __init__(self, path=DATA_FILE):
        self.path = Path(path)
        self.path.parent.mkdir(exist_ok=True)

    def append(self, record):
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
                row["source"] = "legacy"
                self.append(row)
