# URL Portal Progress Notes

## Current Architecture

- QR code → `/wm/p/<portal_id>` on yuckbox.
- Quart server (portal router) maps portal IDs to actions.
- `POST /wm/act` executes actions (currently `open_daily`).
- Reverse proxy via Caddy (Docker) on `yuckbox.spillyourguts.online`.
- Working Copy deep links returned by the action response.

## What’s Implemented

- Portal server running on port `8090`.
- `/wm/p/<portal_id>` defaults to an HTML “Run Portal” page with a Shortcuts deep link and JSON debug link.
- `/wm/p/<portal_id>?format=json` returns discovery JSON.
- `/wm/act` executes `open_daily`:
  - Creates daily note if missing from template.
  - Replaces placeholders.
  - Git add/commit/push.
  - Returns `working_copy_url` and `obsidian_uri`.
- Endpoint hub: `/wm/endpoints`.
- Working Copy URL is now using `x-callback-url/read` with repo `wintermute` and optional key.

## Setbacks and Solutions

- **SSH deploy failed** (`Permission denied (publickey)`) → switched to running locally on yuckbox.
- **Python install blocked (PEP 668)** → created `.venv` and installed deps there.
- **Network restrictions for pip** → used escalated network access to install deps.
- **Port bind errors / sandbox networking** → ran with escalated permissions; moved to port `8090`.
- **Caddy TLS failure / container crash** → Caddy was missing mounted certs; recreated container from `/home/ian/yams/caddy` so `/etc/caddy/certs` is mounted.
- **HTTPS health check issues** → resolved after Caddy restart and correct cert mount.
- **Working Copy “open” command failed** → switched to documented `read` command; repo name needs to be `wintermute`.
- **Repo hygiene** → added `.cursor/` to `.gitignore` and removed `.sh` files from repo index.

## Existing Endpoints

- `GET /wm/p/<portal_id>` → HTML by default, JSON with `?format=json` or `Accept: application/json`.
- `POST /wm/act` → execute action.
- `GET /wm/endpoints` → list endpoints.
- `GET /health` → service health.

## Current Deployment

- Domain: `https://yuckbox.spillyourguts.online` (Tailscale-only)
- Reverse proxy: Caddy in Docker at `/home/ian/yams/caddy`
- Portal server: Quart on `8090`

## Open Issues / Blockers

- Working Copy Pro required for x-callback-url actions (`read`/`write`) → core deep link flow blocked until paid.
- DNS resolution still settling; tailnet-only access is OK for now.

## Next Steps

1. **Working Copy Pro**
   - Purchase/enable Pro to unlock x-callback-url actions.
   - Re-test `working_copy_url` from `/wm/act`.

2. **iOS Shortcut (WM Portal)**
   - Accept `portal_id` as text input.
   - POST to `https://yuckbox.spillyourguts.online/wm/act`.
   - Open `working_copy_url` in Working Copy.

3. **Action Hardening**
   - Add optional HMAC signature and timestamp for `/wm/act`.
   - Add lock/queue around git operations to prevent conflicts.

4. **Mac Listener (later)**
   - Add a lightweight listener to open Obsidian (or other apps) on macOS.
   - Provide `/wm/open` or server-driven notifications.

5. **Documentation**
   - Update README with Working Copy Pro requirement and Shortcuts setup steps.

