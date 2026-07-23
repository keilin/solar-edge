from app.solaredge import SolarEdgeClient
from datetime import date
import json


def main():
    client = SolarEdgeClient()
    result = {
        "date": str(date.today()),
        "overview": client.overview(),
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
