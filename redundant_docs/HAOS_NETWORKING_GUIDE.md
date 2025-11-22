# Home Assistant OS (HAOS) Networking Guide for Somfy PoE Integration

## Executive Summary

**CRITICAL ANSWER: NO, this UDP networking issue will NOT affect Home Assistant OS (HAOS) installations.**

The UDP port 55055 networking issue you encountered in the HA Core Docker development environment **does not apply** to production Home Assistant OS (HAOS) installations. Here's why:

| Environment | Network Mode | UDP Port 55055 | Will Integration Work? |
|------------|--------------|----------------|------------------------|
| **HA Core (Docker devcontainer)** | Bridge (isolated) | NOT accessible | NO - requires fix |
| **HAOS (Production)** | Host networking | Fully accessible | YES - works out of box |

---

## Table of Contents

1. [Quick Answer for HAOS Users](#quick-answer-for-haos-users)
2. [Understanding the Architecture](#understanding-the-architecture)
3. [Why the Issue Exists in Development](#why-the-issue-exists-in-development)
4. [Why HAOS Works Without Issues](#why-haos-works-without-issues)
5. [Installation Guide for HAOS](#installation-guide-for-haos)
6. [Installation Guide for HA Core (Docker)](#installation-guide-for-ha-core-docker)
7. [Networking Comparison: Dev vs Production](#networking-comparison-dev-vs-production)
8. [Troubleshooting](#troubleshooting)
9. [Technical Deep Dive](#technical-deep-dive)

---

## Quick Answer for HAOS Users

### Will This Work on My HAOS Installation?

**YES!** If you're running Home Assistant OS (HAOS), this integration will work perfectly without any network configuration changes.

### Do I Need to Configure Anything Special?

**NO!** Just install the integration normally through the UI. HAOS handles all networking automatically.

### What About Port Forwarding or Docker Settings?

**NOT NEEDED!** HAOS uses host networking mode by default, which gives Home Assistant direct access to all network ports, including UDP port 55055.

---

## Understanding the Architecture

### What is Home Assistant OS (HAOS)?

Home Assistant OS is a complete operating system specifically designed to run Home Assistant. It includes:

- **Minimal Linux OS** (based on Buildroot)
- **Docker container engine** (for running HA Core and add-ons)
- **Supervisor** (orchestration layer managing containers)
- **Automatic networking configuration** (host mode by default)

### Architecture Overview

```
┌──────────────────────────────────────────────┐
│           Home Assistant OS (HAOS)           │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │        Supervisor (Docker)             │ │
│  │  - Manages HA Core container           │ │
│  │  - Manages Add-on containers           │ │
│  │  - Handles updates & backups           │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │     HA Core Container                  │ │
│  │  Network Mode: HOST                    │ │  <-- KEY DIFFERENCE!
│  │  - Direct host network access          │ │
│  │  - All ports available (inc. 55055)    │ │
│  │  - mDNS/Multicast/Broadcast working    │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │     Physical Network Interface         │ │
│  │  (Direct access from HA Core)          │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
         │
         │ UDP 55055 ✓ (Direct access)
         │
    ┌────▼────┐
    │  Somfy  │
    │  Motor  │
    └─────────┘
```

### Why HAOS Uses Host Networking

HAOS runs the Home Assistant Core container with `network_mode: host` because:

1. **Device Discovery**: Many integrations need mDNS, UPnP, SSDP for auto-discovery
2. **Multicast/Broadcast**: Protocols like CoAP, SSDP require multicast support
3. **Direct Hardware Access**: Bluetooth, Zigbee, Z-Wave need direct network stack access
4. **Simplicity**: No port mapping configuration needed for users
5. **Performance**: Lower latency, fewer network hops

---

## Why the Issue Exists in Development

### HA Core Docker Development Environment

When you run HA Core in a Docker container for development (like in a VS Code devcontainer), the default networking is **bridge mode**:

```
┌──────────────────────────────────────────────┐
│           Host Machine (macOS/Linux)         │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │     Docker Bridge Network              │ │
│  │  (Isolated virtual network)            │ │
│  │                                        │ │
│  │  ┌──────────────────────────────────┐ │ │
│  │  │   HA Core Container              │ │ │
│  │  │  172.17.0.2                      │ │ │
│  │  │  - Isolated network namespace    │ │ │
│  │  │  - Port 55055 NOT exposed        │ │ │  <-- PROBLEM!
│  │  │  - UDP responses can't reach it  │ │ │
│  │  └──────────────────────────────────┘ │ │
│  └────────────────────────────────────────┘ │
│                                              │
│  ┌────────────────────────────────────────┐ │
│  │     Physical Network Interface         │ │
│  │  192.168.1.x                           │ │
│  └────────────────────────────────────────┘ │
└──────────────────────────────────────────────┘
         │
         │ UDP 55055 ✗ (Blocked by NAT)
         │
    ┌────▼────┐
    │  Somfy  │
    │  Motor  │
    └─────────┘
```

### Why UDP Fails in Bridge Mode

1. **Container sends UDP request** from `172.17.0.2:55055` → `192.168.1.77:55055`
2. **Request reaches motor** (outbound works through NAT)
3. **Motor sends UDP response** to `192.168.1.x:55055` (your host machine's IP)
4. **Response arrives at host**, but port 55055 is NOT mapped to container
5. **Response is dropped** - never reaches container at `172.17.0.2:55055`
6. **Container times out** waiting for response

---

## Why HAOS Works Without Issues

### HAOS Host Networking

HAOS configures the Home Assistant Core container with direct host network access:

```yaml
# Conceptual HAOS configuration (managed by Supervisor)
homeassistant:
  container_name: homeassistant
  image: homeassistant/home-assistant:stable
  network_mode: host  # <-- This is the magic!
  privileged: true
  restart: unless-stopped
```

### How This Solves the UDP Problem

With host networking in HAOS:

1. **Container shares host's network stack** - no separate IP address
2. **Container binds directly to port 55055** on the host interface
3. **Container sends UDP from host IP** (`192.168.1.x:55055`)
4. **Motor sends response to host IP** (`192.168.1.x:55055`)
5. **Response arrives directly at container** - socket receives it
6. **Communication works perfectly** - no NAT, no port mapping needed

### Benefits of HAOS Approach

| Feature | Bridge Mode (Dev) | Host Mode (HAOS) |
|---------|------------------|------------------|
| UDP port access | Manual port mapping required | Automatic |
| mDNS discovery | Doesn't work | Works perfectly |
| Multicast | Limited/broken | Full support |
| Broadcast | Limited/broken | Full support |
| Configuration needed | Port mapping in docker-compose | None |
| Performance | NAT overhead | Direct access |
| Complexity | High | Low |

---

## Installation Guide for HAOS

### Prerequisites

1. **HAOS installed** (any version 2024.x or later)
2. **Somfy PoE motor** on your network
3. **Network connectivity** between HAOS and motor (same subnet recommended)

### Installation Steps

#### 1. Copy Integration to HAOS

**Method A: Using Samba Add-on (Recommended)**

1. Install "Samba share" add-on in HAOS
2. Navigate to `\\homeassistant\config\` (Windows) or `smb://homeassistant/config/` (macOS)
3. Create folder: `custom_components/somfy_poe/`
4. Copy all integration files to this folder

**Method B: Using SSH Add-on**

1. Install "SSH & Web Terminal" add-on in HAOS
2. Connect via SSH
3. Navigate to `/config/custom_components/`
4. Create folder and copy files:
   ```bash
   mkdir -p /config/custom_components/somfy_poe
   cd /config/custom_components/somfy_poe
   # Upload files via SFTP or wget
   ```

**Method C: Using File Editor Add-on**

1. Install "File editor" add-on in HAOS
2. Create folder structure via UI
3. Upload files one by one

#### 2. Restart Home Assistant

1. Go to **Settings** → **System**
2. Click **Restart** (top right)
3. Wait for restart to complete (~1-2 minutes)

#### 3. Add Integration

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for "**Somfy PoE Motor**"
4. Click on the integration

#### 4. Configure Integration

Enter the following information:

- **Name**: Friendly name (e.g., "Living Room Shade")
- **IP Address**: Motor's IP address (e.g., `192.168.1.77`)
- **Target ID**: Last 6 characters of MAC address (e.g., `160326`)
- **Encryption Key**: 32-character hex key from motor label (e.g., `FBE90399BA25B4B67DC1B23BE0D9C084`)

#### 5. Verify Installation

1. Check **Settings** → **Devices & Services** → **Somfy PoE Motor**
2. You should see your motor listed
3. Test by opening/closing the cover
4. Check position updates in real-time

### HAOS Network Requirements

For HAOS, you only need:

- **Same network subnet** as the motor (recommended)
- **No firewall blocking** UDP port 55055 between HAOS and motor
- **No VLAN isolation** between HAOS and motor

That's it! No port mapping, no network mode configuration, no Docker settings needed.

---

## Installation Guide for HA Core (Docker)

### For Development/Testing Environments Only

If you're running HA Core in Docker (not HAOS), you need to configure network settings:

### Option 1: Host Network Mode (Recommended)

**docker-compose.yml:**
```yaml
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    image: homeassistant/home-assistant:stable
    network_mode: host  # <-- Add this
    volumes:
      - ./config:/config
      - /etc/localtime:/etc/localtime:ro
    restart: unless-stopped
    privileged: true
```

**Pros:**
- Works exactly like HAOS
- Full device discovery support
- No port mapping needed
- Best for production-like testing

**Cons:**
- Container shares all host ports (less isolation)
- Not supported on Docker Desktop for Mac/Windows

### Option 2: Bridge Mode with Port Mapping

**docker-compose.yml:**
```yaml
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    image: homeassistant/home-assistant:stable
    network_mode: bridge  # <-- Default, but explicit
    ports:
      - "8123:8123"      # Web UI
      - "55055:55055/udp"  # Somfy PoE motor (REQUIRED!)
    volumes:
      - ./config:/config
      - /etc/localtime:/etc/localtime:ro
    restart: unless-stopped
```

**Pros:**
- Better container isolation
- Works on all Docker platforms

**Cons:**
- Must map every required port manually
- mDNS/multicast may not work
- Must restart container after adding ports

### Verification After Setup

```bash
# Check that port 55055 is bound
docker exec homeassistant netstat -ulnp | grep 55055

# Should show something like:
# udp  0  0  0.0.0.0:55055  0.0.0.0:*  -

# Test communication
docker logs homeassistant | grep somfy_poe
```

---

## Networking Comparison: Dev vs Production

### Side-by-Side Comparison

| Aspect | HA Core (Docker Dev) | HAOS (Production) |
|--------|---------------------|-------------------|
| **Installation Type** | Manual Docker container | Complete OS |
| **Network Mode** | Bridge (default) | Host (automatic) |
| **Network Configuration** | Manual in docker-compose.yml | Automatic by Supervisor |
| **Port 55055 Access** | Must be mapped explicitly | Available automatically |
| **UDP Communication** | Requires port mapping | Works out of box |
| **mDNS Discovery** | Limited/broken | Works perfectly |
| **Multicast Support** | Limited/broken | Full support |
| **Device Discovery** | May fail | Works perfectly |
| **Configuration Files** | docker-compose.yml | None (managed by Supervisor) |
| **User Expertise Needed** | Docker networking knowledge | None |
| **Setup Complexity** | High | Low |
| **Best For** | Development/testing | Production use |

### What Works Where

| Feature | Dev (Bridge) | Dev (Host) | HAOS |
|---------|--------------|------------|------|
| Web UI (8123) | ✓ (with port mapping) | ✓ | ✓ |
| Somfy UDP (55055) | ✓ (with port mapping) | ✓ | ✓ |
| mDNS discovery | ✗ | ✓ | ✓ |
| Multicast | ✗ | ✓ | ✓ |
| Broadcast | ✗ | ✓ | ✓ |
| Zigbee/Z-Wave USB | ✓ (with device mapping) | ✓ | ✓ |
| Bluetooth | ✗ | ✓ | ✓ |
| Add-ons | ✗ | ✗ | ✓ |
| Supervisor | ✗ | ✗ | ✓ |

---

## Troubleshooting

### HAOS Issues

#### Issue: Integration Not Responding

**Symptoms:**
- Integration shows as "unavailable"
- No response from motor commands
- Timeout errors in logs

**Diagnosis:**
```bash
# SSH into HAOS (requires SSH add-on)

# 1. Check if HA Core container is running
docker ps | grep homeassistant

# 2. Check network mode (should show "host")
docker inspect homeassistant | grep NetworkMode

# 3. Check if port 55055 is accessible
nc -u -v 192.168.1.77 55055

# 4. Check logs
docker logs homeassistant | grep -i somfy
```

**Solutions:**

1. **Verify motor is reachable:**
   ```bash
   ping 192.168.1.77
   ```

2. **Check firewall (if using external firewall):**
   - Ensure UDP port 55055 is allowed between HAOS and motor
   - Most home networks don't have this issue

3. **Check VLAN configuration:**
   - HAOS and motor must be on same VLAN
   - Multicast/broadcast doesn't cross VLANs by default

4. **Enable debug logging:**
   ```yaml
   # configuration.yaml
   logger:
     default: info
     logs:
       custom_components.somfy_poe: debug
   ```

#### Issue: Motor Discovered But Commands Fail

**Symptoms:**
- Integration loads successfully
- Position shows as "unknown"
- Commands timeout or fail

**Solutions:**

1. **Verify encryption key:**
   - Check motor label for correct key
   - Key must be exactly 32 hex characters
   - Case doesn't matter (will be uppercased)

2. **Verify Target ID:**
   - Must be last 6 characters of MAC address
   - Example: MAC `4C:C2:06:16:03:26` → Target ID `160326`
   - Must be entered as STRING (with quotes in YAML if applicable)

3. **Check motor status:**
   - Ensure motor has power (PoE connected)
   - Ensure end limits are configured
   - Test motor with physical controls

### HA Core Docker Issues

#### Issue: Port 55055 Not Accessible in Bridge Mode

**Symptoms:**
- Same as HAOS timeout issues
- But you're running HA Core in Docker

**Solutions:**

1. **Add port mapping to docker-compose.yml:**
   ```yaml
   ports:
     - "8123:8123"
     - "55055:55055/udp"  # Add this line
   ```

2. **Or switch to host network mode:**
   ```yaml
   network_mode: host
   # Remove 'ports' section entirely
   ```

3. **Restart container:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

4. **Verify port is bound:**
   ```bash
   docker exec homeassistant netstat -ulnp | grep 55055
   ```

#### Issue: Host Mode Not Working on macOS/Windows

**Symptom:**
- `network_mode: host` doesn't work on Docker Desktop

**Explanation:**
- Docker Desktop for Mac/Windows runs Docker inside a Linux VM
- Host networking connects to VM, not your actual host
- This is a Docker Desktop limitation

**Solutions:**

1. **Use bridge mode with port mapping** (see above)
2. **Or use Linux** for development
3. **Or develop directly on HAOS** (create devcontainer inside HAOS VM)

---

## Technical Deep Dive

### How HAOS Manages Networking

#### Supervisor Architecture

The HAOS Supervisor manages Docker containers with specific networking configurations:

```python
# Conceptual Supervisor logic (simplified)
def create_homeassistant_container():
    config = {
        "image": "homeassistant/home-assistant:stable",
        "network_mode": "host",  # Direct host access
        "privileged": True,       # Hardware access
        "restart_policy": {"Name": "unless-stopped"},
        # ... other settings
    }
    docker_client.containers.create(**config)
```

#### Network Stack in HAOS

```
┌─────────────────────────────────────────────────────┐
│               HAOS Linux Kernel                     │
│  - Network drivers                                  │
│  - Network namespaces                               │
│  - iptables/nftables (firewall)                     │
└─────────────────────────────────────────────────────┘
                        │
                        │ Host network namespace
                        │ (shared with containers)
                        ▼
┌─────────────────────────────────────────────────────┐
│          Physical Network Interface                 │
│  eth0: 192.168.1.x                                  │
│  - All ports accessible                             │
│  - Multicast enabled                                │
│  - Broadcast enabled                                │
└─────────────────────────────────────────────────────┘
          │                             │
          │                             │
    ┌─────▼──────┐              ┌──────▼──────┐
    │ HA Core    │              │  Add-ons    │
    │ Container  │              │ (hassio     │
    │ (host net) │              │  network)   │
    └────────────┘              └─────────────┘
```

### UDP Communication Flow in HAOS

#### 1. Socket Creation

```python
# In transport.py (running inside HA Core container on HAOS)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 55055))  # Binds to host's 0.0.0.0:55055
```

Because of host networking:
- Socket binds to **host's network interface** directly
- No NAT, no port translation
- Socket appears at `192.168.1.x:55055` to external network

#### 2. Sending Request

```python
# Send encrypted request to motor
sock.sendto(encrypted_packet, (motor_ip, 55055))
```

Packet travels:
```
HA Core → Host eth0 → Network → Somfy Motor
(192.168.1.x:55055) → (192.168.1.77:55055)
```

#### 3. Receiving Response

```python
# Motor sends response back
data, addr = sock.recvfrom(4096)
```

Response travels:
```
Somfy Motor → Network → Host eth0 → HA Core
(192.168.1.77:55055) → (192.168.1.x:55055) → Socket
```

**Key Point:** Because the socket is bound to the host's interface, the response arrives **directly** at the socket without any NAT translation.

### Why Bridge Mode Fails

In Docker bridge mode:

```python
# Same code in bridge mode
sock.bind(("", 55055))  # Binds to 172.17.0.2:55055 (container IP)
sock.sendto(encrypted_packet, (motor_ip, 55055))
```

Packet flow:
```
HA Core → Docker NAT → Host eth0 → Network → Somfy Motor
(172.17.0.2:55055) → (192.168.1.x:RANDOM) → (192.168.1.77:55055)
                      ↑
                      Source port is randomized by NAT!
```

Response flow:
```
Somfy Motor → Network → Host eth0 → ??? → ✗
(192.168.1.77:55055) → (192.168.1.x:55055) → NOT MAPPED → DROPPED
```

The response goes to `192.168.1.x:55055`, but Docker hasn't mapped this port, so it gets dropped.

### HAOS Kernel Configuration

HAOS kernel is compiled with specific network features:

```bash
# Enabled features (from search results)
CONFIG_NETFILTER=y          # Firewall support
CONFIG_IP_MULTICAST=y       # Multicast routing
CONFIG_NET_IPGRE=y         # GRE tunneling

# Disabled features (by design)
# CONFIG_IP_MROUTE is not set  # Multicast forwarding between interfaces
```

**Note:** `CONFIG_IP_MROUTE` is disabled, which means multicast forwarding between interfaces (e.g., for routing multicast between VLANs) is not supported. However, this doesn't affect single-interface multicast, which is what most integrations (including Somfy) need.

### Add-on Network vs Core Network

HAOS uses different network modes for different containers:

```yaml
# Home Assistant Core
homeassistant:
  network_mode: host  # Full host access

# Add-ons (e.g., Mosquitto MQTT)
mosquitto:
  networks:
    - hassio  # Internal Docker network
  ports:
    - "1883:1883"  # Explicit port mapping
```

**Why different?**
- **HA Core needs host networking** for device discovery and custom integrations
- **Add-ons use isolated network** for security and proper container orchestration
- **Supervisor manages communication** between HA Core and add-ons

---

## Frequently Asked Questions

### General Questions

#### Q: Do I need to configure anything special for HAOS?

**A:** No. HAOS uses host networking by default, which gives the Somfy integration automatic access to UDP port 55055. Just install the integration normally.

#### Q: Will this work on Raspberry Pi running HAOS?

**A:** Yes! HAOS networking works the same on all platforms (Raspberry Pi, x86, VM, etc.). The integration will work perfectly.

#### Q: Do I need to open ports on my router?

**A:** No. The Somfy motor communicates locally on your LAN via UDP. No internet access or router port forwarding is needed.

#### Q: Can I run multiple motors?

**A:** Yes! Add each motor as a separate integration instance. Each integration creates its own UDP socket, and the `SO_REUSEADDR` option allows multiple sockets on port 55055.

### Technical Questions

#### Q: Why does the dev environment need port mapping but HAOS doesn't?

**A:** The dev environment (HA Core in Docker) uses bridge networking by default, which isolates the container's network. HAOS uses host networking, which gives the container direct access to the host's network stack.

#### Q: What if I'm running HAOS on a VLAN?

**A:** Ensure the Somfy motor is on the same VLAN as HAOS. UDP broadcast/multicast typically doesn't cross VLANs. If they must be on different VLANs, configure your router to allow UDP 55055 between VLANs.

#### Q: Can I use this integration with Home Assistant Container?

**A:** Yes, but you need to configure Docker networking yourself:
- **Option 1:** Use `network_mode: host` in docker-compose.yml
- **Option 2:** Map port `55055:55055/udp` in docker-compose.yml

#### Q: Does this integration require internet access?

**A:** No. All communication is local between Home Assistant and the Somfy motor via encrypted UDP. No cloud services are involved.

#### Q: What about Home Assistant Supervised?

**A:** Home Assistant Supervised also uses host networking for the Core container, just like HAOS. The integration will work without additional configuration.

### Troubleshooting Questions

#### Q: I installed the integration but it's not working on HAOS. Why?

**A:** Check these common issues:
1. Motor is powered on and reachable (can you ping it?)
2. Encryption key is correct (32 hex characters from motor label)
3. Target ID is correct (last 6 characters of MAC address)
4. No firewall blocking UDP 55055 between HAOS and motor
5. HAOS and motor are on same network/VLAN

#### Q: Can I test the integration before installing in HAOS?

**A:** Yes! Use the test scripts in `working_tests/`:
1. SSH into HAOS or run on another machine on the same network
2. Install Python dependencies: `pip install cryptography`
3. Run `python3 test_decrypt_responses.py`

#### Q: How do I check if port 55055 is being used in HAOS?

**A:** SSH into HAOS and run:
```bash
docker exec homeassistant netstat -ulnp | grep 55055
```

You should see the port bound if the integration is running.

---

## Summary

### For HAOS Users (Production)

✓ **Installation is straightforward:**
1. Copy integration to `/config/custom_components/somfy_poe/`
2. Restart Home Assistant
3. Add integration via UI
4. Enter motor configuration
5. Start using your motorized covers!

✓ **No network configuration needed** - HAOS handles everything automatically

✓ **Works out of the box** - Host networking gives direct access to UDP port 55055

### For HA Core Docker Users (Development)

⚠ **Additional configuration required:**

**Option 1: Host networking (recommended)**
```yaml
network_mode: host
```

**Option 2: Port mapping**
```yaml
ports:
  - "55055:55055/udp"
```

⚠ **Must restart container** after changing network configuration

⚠ **Host mode doesn't work** on Docker Desktop for Mac/Windows (use port mapping instead)

### Key Takeaways

1. **HAOS = No Issues** - Host networking is automatic
2. **HA Core Docker = Needs Configuration** - Bridge mode requires port mapping or switch to host mode
3. **UDP Port 55055 is Critical** - Must be accessible for motor communication
4. **Encryption Key is Critical** - Must match the key on your motor's label
5. **Same Network Required** - HAOS and motor should be on same subnet/VLAN

---

## Additional Resources

- **Home Assistant Installation Methods:** https://www.home-assistant.io/installation/
- **HAOS Documentation:** https://www.home-assistant.io/installation/#advanced-installation-methods
- **Docker Networking Documentation:** https://docs.docker.com/network/
- **Somfy PoE Integration README:** [README.md](README.md)
- **Testing Guide:** [TESTING.md](TESTING.md)
- **Development Guide:** [DEVELOPMENT.md](DEVELOPMENT.md)

---

**Last Updated:** 2025-11-22

**Questions?** Check the troubleshooting section or review the test scripts in `working_tests/` to verify your setup.
