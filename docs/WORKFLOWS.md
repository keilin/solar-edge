# GitHub Actions workflow reference

This repository uses three GitHub Actions workflows.

## SolarEdge Monitor

**File:** `.github/workflows/monitor.yml`  
**Purpose:** Routine data collection and dashboard-data generation.

**Triggers**
- Daily at 08:15 UTC.
- Manually through **Actions → SolarEdge Monitor → Run workflow**.
- On pushes that change files under `app/`, `tests/`, or the monitor workflow itself.

**What it does**
1. Installs Python dependencies and runs the unit test suite.
2. Queries SolarEdge for daily production over the latest seven-day window. This revisits recent dates so later SolarEdge readings can replace provisional values.
3. Refreshes monthly production totals for the three most recently completed calendar months, plus the current month's total.
4. Rebuilds `docs/dashboard.json` from the production CSV.
5. Commits changed files under `data/` and `docs/`.

The rolling daily window and recent monthly refresh are intentional: SolarEdge data can be incomplete or provisional when first queried. The storage layer replaces an existing record when a newer value for the same date/period/source arrives.

## SolarEdge Daily History Backfill

**File:** `.github/workflows/backfill.yml`  
**Purpose:** Populate or repair the historical daily production series.

**Trigger:** Manual only, through **Actions → SolarEdge Daily History Backfill → Run workflow**.

The backfill requests daily data month by month, beginning March 1, 2017 and ending yesterday. It updates `data/production.csv`, rebuilds the dashboard data, and commits the result.

This is a maintenance operation, not a scheduled task. It can make many SolarEdge API requests, take several minutes, and encounter rate limiting. Do not run it just to refresh recent production; the monitor handles that.

## Deploy Dashboard

**File:** `.github/workflows/pages.yml`  
**Purpose:** Publish the generated dashboard.

**Triggers**
- Whenever the SolarEdge Monitor workflow completes.
- Manually through **Actions → Deploy Dashboard → Run workflow**.

On a successful monitor run, it checks out the repository, packages the `docs/` directory, and deploys it to GitHub Pages. A manual run republishes the current `docs/` contents; it does not query SolarEdge or rebuild the dashboard data.

Published site: https://keilin.github.io/solar-edge/

## Shared credential handling

The monitor and backfill workflows both call the SolarEdge API. OAuth refresh tokens rotate, so each workflow writes any newly issued refresh token back to the `SOLAREDGE_REFRESH_TOKEN` repository secret before the job exits.

They use `GH_PAT` as `GH_TOKEN` for that update. The fine-grained PAT must be scoped to this repository and have **Actions: Read and write** and **Secrets: Read and write** permissions. If token persistence fails, fix that before rerunning API workflows; otherwise a rotated token may be lost.
