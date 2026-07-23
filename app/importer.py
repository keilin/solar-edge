from app.storage import ProductionStore


def import_legacy(path="data/import.csv"):
    store = ProductionStore()
    store.import_csv(path)


if __name__ == "__main__":
    import_legacy()
