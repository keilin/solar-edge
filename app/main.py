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
        print(values[0])
        if values:
            raw_value = values[0].get("value")

        if raw_value is None:
            energy_kwh = 0
        else:
            energy_kwh = float(raw_value) / 1000

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
