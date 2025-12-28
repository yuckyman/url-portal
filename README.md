# Wintermute URL Portal

QR code-based interface for interacting with the wintermute vault repository.

## Architecture

1. **QR Codes** → Stable URLs: `https://yuckbox.spillyourguts.online/wm/p/<id>`
2. **Yuckbox Portal Router** → Quart server mapping portal IDs to actions
3. **iPhone Shortcut** → Glue layer triggering actions

## Setup

### Local Development

1. Install dependencies:
```bash
cd portal-server
pip install -r requirements.txt
```

2. Set environment variables (optional, defaults provided):
```bash
export WINTERMUTE_REPO_PATH=/path/to/wintermute
export WM_PORTAL_HOST=0.0.0.0
export WM_PORTAL_PORT=8090
```

3. Run the server:
```bash
python app.py
```

### Deployment to Yuckbox

1. Copy the `portal-server/` directory to yuckbox:
```bash
scp -r portal-server/ ian@yuckbox:/home/ian/scripts/url-portal/
```

2. SSH into yuckbox and set up:
```bash
ssh ian@yuckbox
cd /home/ian/scripts/url-portal
pip install -r requirements.txt
```

3. Configure environment variables (create `.env` or set systemd service):
```bash
export WINTERMUTE_REPO_PATH=/home/ian/WINTERMUTE
export WM_PORTAL_HOST=0.0.0.0
export WM_PORTAL_PORT=8090
```

4. Run as a service (systemd, supervisor, etc.) or use a process manager.

## Portal Configuration

Portals are configured in `0_admin/00_index/portals.json` in the wintermute repo:

```json
{
  "dly": {"action": "open_daily"},
  "h2o": {"action": "add_water", "delta": 64},
  "new": {"action": "new_file"},
  "mac": {"action": "open_on_mac"},
  "agent": {"action": "spawn_agent"}
}
```

## API Endpoints

- `GET /wm/p/<id>` - Get portal information
- `POST /wm/act` - Execute a portal action
- `GET /wm/endpoints` - List available endpoints
- `GET /health` - Health check
 
## Current Deployment

- Public URL (Tailscale-only): `https://yuckbox.spillyourguts.online`
- Reverse proxy: Caddy with handle blocks for `/wm/*` and `/health`
- Portal server: Quart on port `8090`

## Actions

### open_daily

Creates today's daily note from template if it doesn't exist, then commits and pushes to git.

- Template: `0_admin/02_templates/daily_note_2026.md`
- Output: `1_life/13_journal/YYYY-MM-DD.md`
- Placeholders: `{{date}}`, `{{DATE}}`, `{{title}}`, `{{date_long}}`, etc.

## iPhone Shortcut

The iPhone shortcut should:
1. Parse the scanned URL to extract portal ID
2. Call `GET /wm/p/<id>` to get action info
3. Call `POST /wm/act` with portal_id and action
4. Display result to user

## Testing

### Local Unit Tests

Run the test suite to verify basic functionality:

```bash
cd portal-server
python test_portal.py
```

This tests:
- Portal ID validation
- Route structure
- Action registry
- Configuration loading

### Integration Testing

After deployment to yuckbox:

1. **Verify HTTPS access**:
   ```bash
   curl https://yuckbox.spillyourguts.online/health
   ```

2. **Test portal endpoint**:
   ```bash
   curl https://yuckbox.spillyourguts.online/wm/p/dly
   ```

3. **Test action execution**:
   ```bash
   curl -X POST https://yuckbox.spillyourguts.online/wm/act \
     -H "Content-Type: application/json" \
     -d '{"portal_id": "dly", "action": "open_daily"}'
   ```

4. **List endpoints**:
   ```bash
   curl https://yuckbox.spillyourguts.online/wm/endpoints
   ```

5. **Verify daily note creation**:
   ```bash
   cd /home/ian/WINTERMUTE
   ls -la 1_life/13_journal/$(date +%Y-%m-%d).md
   git log --oneline -1
   ```

6. **Test iPhone shortcut**:
   - Scan QR code with URL: `https://yuckbox.spillyourguts.online/wm/p/dly`
   - Verify shortcut calls portal server
   - Check that daily note is created in repo

## Deployment Checklist

- [ ] Copy `portal-server/` to `ian@yuckbox:/home/ian/scripts/url-portal/`
- [ ] Run `deploy.sh` on yuckbox (or manually follow steps)
- [ ] Verify `portals.json` exists at `/home/ian/WINTERMUTE/0_admin/00_index/portals.json`
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Set environment variables
- [ ] Test server startup: `python app.py`
- [ ] Configure as systemd service (optional)
- [ ] Set up HTTPS/reverse proxy if needed
- [ ] Create iPhone shortcut following `shortcut_instructions.md`
- [ ] Test full flow end-to-end

## v2 Plans

- Mac listener service for opening Obsidian notes
- Additional portal actions (water tracking, new file creation)
- Advanced template system
- Agent spawning capabilities
- Working Copy integration

## Mac Listener

Standalone listener for opening apps/URLs on your Mac lives in `mac-listener/`.
See `mac-listener/README.md` for setup and security requirements.
