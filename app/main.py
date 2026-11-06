from app.solaredge import SolarEdgeClient
from app.storage import ProductionStore
from datetime import date, timedelta
import json


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
        "monthly_kwh": month_kwh,
    }, indent=2))


if __name__ == "__main__":
    main()
