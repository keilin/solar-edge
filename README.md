# SolarEdge Monitor

Automated SolarEdge production tracking using GitHub Actions and the SolarEdge Monitoring API V2.

## GitHub Actions secrets

Add these repository secrets:

- `SOLAREDGE_SITE_ID`
- `SOLAREDGE_CLIENT_ID`
- `SOLAREDGE_CLIENT_SECRET`
- `SOLAREDGE_REFRESH_TOKEN`
- `GH_PAT`

`GH_PAT` is a fine-grained personal access token for this repository with Actions read/write permission. The workflow uses it to replace `SOLAREDGE_REFRESH_TOKEN` after SolarEdge rotates it. Do not use the ordinary `GITHUB_TOKEN` for this operation.

## Running

The GitHub Action runs daily, appends to `data/production.csv`, and rebuilds
`docs/dashboard.json` from it. `data/production.csv` is the single source of
truth for both persistence and dashboard generation.

Run the tests locally with:

```sh
python -m unittest discover -s tests -v
```
