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

chatgpt notes:

# v1 iOS shortcut: `WM Portal`

## what you’re *actually* “accepting”
- when you run a shortcut via `shortcuts://run-shortcut?...&input=text&text=...`, the `text=` becomes **Shortcut Input** automatically — there’s no separate toggle you have to find. you just have to *read* it inside the shortcut. [1]

---

## build it (minimal + reliable)

### 0) create the shortcut
1. shortcuts app → `+` → **new shortcut**
2. name it **exactly**: `WM Portal` (the URL scheme matches by name) [1]

### 1) grab the portal_id from shortcut input
add actions in this order:

1. **Get Text from Input**  
   - this coerces the shortcut input into text (what you passed as `text=dly`). [5]
2. **Set Variable** → name: `portal_id`  
   - value: output of “Get Text from Input” [5]
3. **If** `portal_id` *is empty*  
   - **Ask for Input** (prompt: `portal id?`)  
   - **Set Variable** `portal_id` to the result [3]

✅ at this point: running from a QR deep link gives you `portal_id = dly`, and running manually still works.

---

## wire it to yuckbox `/wm/act` (v1 API call)

4. **Dictionary** (this becomes your JSON body)
   - `portal_id` : `portal_id`
   - `request_id` : (for now) `Current Date` (or any unique string)
   - `context` : (Dictionary)
     - `tz` : `America/New_York`

5. **Get Contents of URL**
   - URL: `https://<your-domain>/wm/act`
   - Method: `POST`
   - Request Body: `JSON`
   - JSON: the dictionary above [4]

6. **Quick Look** (or **Show Notification**) with the response (debug)

---

## test link (paste into safari on iphone)
- `shortcuts://run-shortcut?name=WM%20Portal&input=text&text=dly` [1]

if it opens shortcuts and runs, your “accept input” plumbing is correct.

---

## optional: open an `obsidian_uri` returned by the API
after “Get Contents of URL”:
- **Get Dictionary Value** `open` → then `obsidian_uri`
- **Open URLs** with that value

(this is clean if your `/wm/act` returns `{ "open": { "obsidian_uri": "obsidian://..." } }`.)

---

## share-sheet input (separate concept; not required for QR → shortcuts)
if you want `WM Portal` to appear in the share sheet (e.g., share a URL to it), enable:
- shortcut → **Details** → **Show in Share Sheet**
- then optionally limit accepted input types (URL/text/etc.) [2][4]

---

## references
[1] Apple Support — “Run a shortcut from a URL” (shortcuts://run-shortcut parameters): https://support.apple.com/guide/shortcuts/run-a-shortcut-from-a-url-apd624386f42/ios  
[2] Apple Support — “Understanding input types” (share sheet input filtering): https://support.apple.com/guide/shortcuts/input-types-apd7644168e1/ios  
[3] Apple Support — “Use the Ask for Input action”: https://support.apple.com/guide/shortcuts/use-the-ask-for-input-action-apd68b5c9161/ios  
[4] Apple Support — “Launch a shortcut from another app” (Show in Share Sheet / input block): https://support.apple.com/guide/shortcuts/launch-a-shortcut-from-another-app-apd163eb9f95/ios  
[5] Apple Support — “Use variables in Shortcuts” (magic variables / passing action outputs): https://support.apple.com/guide/shortcuts/use-variables-apdd02c2780c/ios  