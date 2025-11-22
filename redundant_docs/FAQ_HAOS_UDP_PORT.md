# FAQ: UDP Port 55055 and Home Assistant OS

## The Question

> "Is this problem will happen in real HAOS or not? Because we are setup HA core/project in computer to mimic HAOS. I want this fix could be applied to HAOS, is it possible, or any setting we need to apply?"

---

## The Answer

### NO, this problem will NOT happen in real HAOS.

The UDP port 55055 networking issue you encountered in the HA Core Docker development environment **does not affect** production Home Assistant OS (HAOS) installations.

---

## Why Not?

### Development Environment (HA Core in Docker)
```
Problem:
- Uses Docker bridge networking (isolated network)
- Port 55055/udp is NOT exposed by default
- UDP responses from motor can't reach the container
- Integration times out waiting for responses

Solution Required:
- Add port mapping: "55055:55055/udp"
- OR use host networking mode
```

### Production Environment (HAOS)
```
No Problem:
✓ Uses Docker host networking automatically
✓ Port 55055/udp is accessible by default
✓ UDP responses reach Home Assistant directly
✓ Integration works without any configuration

Solution Required:
✓ NONE - Works out of the box!
```

---

## What This Means for You

### If You're Running HAOS (Production)

1. **Install the integration normally** - No special configuration needed
2. **No port mapping required** - HAOS handles this automatically
3. **No Docker settings to change** - Supervisor manages everything
4. **It just works!** - Install and use like any other integration

### If You're Developing with HA Core (Docker)

1. **You need to configure networking** - Add port mapping or use host mode
2. **This is only for development** - Production HAOS doesn't need this
3. **See the networking guide** - Complete instructions provided

---

## Installation Steps for HAOS

```
Step 1: Copy integration to /config/custom_components/somfy_poe/
        (Use Samba, SSH, or File Editor add-on)

Step 2: Restart Home Assistant
        (Settings → System → Restart)

Step 3: Add integration via UI
        (Settings → Devices & Services → Add Integration)

Step 4: Enter motor configuration
        - IP Address: e.g., 192.168.1.77
        - Target ID: e.g., 160326 (last 6 chars of MAC)
        - Encryption Key: e.g., FBE90399BA25... (32 hex chars)

Step 5: Test your covers!
        (Open/Close/Set Position)

Network configuration needed: NONE ✓
```

---

## Why the Difference?

### HAOS Architecture

Home Assistant OS runs the Home Assistant Core container with **host networking mode** by default:

```yaml
# HAOS Supervisor automatically configures:
homeassistant:
  network_mode: host  # Direct host network access
  privileged: true
```

This means:
- Home Assistant has direct access to all network ports
- UDP port 55055 is available without configuration
- Device discovery (mDNS, UPnP, etc.) works automatically
- No port mapping needed

### HA Core Docker (Development)

When you run HA Core in Docker manually, it uses **bridge networking** by default:

```yaml
# Default Docker networking (isolated):
homeassistant:
  network_mode: bridge  # Isolated network
  # Ports must be mapped explicitly
```

This means:
- Container has its own isolated network (172.17.0.x)
- Ports must be explicitly mapped to host
- UDP responses can't reach container unless mapped
- You must configure networking manually

---

## Technical Explanation

### Why UDP Fails in Bridge Mode

```
Container (172.17.0.2) → NAT → Host (192.168.1.x) → Motor (192.168.1.77)
   Send: 172.17.0.2:55055 → (NAT changes to) 192.168.1.x:RANDOM → 192.168.1.77:55055 ✓

Motor (192.168.1.77) → Host (192.168.1.x) → ??? → Container (FAILS!)
   Reply: 192.168.1.77:55055 → 192.168.1.x:55055 → NOT MAPPED → DROPPED ✗
```

The motor sends the UDP response to your host machine's IP on port 55055, but Docker hasn't mapped that port, so the response is dropped before reaching the container.

### Why UDP Works in HAOS (Host Mode)

```
Container = Host (192.168.1.x) → Motor (192.168.1.77)
   Send: 192.168.1.x:55055 → 192.168.1.77:55055 ✓

Motor (192.168.1.77) → Host (192.168.1.x) = Container
   Reply: 192.168.1.77:55055 → 192.168.1.x:55055 → Container receives! ✓
```

With host networking, the container shares the host's network stack. The container binds directly to port 55055 on the host, so responses arrive directly.

---

## Settings to Apply in HAOS

### Answer: NONE!

HAOS doesn't need any network settings for this integration. The Supervisor automatically configures the Home Assistant Core container with host networking.

You **cannot** and **do not need to** change the network mode in HAOS. It's managed automatically and correctly by the Supervisor.

---

## Common Questions

### Q: Do I need to edit any configuration files in HAOS?

**A:** No. HAOS manages all Docker configuration automatically.

### Q: Do I need to forward ports on my router?

**A:** No. Communication is local between HAOS and the motor. No internet access or port forwarding needed.

### Q: Will this work on Raspberry Pi running HAOS?

**A:** Yes! HAOS networking works the same on all platforms (Pi, x86, VM, etc.).

### Q: What if I'm running HA Core in Docker, not HAOS?

**A:** Then you DO need to configure networking. See the [HAOS Networking Guide](HAOS_NETWORKING_GUIDE.md).

### Q: Can I test before installing on HAOS?

**A:** Yes! Use the test scripts in `working_tests/` to verify motor communication before installing the integration.

---

## Summary

| Environment | UDP Port Issue? | Configuration Needed? | Fix |
|-------------|-----------------|----------------------|-----|
| **HAOS (Production)** | ✗ No | ✗ None | ✓ Works automatically |
| **HA Core Docker (Dev)** | ✓ Yes | ✓ Yes | Add port mapping or host mode |

### Bottom Line

**If you're using HAOS:** You don't need to worry about this issue at all. Just install the integration and it will work perfectly.

**If you're developing with HA Core in Docker:** You need to configure networking as described in the [HAOS Networking Guide](HAOS_NETWORKING_GUIDE.md).

---

## Related Documentation

- **Complete Networking Guide:** [HAOS_NETWORKING_GUIDE.md](HAOS_NETWORKING_GUIDE.md)
- **Quick Reference:** [QUICK_REFERENCE_HAOS.md](QUICK_REFERENCE_HAOS.md)
- **Installation Guide:** [README.md](README.md)
- **Testing Guide:** [TESTING.md](TESTING.md)

---

**Last Updated:** 2025-11-22

**Still have questions?** Check the complete [HAOS Networking Guide](HAOS_NETWORKING_GUIDE.md) for detailed explanations and troubleshooting.
