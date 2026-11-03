# SolarEdge Monitor

**Published dashboard:** https://keilin.github.io/solar-edge/

Automated SolarEdge production tracking using GitHub Actions and the SolarEdge Monitoring API V2 (OAuth 2.0, Site Access).

The workflow runs daily, reads the previous day's production, updates `data/production.csv`, rebuilds `docs/dashboard.json`, and commits the updated data. SolarEdge rotates the refresh token during use; the workflow saves each replacement back to the GitHub repository secret.

## One-time setup

### 1. Create a SolarEdge API application

1. Sign in to the [SolarEdge Developer Portal](https://developer.solaredge.com/).
2. Create an application with **Site Access** enabled and the `SITE_DATA` permission/scope.
3. In the application's OAuth settings, register this Redirect URI:

   `https://github.com/OWNER/REPOSITORY`

   Replace `OWNER/REPOSITORY` with this repository's path. For this project it is `https://github.com/keilin/solar-edge`.
4. Copy the application's **Client ID** and **Client Secret**. Keep the secret private.

The portal's **Consent Screen Preview** is only a preview; its Allow/Approve button is not interactive. Authorization is performed by opening the real authorization URL below.

### 2. Authorize the application and obtain the first refresh token

SolarEdge requires an initial authorization-code exchange before this workflow can run. The authorization code is short-lived and can only be exchanged once.

1. Build this URL, replacing `YOUR_CLIENT_ID` with the Client ID. The redirect URI is URL-encoded:

   ```text
   https://connect.solaredge.com/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=https%3A%2F%2Fgithub.com%2Fkeilin%2Fsolar-edge&response_type=code
   ```

   If using a different repository, substitute its exact registered Redirect URI in both the portal and this URL (URL-encode it).
2. Open the URL in a browser, sign in to the SolarEdge account that has access to the site, and approve the requested access.
3. SolarEdge redirects to the registered URI. The destination page may not render; that is okay. Inspect the browser address bar and find the `code=` query parameter. The URL also includes `site_id=`. Record the full redirected URL temporarily, but do not publish or share it: the authorization code is a credential.
4. Exchange the code promptly. The following Python script prompts for the Client ID, Client Secret, and full redirected URL, extracts the code, and requests the initial token pair. It requires the `requests` package (installed by `pip install -r requirements.txt`).

   ```python
   import getpass
   import requests
   from urllib.parse import urlparse, parse_qs

   client_id = input("Client ID: ").strip()
   client_secret = getpass.getpass("Client Secret: ")
   redirected_url = input("Paste complete redirected URL: ").strip()

   code = parse_qs(urlparse(redirected_url).query).get("code", [None])[0]
   if not code:
       raise SystemExit("No authorization code found in URL")

   response = requests.post(
       "https://monitoringapi.solaredge.com/v2/oauth2/token",
       auth=(client_id, client_secret),
       data={
           "grant_type": "authorization_code",
           "code": code,
           "redirect_uri": "https://github.com/keilin/solar-edge",
       },
       headers={"Accept": "application/json"},
       timeout=30,
   )
   response.raise_for_status()
   token_data = response.json()
   print("Initial authorization succeeded.")
   print("Refresh token:", token_data["refresh_token"])
   ```

   Save the returned `refresh_token` securely. Do not use the access token as the repository secret. Do not reuse the authorization code; it is single-use and expires quickly.

   If the script returns an error, check that the Client ID and Client Secret belong to the same application, that the Redirect URI matches exactly, and that you used a fresh code. A `401 invalid_client` indicates client authentication trouble; a `400 Invalid code` usually means the code is expired, already used, or mismatched with the redirect URI.

### 3. Add GitHub repository secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret** and add:

| Secret | Value |
|---|---|
| `SOLAREDGE_SITE_ID` | The numeric `site_id` from the authorization redirect |
| `SOLAREDGE_CLIENT_ID` | Client ID from the SolarEdge application |
| `SOLAREDGE_CLIENT_SECRET` | Client Secret from the SolarEdge application |
| `SOLAREDGE_REFRESH_TOKEN` | Initial refresh token from the code exchange |
| `GH_PAT` | Fine-grained GitHub personal access token (see below) |

Do not commit credentials, authorization URLs containing a code, access tokens, or refresh tokens to the repository.

### 4. Create the GitHub token used for refresh-token rotation

The workflow must update the `SOLAREDGE_REFRESH_TOKEN` repository secret after SolarEdge rotates it. The built-in `GITHUB_TOKEN` does not have the required permission for this operation, so create a fine-grained personal access token:

1. Create a fine-grained token restricted to this repository.
2. Grant repository permissions:
   - **Actions: Read and write**
   - **Secrets: Read and write**
   - **Metadata: Read-only** (automatically required)
3. Save the token as the repository secret `GH_PAT`.

The workflow exposes this secret as `GH_TOKEN` to the GitHub CLI. It uses the token to read the repository Actions public key and write the rotated refresh token. If the workflow reports HTTP 403 while updating the secret, check that the PAT has **Secrets: Read and write** and has not expired.

## Run and verify

1. Open **Actions → SolarEdge Monitor**.
2. Select **Run workflow** to test the setup immediately.
3. Confirm the run passes the client tests, retrieves production data, and completes the refresh-token secret update.
4. Check that `data/production.csv` and `docs/dashboard.json` are updated by the run.

The workflow is also scheduled to run daily. Each successful token refresh may rotate the refresh token; do not restore an older token from a backup after a successful run, or subsequent authentication may fail.

## Local development

Install dependencies and run the tests:

```sh
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```

The application expects these environment variables when run directly:

- `SOLAREDGE_SITE_ID`
- `SOLAREDGE_CLIENT_ID`
- `SOLAREDGE_CLIENT_SECRET`
- `SOLAREDGE_REFRESH_TOKEN`

Optionally set `SOLAREDGE_REFRESH_TOKEN_FILE` to a file path to have the client write a newly rotated refresh token there. The GitHub Actions workflow uses this mechanism and then updates the repository secret.
