# DNS Setup Instructions

## Current Status

- ❌ DNS record does NOT exist in Cloudflare
- ✅ Portal server is working on direct IP: `100.89.92.75:8090`
- ✅ Tailscale is running and IP is reachable
- ✅ Domain uses Cloudflare DNS (`spillyourguts.online`)

## Solution: Add DNS A Record

You have two options:

### Option 1: Cloudflare API (Automated)

1. **Get Cloudflare API Token**:
   - Go to https://dash.cloudflare.com/profile/api-tokens
   - Click "Create Token"
   - Use "Edit zone DNS" template
   - Select zone: `spillyourguts.online`
   - Create token and copy it

2. **Run the script**:
   ```bash
   export CLOUDFLARE_API_TOKEN='your-token-here'
   ./add_dns_record.sh
   ```

3. **Verify**:
   ```bash
   dig yuckbox.spillyourguts.online
   # Should return: 100.89.92.75
   ```

### Option 2: Cloudflare Dashboard (Manual)

1. **Log into Cloudflare Dashboard**:
   - Go to https://dash.cloudflare.com
   - Select zone: `spillyourguts.online`

2. **Add DNS Record**:
   - Go to DNS → Records
   - Click "Add record"
   - Type: `A`
   - Name: `yuckbox`
   - IPv4 address: `100.89.92.75`
   - TTL: `300` (or Auto)
   - Proxy status: `DNS only` (gray cloud, not orange)
   - Click "Save"

3. **Verify**:
   ```bash
   dig yuckbox.spillyourguts.online
   # Should return: 100.89.92.75
   ```

### Option 3: Tailscale MagicDNS (Alternative)

If you prefer to use Tailscale's built-in DNS instead:

1. **Enable MagicDNS**:
   - Go to https://login.tailscale.com/admin/dns
   - Enable MagicDNS
   - Add DNS name: `yuckbox.spillyourguts.online` → `100.89.92.75`

2. **Note**: This only works for devices connected to Tailscale

## After DNS is Set Up

Once DNS resolves:

1. **Test HTTPS**:
   ```bash
   curl -k https://yuckbox.spillyourguts.online/health
   ```

2. **Test Portal**:
   ```bash
   curl -k https://yuckbox.spillyourguts.online/wm/p/dly
   ```

3. **Regenerate QR Code** (if needed):
   ```bash
   python qr-codes/generate_qr.py
   ```

## Troubleshooting

### DNS Still Not Resolving After Adding Record

1. **Wait for propagation** (can take 5 minutes to 48 hours)
2. **Check from different DNS server**:
   ```bash
   dig @8.8.8.8 yuckbox.spillyourguts.online
   dig @1.1.1.1 yuckbox.spillyourguts.online
   ```
3. **Clear DNS cache**:
   ```bash
   # macOS
   sudo dscacheutil -flushcache
   sudo killall -HUP mDNSResponder
   ```

### HTTPS Not Working After DNS Resolves

1. **Check Caddy on yuckbox**:
   ```bash
   ssh ian@yuckbox
   systemctl status caddy
   journalctl -u caddy -f
   ```

2. **Verify Caddyfile**:
   ```bash
   cat /etc/caddy/Caddyfile
   ```

3. **Test SSL certificate**:
   ```bash
   curl -v https://yuckbox.spillyourguts.online/health
   ```

## Quick Reference

- **Domain**: `yuckbox.spillyourguts.online`
- **IP**: `100.89.92.75`
- **Port**: `8090` (internal), `443` (HTTPS via Caddy)
- **Zone**: `spillyourguts.online` (Cloudflare)

