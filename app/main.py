from app.solaredge import SolarEdgeClient
from app.storage import ProductionStore
from datetime import date, timedelta
import json


def _refresh_completed_months(client, store, today):
    """Refresh all completed months in the current calendar year."""
    current_month = date(today.year, today.month, 1)
    start_day = date(today.year, 1, 1)
    end_day = current_month - timedelta(days=1)

    result = client.monthly_energy(start_day.isoformat(), end_day.isoformat())
    values = result.get("values", []) if isinstance(result, dict) else []
    refreshed = []

    for item in values:
        if not isinstance(item, dict) or item.get("value") is None:
            continue
        raw_date = item.get("timestamp") or item.get("date")
        if not raw_date:
            continue
        month = str(raw_date)[:7]
        energy_kwh = float(item["value"]) / 1000
        store.append({
            "date": month,
            "period": "month",
            "energy_kwh": energy_kwh,
            "source": "solaredge",
        })
        refreshed.append({"month": month, "energy_kwh": energy_kwh})

    return refreshed

def main():
    client = SolarEdgeClient()
    store = ProductionStore()

    # Capture the previous completed day and refresh the preceding week.
    # Historical API values can initially be provisional zeros; revisiting
    # recent dates lets later readings replace those values.
    end_day = date.today() - timedelta(days=1)
    start_day = end_day - timedelta(days=6)
    result = client.energy(start_day.isoformat(), end_day.isoformat(), "DAY")

    daily_values = result.get("values", []) if isinstance(result, dict) else []
    captured = []
    for item in daily_values:
        if not isinstance(item, dict):
            continue
        raw_date = item.get("timestamp") or item.get("date")
        value = item.get("value")
        if not raw_date or value is None:
            continue

        day = str(raw_date)[:10]
        energy_kwh = float(value) / 1000
        store.append(
            {
                "date": day,
                "period": "day",
                "energy_kwh": energy_kwh,
                "source": "solaredge",
            }
        )
        captured.append({"date": day, "energy_kwh": energy_kwh})

    # Backfill the three most recent completed months from SolarEdge's
    # monthly-resolution endpoint. Daily sums are not used because a few
    # historical daily readings may be absent.
    completed_months = _refresh_completed_months(client, store, date.today())

    month = end_day.strftime("%Y-%m")
    monthly = client.monthly_energy(f"{month}-01", end_day.isoformat())

    month_kwh = None
    if isinstance(monthly, dict):
        values = monthly.get("values", [])
        if values and values[0].get("value") is not None:
            month_kwh = float(values[0]["value"]) / 1000
            store.append(
                {
                    "date": month,
                    "period": "month",
                    "energy_kwh": month_kwh,
                    "source": "solaredge",
                }
            )

    print(json.dumps({
        "daily_values": captured,
        "completed_months": completed_months,
        "monthly_kwh": month_kwh,
    }, indent=2))


if __name__ == "__main__":
    main()
