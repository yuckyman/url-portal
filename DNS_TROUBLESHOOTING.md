# DNS Troubleshooting Guide

## Issue: Domain Not Resolving

If `yuckbox.spillyourguts.online` is not resolving, check the following:

## Quick Checks

1. **Run the diagnostic script**:
   ```bash
   ./check_dns.sh
   ```

2. **Check DNS resolution manually**:
   ```bash
   dig yuckbox.spillyourguts.online
   nslookup yuckbox.spillyourguts.online
   ```

3. **Test direct IP access** (bypasses DNS):
   ```bash
   curl http://100.89.92.75:8090/health
   ```

## Common Issues

### 1. DNS Record Not Created

**Symptom**: `dig` returns no results

**Solution**: 
- Verify the DNS record exists in your DNS provider
- Check that the A record points to `100.89.92.75`
- Ensure the record is active (not paused/deleted)

**For Tailscale MagicDNS**:
- Enable MagicDNS in Tailscale admin console
- Ensure the device is connected to Tailscale
- MagicDNS should automatically create DNS entries

### 2. DNS Propagation Delay

**Symptom**: Record exists but doesn't resolve everywhere

**Solution**: 
- DNS changes can take 5 minutes to 48 hours to propagate
- Check from different DNS servers: `dig @8.8.8.8 yuckbox.spillyourguts.online`
- Use a DNS propagation checker tool

### 3. Tailscale Not Connected

**Symptom**: Cannot reach `100.89.92.75`

**Solution**:
- Ensure Tailscale is running: `tailscale status`
- Connect to Tailscale network
- Verify device is authorized in Tailscale admin

### 4. Caddy Not Routing Correctly

**Symptom**: DNS resolves but HTTPS fails

**Check Caddyfile on yuckbox**:
```bash
ssh ian@yuckbox
cat /etc/caddy/Caddyfile
```

**Verify handle blocks**:
```caddy
yuckbox.spillyourguts.online {
    handle /wm/* {
        reverse_proxy localhost:8090
    }
    handle /health {
        reverse_proxy localhost:8090
    }
    handle {
        reverse_proxy localhost:8090
    }
}
```

**Check Caddy status**:
```bash
systemctl status caddy
journalctl -u caddy -f
```

### 5. Firewall Blocking

**Symptom**: Direct IP works but domain doesn't

**Check firewall rules on yuckbox**:
```bash
sudo ufw status
sudo iptables -L -n
```

## Testing Steps

1. **Test DNS resolution**:
   ```bash
   dig +short yuckbox.spillyourguts.online
   # Should return: 100.89.92.75
   ```

2. **Test direct IP** (bypasses DNS):
   ```bash
   curl http://100.89.92.75:8090/health
   # Should return: {"status":"healthy",...}
   ```

3. **Test HTTPS via domain**:
   ```bash
   curl -k https://yuckbox.spillyourguts.online/health
   # Should return: {"status":"healthy",...}
   ```

4. **Test portal endpoint**:
   ```bash
   curl -k https://yuckbox.spillyourguts.online/wm/p/dly
   # Should return portal config JSON
   ```

## Quick Fixes

### If DNS is the issue:

**Option 1: Use direct IP in QR code** (temporary):
- Update QR code URL to: `http://100.89.92.75:8090/wm/p/dly`
- Note: This won't work with HTTPS/SSL

**Option 2: Add to /etc/hosts** (local only):
```bash
echo "100.89.92.75 yuckbox.spillyourguts.online" | sudo tee -a /etc/hosts
```

**Option 3: Fix DNS record**:
- Log into your DNS provider
- Create/update A record: `yuckbox.spillyourguts.online` → `100.89.92.75`
- Wait for propagation

## Next Steps

Once DNS is working:
1. Test the QR code scans correctly
2. Verify iPhone shortcut can reach the domain
3. Test full flow: QR → Shortcut → Portal → Daily Note

