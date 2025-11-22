# Quick Reference: HAOS vs Docker Networking

## Do I Need to Worry About Port 55055?

### If you're using HAOS (Home Assistant OS):
```
✓ NO - It works automatically!
✓ HAOS uses host networking by default
✓ UDP port 55055 is automatically accessible
✓ Just install the integration normally
```

### If you're using HA Core in Docker:
```
⚠ YES - You need to configure networking
⚠ Add port mapping OR use host mode
⚠ See configuration examples below
```

---

## Installation Checklist

### HAOS (Production) - 5 Steps

```
□ 1. Copy integration to /config/custom_components/somfy_poe/
□ 2. Restart Home Assistant (Settings → System → Restart)
□ 3. Add integration (Settings → Devices & Services → Add Integration)
□ 4. Enter motor details (IP, Target ID, Encryption Key)
□ 5. Test by opening/closing cover
```

**Network configuration needed:** NONE ✓

---

### HA Core Docker (Development) - Setup

**Option A: Host Networking (Recommended)**

```yaml
# docker-compose.yml
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    image: homeassistant/home-assistant:stable
    network_mode: host  # ← Add this line
    volumes:
      - ./config:/config
    restart: unless-stopped
    privileged: true
```

Then:
```bash
docker-compose down
docker-compose up -d
```

---

**Option B: Bridge with Port Mapping**

```yaml
# docker-compose.yml
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    image: homeassistant/home-assistant:stable
    ports:
      - "8123:8123"
      - "55055:55055/udp"  # ← Add this line
    volumes:
      - ./config:/config
    restart: unless-stopped
```

Then:
```bash
docker-compose down
docker-compose up -d
```

---

## Quick Troubleshooting

### HAOS Issues

**Problem: Integration not responding**
```bash
# SSH into HAOS, then:
ping <motor-ip>                    # Check connectivity
docker exec homeassistant netstat -ulnp | grep 55055  # Check port
docker logs homeassistant | grep -i somfy  # Check logs
```

**Problem: Commands fail**
```
□ Verify encryption key (32 hex chars from motor label)
□ Verify Target ID (last 6 chars of MAC address, no colons)
□ Check motor has power (PoE connected)
□ Ensure end limits are configured on motor
```

---

### Docker Issues

**Problem: Port 55055 not accessible**
```bash
# Check port mapping
docker ps | grep homeassistant
docker port homeassistant

# If port not listed, add to docker-compose.yml:
ports:
  - "55055:55055/udp"

# Then restart
docker-compose down && docker-compose up -d
```

**Problem: Host mode not working (Mac/Windows)**
```
Docker Desktop for Mac/Windows doesn't support true host mode.
Use bridge mode with port mapping instead (Option B above).
```

---

## Configuration Values Quick Reference

### Required Information

| Parameter | Example | Where to Find |
|-----------|---------|---------------|
| **Name** | `Living Room Shade` | Your choice (friendly name) |
| **IP Address** | `192.168.1.77` | Router's DHCP list or motor config tool |
| **Target ID** | `160326` | Last 6 characters of MAC (no colons) |
| **Encryption Key** | `FBE90399BA25B4B67DC1B23BE0D9C084` | Label on motor or motor documentation |

### Finding Target ID

```
MAC Address:  4C:C2:06:16:03:26
                      └──┴──┴──┘
Target ID:               160326

IMPORTANT: Enter as STRING, not number!
Correct: "160326"
Wrong:   160326
```

---

## Network Mode Comparison

| Feature | HAOS | Docker (Host) | Docker (Bridge) |
|---------|------|---------------|-----------------|
| Works out of box | ✓ Yes | ✓ Yes | ⚠ Need port map |
| UDP 55055 access | ✓ Auto | ✓ Auto | ⚠ Manual config |
| mDNS discovery | ✓ Yes | ✓ Yes | ✗ No |
| Configuration needed | ✓ None | ⚠ docker-compose | ⚠ docker-compose |
| Best for | Production | Dev/Test | Dev (Mac/Win) |

---

## Testing Before Installation

```bash
# 1. Install dependencies
pip install cryptography

# 2. Download test script
cd working_tests/

# 3. Edit test_decrypt_responses.py with your motor details:
#    - MOTOR_IP = "192.168.1.77"
#    - ENCRYPTION_KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"
#    - TARGET_ID = "160326"

# 4. Run test
python3 test_decrypt_responses.py

# Expected output:
# ✓ Request sent successfully
# ✓ Response received (X bytes)
# ✓ Decrypted successfully
# ✓ Position: XX.X%
```

---

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection timeout` | Port 55055 not accessible | Check network config, add port mapping |
| `Invalid encryption key` | Wrong key format/value | Verify 32 hex chars from motor label |
| `Device locked (code 32)` | Motor is locked | Unlock motor via controls |
| `End limits not set (code 34)` | Motor needs calibration | Configure end limits on motor |
| `Cannot bind to port 55055` | Port already in use | Stop other service using port |

---

## Platform-Specific Notes

### HAOS on Raspberry Pi
```
✓ Works perfectly
✓ No special configuration
✓ Recommended platform
```

### HAOS on x86/VM
```
✓ Works perfectly
✓ Ensure VM has network bridge (not NAT)
✓ Ensure VM network adapter allows promiscuous mode
```

### Docker on Linux
```
✓ Host mode works
✓ Bridge mode works with port mapping
✓ Recommended for development
```

### Docker Desktop (Mac/Windows)
```
⚠ Host mode doesn't work properly
✓ Use bridge mode with port mapping
⚠ mDNS/multicast won't work
```

---

## Need More Help?

**Full documentation:** [HAOS_NETWORKING_GUIDE.md](HAOS_NETWORKING_GUIDE.md)

**Test scripts:** [working_tests/README.md](working_tests/README.md)

**Integration setup:** [README.md](README.md)

**Enable debug logging:**
```yaml
# configuration.yaml
logger:
  default: info
  logs:
    custom_components.somfy_poe: debug
```

Then check: **Settings → System → Logs**

---

**Last Updated:** 2025-11-22
