# SolarEdge Monitor

Automated SolarEdge production tracking using GitHub Actions.

## Setup

Add repository secrets:

- `SOLAREDGE_SITE_ID`
- `SOLAREDGE_API_KEY`

## Historical import

Convert the old spreadsheet export to:

```csv
month,energy_kwh
2024-01,350
```

Then use the storage importer to load history.

## Running

The GitHub Action runs daily and stores production history in `data/production.csv`.
