from collections import Counter

from app.solaredge import SolarEdgeClient


RANGES = (
    ("2017-03-01", "2017-03-31"),
    ("2025-03-01", "2025-03-31"),
)

# The previous diagnostic established that "resolution=DAY" is recognized,
# while "startDate"/"endDate" are ignored by this V2 endpoint. Test plausible
# V2 date-range parameter pairs without changing the production client.
DATE_PARAMETER_PAIRS = (
    ("startDate", "endDate", "date"),
    ("startTime", "endTime", "datetime"),
    ("from", "to", "date"),
    ("start", "end", "date"),
    ("startDateTime", "endDateTime", "datetime"),
)


def format_value(value, kind):
    if kind == "datetime":
        return f"{value}T00:00:00Z"
    return value


def inspect(client, start_date, end_date, start_key, end_key, kind):
    params = {
        start_key: format_value(start_date, kind),
        end_key: format_value(end_date, kind),
        "resolution": "DAY",
    }
    label = f"{start_key}/{end_key}"

    try:
        result = client._get("energy", params)
        result = client._unwrap_energy(result)
    except Exception as exc:
        print(f"\nPARAMETERS {label}; REQUEST {start_date} through {end_date}")
        print(f"REQUEST ERROR: {type(exc).__name__}: {exc}")
        return

    if not isinstance(result, dict) or not isinstance(result.get("values"), list):
        print(f"\nPARAMETERS {label}; REQUEST {start_date} through {end_date}")
        print(f"UNEXPECTED RESPONSE: {result!r}")
        return

    values = result["values"]
    timestamps = [
        str(item.get("timestamp") or item.get("date") or "<missing>")
        for item in values
        if isinstance(item, dict)
    ]
    months = Counter(ts[:7] for ts in timestamps if len(ts) >= 7)

    print(
        f"\nPARAMETERS {label}; REQUEST {start_date} through {end_date}"
    )
    print(
        f"Response resolution={result.get('resolution')!r}; "
        f"period={result.get('period')!r}; unit={result.get('unit')!r}; "
        f"records={len(values)}"
    )
    print(
        f"Returned timestamp range: "
        f"{timestamps[0] if timestamps else 'none'} through "
        f"{timestamps[-1] if timestamps else 'none'}"
    )
    print(f"Returned months: {dict(sorted(months.items()))}")


def main():
    client = SolarEdgeClient()

    for start_date, end_date in RANGES:
        for start_key, end_key, kind in DATE_PARAMETER_PAIRS:
            inspect(
                client,
                start_date,
                end_date,
                start_key,
                end_key,
                kind,
            )


if __name__ == "__main__":
    main()
