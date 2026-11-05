from datetime import date, timedelta

from app.solaredge import SolarEdgeClient
from app.storage import ProductionStore

# Solar installation was commissioned in March 2017. SolarEdge returns only
# dates for which it has data, so starting slightly before commissioning is safe.
START_DATE = date(2017, 3, 1)


def main():
    client = SolarEdgeClient()
    store = ProductionStore()
    existing = {
        (row["date"], row.get("period", ""), row["source"])
        for row in store._records()
    }

    end_date = date.today() - timedelta(days=1)
    cursor = START_DATE
    fetched = 0
    inserted = 0

    # Keep requests to one calendar year to avoid oversized API responses.
    while cursor <= end_date:
        chunk_end = min(date(cursor.year, 12, 31), end_date)
        result = client.energy(cursor.isoformat(), chunk_end.isoformat(), "DAY")
        values = result.get("values", []) if isinstance(result, dict) else []

        for item in values:
            raw_date = item.get("date")
            value = item.get("value")
            if not raw_date or value is None:
                continue

            day = str(raw_date)[:10]
            key = (day, "day", "solaredge")
            fetched += 1
            if key in existing:
                continue

            store.append({
                "date": day,
                "period": "day",
                "energy_kwh": float(value) / 1000,
                "source": "solaredge",
            })
            existing.add(key)
            inserted += 1

        print(f"Retrieved {cursor} through {chunk_end}: {len(values)} API values")
        cursor = chunk_end + timedelta(days=1)

    print(f"Daily backfill complete: {fetched} values returned, {inserted} new records added.")


if __name__ == "__main__":
    main()
