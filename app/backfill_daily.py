from datetime import date, timedelta

from app.solaredge import SolarEdgeClient
from app.storage import ProductionStore

START_DATE = date(2017, 3, 1)


def _energy_values(result):
    """Normalize the V2 energy response and reject unexpected shapes."""
    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected SolarEdge energy response type: {type(result).__name__}")
    values = result.get("values")
    if not isinstance(values, list):
        raise RuntimeError(
            "SolarEdge energy response has no 'values' list; "
            f"top-level keys: {sorted(result.keys())}"
        )
    return values, result.get("unit", "Wh")


def _value_to_kwh(value, unit):
    number = float(value)
    normalized = str(unit).strip().lower()
    if normalized in ("wh", "watt-hours"):
        return number / 1000
    if normalized in ("kwh", "kilowatt-hours"):
        return number
    raise RuntimeError(f"Unsupported SolarEdge energy unit: {unit!r}")


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
    numeric_values = 0

    while cursor <= end_date:
        # Keep requests to one calendar month. The V2 API has been verified
        # with month-long ranges; larger historical ranges returned HTTP 400.
        if cursor.month == 12:
            next_month = date(cursor.year + 1, 1, 1)
        else:
            next_month = date(cursor.year, cursor.month + 1, 1)
        chunk_end = min(next_month - timedelta(days=1), end_date)
        result = client.energy(cursor.isoformat(), chunk_end.isoformat(), "DAY")
        values, unit = _energy_values(result)

        valid_in_chunk = 0
        null_in_chunk = 0
        for item in values:
            if not isinstance(item, dict):
                continue

            # SolarEdge V2 returns ISO-8601 timestamps, not a "date" field.
            raw_date = item.get("timestamp") or item.get("date")
            value = item.get("value")
            if value is None:
                null_in_chunk += 1
                continue
            if not raw_date:
                raise RuntimeError(f"SolarEdge returned a numeric value without a date or timestamp: {item!r}")

            day = str(raw_date)[:10]
            energy_kwh = _value_to_kwh(value, unit)
            key = (day, "day", "solaredge")
            fetched += 1
            numeric_values += 1
            valid_in_chunk += 1

            if key in existing:
                continue

            store.append({
                "date": day,
                "period": "day",
                "energy_kwh": energy_kwh,
                "source": "solaredge",
            })
            existing.add(key)
            inserted += 1

        print(
            f"Retrieved {cursor} through {chunk_end}: {len(values)} records; "
            f"{valid_in_chunk} numeric, {null_in_chunk} null; unit={unit!r}"
        )
        if values and valid_in_chunk == 0:
            print(f"Sample SolarEdge record: {values[0]!r}")
            print(f"Response keys: {sorted(result.keys())}")
        cursor = chunk_end + timedelta(days=1)

    if numeric_values == 0:
        raise RuntimeError(
            "SolarEdge returned no numeric daily energy values across the entire "
            "backfill range. No successful backfill can be claimed."
        )

    print(f"Daily backfill complete: {fetched} numeric values, {inserted} new records added.")


if __name__ == "__main__":
    main()
