# Docker Setup Guide for Somfy PoE Integration

## Overview

The Somfy PoE integration uses UDP port 55055 for motor communication. This guide ensures proper network configuration for Docker environments (like Home Assistant OS).

## Network Requirements

### 1. UDP Port Access
The integration **MUST** be able to:
- Bind to UDP port 55055 (both send and receive)
- Send UDP packets to motor IP on port 55055
- Receive UDP responses from motor (ephemeral source port)

### 2. Docker Network Modes

#### Option A: Host Network (Recommended)
Use host network mode for direct network access:

```yaml
# docker-compose.yml
services:
  homeassistant:
    network_mode: host
```

**Pros:**
- Direct access to UDP port 55055
- No port mapping needed
- Motor can respond directly to host IP

**Cons:**
- Less container isolation
- Not available on Docker Desktop for Mac/Windows

#### Option B: Bridge Network with Port Mapping

```yaml
# docker-compose.yml
services:
  homeassistant:
    ports:
      - "55055:55055/udp"
```

**Pros:**
- Better container isolation

**Cons:**
- May cause issues with UDP responses (motor sends to ephemeral port)
- SO_REUSEADDR may not work correctly
- Not recommended for this integration

#### Option C: macvlan Network (Advanced)
Give container its own MAC address and IP:

```yaml
networks:
  somfy_net:
    driver: macvlan
    driver_opts:
      parent: eth0
```

**Pros:**
- Container appears as physical device on network
- Full UDP support

**Cons:**
- Complex setup
- Requires network reconfiguration

## Home Assistant OS Setup

### Recommended: Host Network Mode

1. **For Home Assistant OS (Supervised):**
   - Already uses host network mode by default
   - No additional configuration needed
   - Integration should work out of the box

2. **For Home Assistant Container:**
   ```bash
   docker run -d \
     --name homeassistant \
     --network=host \
     ghcr.io/home-assistant/home-assistant:stable
   ```

3. **For Home Assistant Docker Compose:**
   ```yaml
   version: '3'
   services:
     homeassistant:
       container_name: homeassistant
       image: ghcr.io/home-assistant/home-assistant:stable
       network_mode: host
       volumes:
         - ./config:/config
       restart: unless-stopped
   ```

## Testing Network Connectivity

### From Docker Container

```bash
# Enter the container
docker exec -it homeassistant bash

# Test motor is reachable
ping -c 3 192.168.1.77

# Verify UDP port (this should succeed)
nc -u -z -v 192.168.1.77 55055
```

### Python Socket Test

Create a test script in Home Assistant:

```python
import socket

# Test UDP socket binding
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    sock.bind(("", 55055))
    print("✓ Successfully bound to UDP port 55055")
    sock.close()
except OSError as e:
    print(f"✗ Failed to bind to UDP port 55055: {e}")
```

## Troubleshooting

### Issue: "Cannot bind to port 55055"

**Causes:**
- Another process is using the port
- Container doesn't have host network access
- Firewall blocking the port

**Solutions:**
```bash
# Check what's using the port
lsof -i UDP:55055

# If running HA in Docker without host network, add:
network_mode: host
```

### Issue: "Connection timeout"

**Causes:**
- Motor not on same network as container
- Network mode doesn't support UDP responses
- Firewall blocking traffic

**Solutions:**
1. Use host network mode
2. Verify motor IP is reachable from container
3. Check firewall rules (allow UDP 55055)

### Issue: "Motor responds sometimes, not always"

**Causes:**
- Rapid requests overwhelming motor
- Request ID conflicts
- Network congestion

**Solutions:**
1. Integration already has retry logic
2. Uses asyncio lock to serialize requests
3. Creates fresh socket per request

## Security Considerations

### Firewall Rules

Allow UDP traffic on port 55055:

```bash
# iptables (Linux)
iptables -A INPUT -p udp --dport 55055 -j ACCEPT
iptables -A OUTPUT -p udp --sport 55055 -j ACCEPT

# UFW (Ubuntu)
ufw allow 55055/udp
```

### Network Isolation

The integration:
- Uses AES-128-CBC encryption for all commands
- Requires the motor's encryption key
- No authentication needed (motor validates encrypted payload)

## Verification Checklist

Before deploying to production:

- [ ] Container can bind to UDP port 55055
- [ ] Motor IP is pingable from container
- [ ] UDP packets can reach motor (use nc or tcpdump)
- [ ] Motor responds to encrypted requests
- [ ] Integration test passes in container environment

## Example: Testing in Docker

```bash
# Create test container with host network
docker run -it --rm \
  --network=host \
  python:3.12 \
  bash

# Inside container
pip install cryptography
python3 << 'EOF'
import socket
import os
import json
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Your motor config
HOST = "192.168.1.77"
PORT = 55055
TARGET_ID = "160326"
KEY = bytes.fromhex("FBE90399BA25B4B67DC1B23BE0D9C084")

# Simple test message
message = '{"method":"status.info","params":{"targetID":"160326"},"id":1}'
iv = os.urandom(16)
padded = message.encode() + b'\x00' * (-len(message) % 16)

cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), default_backend())
encrypted = iv + cipher.encryptor().update(padded) + cipher.encryptor().finalize()

# Send and receive
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", PORT))
sock.settimeout(5)
sock.sendto(encrypted, (HOST, PORT))

try:
    response, addr = sock.recvfrom(4096)
    print(f"✓ SUCCESS: Received {len(response)} bytes from {addr}")
except socket.timeout:
    print("✗ TIMEOUT: No response")
finally:
    sock.close()
EOF
```

## Home Assistant Add-on Configuration

If you're creating an add-on, use this in `config.yaml`:

```yaml
name: Somfy PoE Control
version: "1.0.0"
slug: somfy_poe
description: Control Somfy PoE motors
arch:
  - aarch64
  - amd64
  - armv7
host_network: true  # CRITICAL for UDP port 55055
ports: {}  # No port mapping needed with host_network
```

## References

- [Home Assistant Networking](https://www.home-assistant.io/installation/)
- [Docker Network Drivers](https://docs.docker.com/network/)
- Somfy PoE motor requires UDP port 55055 bidirectional access
- Integration uses SO_REUSEADDR and SO_REUSEPORT for socket binding
