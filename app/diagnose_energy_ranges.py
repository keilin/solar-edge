from collections import Counter
from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from app.solaredge import SolarEdgeClient


SITE_TIMEZONE = ZoneInfo("America/Los_Angeles")
RANGES = (
    ("2017-03-01", "2017-03-31"),
    ("2025-03-01", "2025-03-31"),
)

# SolarEdge V2 examples use "from"/"to" timestamps with an explicit local
# timezone offset, not the V1 "startDate"/"endDate" date-only parameters.
DATE_PARAMETER_PAIRS = (
    ("startDate", "endDate", "date"),
    ("startTime", "endTime", "datetime-z"),
    ("from", "to", "datetime-local"),
    ("start", "end", "date"),
    ("startDateTime", "endDateTime", "datetime-z"),
)


def format_value(value, kind, is_end=False):
    parsed = date.fromisoformat(value)
    if kind == "date":
        return value
    if kind == "datetime-z":
        suffix = "T23:59:59Z" if is_end else "T00:00:00Z"
        return value + suffix
    if kind == "datetime-local":
        clock = time(23, 59, 59) if is_end else time(0, 0, 0)
        return datetime.combine(parsed, clock, SITE_TIMEZONE).isoformat(timespec="seconds")
    raise ValueError(f"Unknown date format: {kind}")


def inspect(client, start_date, end_date, start_key, end_key, kind):
    params = {
        start_key: format_value(start_date, kind),
        end_key: format_value(end_date, kind, is_end=True),
        "resolution": "DAY",
        "unit": "WH",
    }
    label = f"{start_key}/{end_key} ({kind})"

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

    print(f"\nPARAMETERS {label}; REQUEST {start_date} through {end_date}")
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
