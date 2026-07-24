import csv
from collections import defaultdict
from datetime import date


SYSTEM_SIZE_KWP = 3.97


class Analytics:
    def __init__(self, path="data/production.csv"):
        self.path = path

    def _monthly_records(self):
        """
        Returns:
        {
            "2026-01": 271.529,
            "2026-02": 288.034,
            ...
        }

        Prefers SolarEdge records over legacy imports when duplicates exist.
        """
        records = {}

        with open(self.path) as f:
            for row in csv.DictReader(f):
                if row.get("period") != "month":
                    continue

                date_key = row["date"][:7]
                source = row.get("source", "")

                value = float(row["energy_kwh"])

                # Prefer API data over legacy spreadsheet data
                if date_key not in records:
                    records[date_key] = (value, source)
                elif source == "solaredge":
                    records[date_key] = (value, source)

        return {
            month: value[0]
            for month, value in records.items()
        }

    def monthly_average(self):
        """
        Average production by calendar month.
        """
        months = defaultdict(list)

        for key, value in self._monthly_records().items():
            month = key[5:7]
            months[month].append(value)

        return {
            month: round(sum(values) / len(values), 1)
            for month, values in sorted(months.items())
        }

    def current_year_vs_average(self):
        """
        Compare current year monthly production
        against historical monthly averages.
        """
        current_year = str(date.today().year)

        averages = self.monthly_average()
        records = self._monthly_records()

        result = {}

        for key, value in records.items():
            if not key.startswith(current_year):
                continue

            month = key[5:7]

            if month not in averages:
                continue

            expected = averages[month]

            result[month] = {
                "actual": round(value, 1),
                "average": round(expected, 1),
                "deviation_pct": round(
                    ((value - expected) / expected) * 100,
                    1,
                ),
                "percent_of_expected": round(
                    (value / expected) * 100,
                    1,
                ),
            }

        return result

    def annual_summary(self):
        """
        Annual production summary including
        specific yield (kWh/kWp).
        """
        years = defaultdict(float)

        for key, value in self._monthly_records().items():
            years[key[:4]] += value

        result = {}

        current_year = str(date.today().year)

        complete_years = {
            year: value
            for year, value in years.items()
            if year != current_year
        }
        
        lifetime_average = (
            sum(complete_years.values())
            / len(complete_years)
            if complete_years
            else 0
        )

        for year, energy in sorted(years.items()):
            result[year] = {
                "energy_kwh": round(energy, 1),
                "specific_yield": round(
                    energy / SYSTEM_SIZE_KWP,
                    1,
                ),
                "vs_average_pct": round(
                    ((energy - lifetime_average) / lifetime_average)
                    * 100,
                    1,
                ),
            }

        return result

    def summary(self):
        return {
            "monthly_average": self.monthly_average(),
            "current_year_vs_average": self.current_year_vs_average(),
            "annual_summary": self.annual_summary(),
        }


if __name__ == "__main__":
    import json

    print(json.dumps(
        Analytics().summary(),
        indent=2
    ))
