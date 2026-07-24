from app.solaredge import SolarEdgeClient
from app.storage import ProductionStore
from datetime import date
import json


def main():
    client = SolarEdgeClient()
    store = ProductionStore()

    today = date.today().isoformat()

    result = client.daily_energy(today)

    energy_wh = 0
    energy_kwh = 0

    if isinstance(result, dict):
        values = result.get("values", [])
        if values:
            energy_wh = values[0].get("value", 0)
            energy_kwh = energy_wh / 1000

    store.append(
        {
            "date": today,
            "period": "day",
            "energy_kwh": energy_kwh,
            "source": "solaredge",
        }
    )

    print(
        json.dumps(
            {
                "date": today,
                "energy_kwh": energy_kwh,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
