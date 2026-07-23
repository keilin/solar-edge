from app.solaredge import SolarEdgeClient
from app.storage import ProductionStore
from datetime import date
import json


def extract_energy(overview):
    data = overview.get("overview", {})
    return data.get("lastDayEnergy", {}).get("energy", 0)


def main():
    client = SolarEdgeClient()
    store = ProductionStore()

    overview = client.overview()
    energy = extract_energy(overview)

    store.append({
        "date": str(date.today()),
        "energy_kwh": energy,
        "source": "solaredge",
    })

    print(json.dumps({
        "date": str(date.today()),
        "energy_kwh": energy,
    }, indent=2))


if __name__ == "__main__":
    main()
