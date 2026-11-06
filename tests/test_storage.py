import csv
import tempfile
import unittest
from pathlib import Path

from app.storage import ProductionStore


class ProductionStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.path = Path(self.temp_dir.name) / "production.csv"
        self.store = ProductionStore(self.path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _read(self):
        with self.path.open(newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def test_append_updates_existing_record(self):
        record = {
            "date": "2026-11-05",
            "period": "day",
            "energy_kwh": 0.0,
            "source": "solaredge",
        }
        self.store.append(record)

        record["energy_kwh"] = 14.408
        self.store.append(record)

        rows = self._read()
        self.assertEqual(len(rows), 1)
        self.assertEqual(float(rows[0]["energy_kwh"]), 14.408)

    def test_append_adds_new_record(self):
        self.store.append({
            "date": "2026-11-05",
            "period": "day",
            "energy_kwh": 14.408,
            "source": "solaredge",
        })
        self.store.append({
            "date": "2026-11-06",
            "period": "day",
            "energy_kwh": 12.5,
            "source": "solaredge",
        })

        rows = self._read()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[1]["date"], "2026-11-06")

    def test_append_does_not_duplicate_unchanged_record(self):
        record = {
            "date": "2026-11-05",
            "period": "day",
            "energy_kwh": 14.408,
            "source": "solaredge",
        }
        self.store.append(record)
        self.store.append(record)

        self.assertEqual(len(self._read()), 1)


if __name__ == "__main__":
    unittest.main()
