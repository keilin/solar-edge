from collections import Counter

from app.solaredge import SolarEdgeClient


RANGES = (
    ("2017-03-01", "2017-03-31"),
    ("2025-03-01", "2025-03-31"),
)
RESOLUTION_PARAMS = ("timeUnit", "resolution")


def inspect(client, start_date, end_date, resolution_param):
    params = {
        "startDate": start_date,
        "endDate": end_date,
        resolution_param: "DAY",
    }
    result = client._get("energy", params)
    result = client._unwrap_energy(result)

    if not isinstance(result, dict) or not isinstance(result.get("values"), list):
        raise RuntimeError(
            f"Unexpected response for {params}: "
            f"{result!r}"
        )

    values = result["values"]
    timestamps = [
        str(item.get("timestamp") or item.get("date") or "<missing>")
        for item in values
        if isinstance(item, dict)
    ]
    months = Counter(ts[:7] for ts in timestamps if len(ts) >= 7)

    print(
        f"\nPARAMETER {resolution_param}=DAY; "
        f"REQUEST {start_date} through {end_date}"
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
        for resolution_param in RESOLUTION_PARAMS:
            inspect(client, start_date, end_date, resolution_param)


if __name__ == "__main__":
    main()
