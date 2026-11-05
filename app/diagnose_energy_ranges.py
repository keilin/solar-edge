from collections import Counter

from app.solaredge import SolarEdgeClient


RANGES = (
    ("2017-03-01", "2017-03-31"),
    ("2025-03-01", "2025-03-31"),
)


def main():
    client = SolarEdgeClient()

    for start_date, end_date in RANGES:
        result = client.energy(start_date, end_date, "DAY")
        if not isinstance(result, dict):
            raise RuntimeError(
                f"Unexpected response for {start_date}..{end_date}: "
                f"{type(result).__name__}"
            )

        values = result.get("values")
        if not isinstance(values, list):
            raise RuntimeError(
                f"No values list for {start_date}..{end_date}; "
                f"response keys={sorted(result)}"
            )

        timestamps = [
            str(item.get("timestamp") or item.get("date") or "<missing>")
            for item in values
            if isinstance(item, dict)
        ]
        months = Counter(ts[:7] for ts in timestamps if len(ts) >= 7)
        print(
            f"\nREQUEST {start_date} through {end_date}: "
            f"{len(values)} records; unit={result.get('unit')!r}; "
            f"response keys={sorted(result)}"
        )
        print(
            f"Returned timestamp range: "
            f"{timestamps[0] if timestamps else 'none'} through "
            f"{timestamps[-1] if timestamps else 'none'}"
        )
        print(f"Returned months: {dict(sorted(months.items()))}")
        print(f"All returned timestamps: {timestamps}")


if __name__ == "__main__":
    main()
