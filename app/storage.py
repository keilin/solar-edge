import csv
from pathlib import Path

DATA_FILE = Path("data/production.csv")

FIELDNAMES = [
    "date",
    "period",
    "energy_kwh",
    "source",
]


class ProductionStore:
    def __init__(self, path=DATA_FILE):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _records(self):
        if not self.path.exists():
            return []

        with self.path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def append(self, record):
        records = self._records()

        key = (
            record["date"],
            record["period"],
            record["source"],
        )

        for existing in records:
            existing_key = (
                existing["date"],
                existing.get("period", ""),
                existing["source"],
            )
            if existing_key == key:
                # Historical backfills can contain provisional zeros. Replace
                # them when a later daily monitor call returns the actual value.
                try:
                    unchanged = float(existing["energy_kwh"]) == float(record["energy_kwh"])
                except (TypeError, ValueError):
                    unchanged = existing["energy_kwh"] == str(record["energy_kwh"])

                if unchanged:
                    return

                existing["energy_kwh"] = str(record["energy_kwh"])
                with self.path.open("w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
                    writer.writeheader()
                    writer.writerows(records)
                return

        records.append({field: str(record[field]) for field in FIELDNAMES})
        with self.path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
            writer.writerows(records)

    def import_csv(self, source):
        with open(source, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.append(
                    {
                        "date": row["month"],
                        "period": "month",
                        "energy_kwh": row["energy_kwh"],
                        "source": "legacy",
                    }
                )
