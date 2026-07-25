# SolarEdge Monitor

Automated SolarEdge production tracking using GitHub Actions.

## Setup

Add repository secrets:

- `SOLAREDGE_SITE_ID`
- `SOLAREDGE_API_KEY`

## Running

The GitHub Action runs daily, appends to `data/production.csv`, and rebuilds
`docs/dashboard.json` from it. `data/production.csv` is the single source of
truth for both persistence and dashboard generation.
