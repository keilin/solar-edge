# SolarEdge Monitor v2

New implementation of the SolarEdge production monitor.

## Design

- Use `data/production.csv` as the source of truth.
- Keep historical monthly production imported from the legacy spreadsheet.
- Collect new production data with GitHub Actions.
- Generate dashboard data from the complete production history.
- No legacy storage importer required.

## Migration

Historical data should be copied into `data/production.csv` with monthly records preserved.
