from app.solaredge import SolarEdgeClient
from app.storage import ProductionStore
from datetime import date
import json


def main():
    client = SolarEdgeClient()
    store = ProductionStore()

    today = date.today().isoformat()

    result = client.daily_energy(today)

    energy_kwh = 0

    if isinstance(result, dict):
        values = result.get("values", [])
        if values:
            energy_kwh = float(values[0].get("value") or 0) / 1000

    store.append(
        {
            "date": today,
            "period": "day",
            "energy_kwh": energy_kwh,
            "source": "solaredge",
        }
    )

    month = today[:7]
    monthly = client.monthly_energy(
        f"{month}-01",
        today,
    )

    if isinstance(monthly, dict):
        values = monthly.get("values", [])
        if values:
            month_kwh = float(values[0].get("value") or 0) / 1000
            store.append(
                {
                    "date": month,
                    "period": "month",
                    "energy_kwh": month_kwh,
                    "source": "solaredge",
                }
            )

    print(json.dumps({
        "date": today,
        "energy_kwh": energy_kwh,
    }, indent=2))


if __name__ == "__main__":
    main()
