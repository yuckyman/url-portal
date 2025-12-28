# Mac Listener

Tiny listener service for opening apps, URLs, and tmux presets on your Mac.

## Setup

1. Install dependencies:
```bash
cd mac-listener
pip install -r requirements.txt
```

2. Copy presets:
```bash
cp presets.json.example presets.json
```

3. Export environment variables:
```bash
export WM_MAC_SHARED_SECRET="replace-with-random"
export WM_MAC_ALLOWED_IPS="100.x.x.x"            # yuckbox tailscale IP
export WM_MAC_ALLOWED_ROOTS="/Users/ian/WINTERMUTE:/Users/ian/other"
export WM_MAC_OBSIDIAN_VAULTS="WINTERMUTE"
```

4. Run the server:
```bash
python app.py
```

## Endpoints

- `POST /mac/open/obsidian`
  - `{ "path": "/Users/ian/WINTERMUTE/1_life/13_journal/2025-12-28.md" }`
  - or `{ "vault": "WINTERMUTE", "file": "1_life/13_journal/2025-12-28.md" }`
- `POST /mac/open/cursor`
  - `{ "path": "/Users/ian/WINTERMUTE" }`
- `POST /mac/open/url`
  - `{ "url": "https://chat.openai.com/" }`
  - optional `{ "app": "Google Chrome" }`
- `POST /mac/spawn/agent`
  - `{ "preset": "wm-agent", "cwd": "/Users/ian/WINTERMUTE" }`
- `GET /health`

## Security

- Requests must originate from an allowlisted IP (`WM_MAC_ALLOWED_IPS`)
- Requests must include a valid HMAC signature (shared secret)
- Replay protection via `X-WM-Timestamp` (defaults to 5-minute skew)
- Paths are restricted to `WM_MAC_ALLOWED_ROOTS`

### Signing Example (bash)

```bash
SECRET="replace-with-random"
BODY='{"path":"/Users/ian/WINTERMUTE/1_life/13_journal/2025-12-28.md"}'
TS=$(date +%s)
SIG=$(printf "%s.%s" "$TS" "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')

curl -X POST "http://macbook.local:8091/mac/open/obsidian" \
  -H "Content-Type: application/json" \
  -H "X-WM-Timestamp: $TS" \
  -H "X-WM-Signature: $SIG" \
  -d "$BODY"
```
