# Configuration Guide

**WoowTech Somfy Cover Integration for Home Assistant**

Complete guide for configuring Somfy PoE motors in Home Assistant.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Finding Your Motor Credentials](#finding-your-motor-credentials)
3. [Configuration Methods](#configuration-methods)
4. [Config Flow (UI Setup)](#config-flow-ui-setup)
5. [YAML Configuration](#yaml-configuration)
6. [Multiple Motors](#multiple-motors)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## Prerequisites

### Hardware Requirements

- Somfy PoE motor installed and powered on
- Motor connected to same network as Home Assistant
- Motor end limits configured (use Somfy web interface)

### Network Requirements

- Static IP address for motor (recommended) or DHCP reservation
- Motor accessible from Home Assistant host
- Port 55055 (UDP) not blocked by firewall
- Home Assistant can bind to port 55055

### Software Requirements

- Home Assistant 2023.1 or later
- `cryptography` Python package (installed automatically)

---

## Finding Your Motor Credentials

You need three pieces of information:

### 1. IP Address

**Method A: Check your router**
- Log into your router
- Look for device with hostname `sfy_poe_XXXXXX`
- Note the IP address (e.g., 192.168.1.77)

**Method B: Somfy app**
- Open Somfy TaHoma or myLink app
- Find your motor
- View device settings for IP address

**Method C: Network scan**
```bash
# Using nmap (if installed)
nmap -sn 192.168.1.0/24 | grep -B2 "Somfy"
```

**Recommended**: Set a static IP or DHCP reservation for the motor

---

### 2. Target ID

The target ID is the last 6 characters of the motor's MAC address (in hex format).

**Method A: From web interface**
1. Browse to `https://<motor-ip>` (accept security warning)
2. Login with 4-digit PIN from motor label
3. Navigate to device info page
4. Find MAC address: `4C:C2:06:16:03:26`
5. Target ID is last 6 chars without colons: `160326`

**Method B: From Somfy documentation**
- Check motor label or documentation for MAC address
- Remove colons and take last 6 characters

**Format**:
- Must be exactly 6 hexadecimal characters
- Can use uppercase or lowercase (both work)
- Examples: `160326`, `1A2B3C`, `abcdef`

---

### 3. Encryption Key

The encryption key is a 32-character hexadecimal string used to encrypt communication.

**Where to find it**:
1. Browse to motor web interface: `https://<motor-ip>`
2. Login with PIN
3. Navigate to Settings or Security section
4. Look for "Encryption Key" or "AES Key"
5. Copy the 32-character hex string

**Format**:
- Must be exactly 32 hexadecimal characters (16 bytes)
- Can use uppercase or lowercase
- Example: `FBE90399BA25B4B67DC1B23BE0D9C084`

**Security Note**: This key should be kept secure. Anyone with this key can control your motor.

---

## Configuration Methods

The integration supports two configuration methods that can coexist:

| Method | Pros | Cons | Best For |
|--------|------|------|----------|
| **Config Flow (UI)** | Easy, guided setup<br>Built-in validation<br>Can modify later | Requires UI access | Most users<br>Single motor |
| **YAML** | Version controlled<br>Easy bulk setup<br>Templating possible | Manual editing<br>Requires HA restart | Advanced users<br>Multiple motors |

**You can use both methods simultaneously** for different motors without conflicts.

---

## Config Flow (UI Setup)

### Step-by-Step Guide

#### 1. Open Integration Settings

1. In Home Assistant, go to **Settings** → **Devices & Services**
2. Click the **+ ADD INTEGRATION** button (bottom right)
3. Search for "**WoowTech Somfy Cover**"
4. Click on the integration

![Add Integration](https://via.placeholder.com/800x400?text=Settings+>+Devices+%26+Services+>+Add+Integration)

---

#### 2. Enter Motor Information

Fill in the configuration form:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Friendly name for the motor | `Living Room Shade` |
| **Host** | Motor IP address | `192.168.1.77` |
| **Target ID** | 6-character hex ID | `160326` |
| **Key** | 32-character encryption key | `FBE90399BA25B4B67DC1B23BE0D9C084` |

![Configuration Form](https://via.placeholder.com/600x500?text=Configuration+Form)

**Input Validation**:
- Name: Any string
- Host: Valid IP address or hostname
- Target ID: Exactly 6 hex characters (0-9, A-F, a-f)
- Key: Exactly 32 hex characters

---

#### 3. Submit and Verify

1. Click **SUBMIT**
2. Integration tests connection to motor
3. If successful, device is created

**Success**:
```
✓ WoowTech Somfy Cover
  Living Room Shade
  Via woow_tech_somfy_cover
```

**Common Errors**:

| Error | Cause | Solution |
|-------|-------|----------|
| `cannot_connect` | Motor unreachable | Check IP address, network connection |
| `invalid_target_id` | Wrong format | Must be 6 hex characters |
| `invalid_key` | Wrong format | Must be 32 hex characters |
| `already_configured` | Duplicate target_id | Motor already added |

---

#### 4. Verify Entity

1. Go to **Settings** → **Devices & Services**
2. Find "**WoowTech Somfy Cover**"
3. Click on it to see entities
4. You should see: `cover.living_room_shade`

---

#### 5. Test Controls

1. Go to **Settings** → **Devices & Services** → **Entities**
2. Find `cover.living_room_shade`
3. Click on it to open controls
4. Test buttons:
   - **OPEN** - Motor should move up
   - **STOP** - Motor should stop
   - **CLOSE** - Motor should move down
   - **Position slider** - Move to specific position

---

### Modifying Configuration

**To change settings**:
1. Go to **Settings** → **Devices & Services**
2. Find "WoowTech Somfy Cover"
3. Click the **three dots** (⋮) on the integration entry
4. Select **CONFIGURE** (if available)
   - OR **DELETE** and re-add with new settings

**Note**: Deleting an entry removes all associated entities. Re-adding preserves entity history if you use the same name.

---

## YAML Configuration

### Basic YAML Setup

Add to your `configuration.yaml`:

```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Living Room Shade
    host: 192.168.1.77
    target_id: "160326"
    key: "FBE90399BA25B4B67DC1B23BE0D9C084"
```

**Important**: Reload configuration after editing (`Developer Tools` → `YAML` → `Restart`).

---

### YAML Configuration Options

| Parameter | Required | Type | Description | Default |
|-----------|----------|------|-------------|---------|
| `platform` | Yes | string | Must be `woow_tech_somfy_cover` | - |
| `name` | No | string | Friendly name for the motor | `Somfy Cover` |
| `host` | Yes | string | Motor IP address | - |
| `target_id` | Yes | string | 6-character hex target ID | - |
| `key` | Yes | string | 32-character hex encryption key | - |

---

### Unquoted Hex Values (v1.0.2+)

Starting in version 1.0.2, you can use unquoted hex values:

**Option 1: Quoted (always works)**
```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Bedroom Shade
    host: 192.168.1.78
    target_id: "160327"
    key: "ABC123DEF456789012345678901234AB"
```

**Option 2: Unquoted (v1.0.2+)**
```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Bedroom Shade
    host: 192.168.1.78
    target_id: 160327
    key: ABC123DEF456789012345678901234AB
```

Both formats work identically. Unquoted is more convenient, but quoted ensures compatibility.

---

### Complete Example

```yaml
# configuration.yaml
cover:
  # Living room shade
  - platform: woow_tech_somfy_cover
    name: Living Room Shade
    host: 192.168.1.77
    target_id: "160326"
    key: "FBE90399BA25B4B67DC1B23BE0D9C084"

  # Bedroom shade
  - platform: woow_tech_somfy_cover
    name: Bedroom Shade
    host: 192.168.1.78
    target_id: "160327"
    key: "FBE90399BA25B4B67DC1B23BE0D9C085"

  # Office shade
  - platform: woow_tech_somfy_cover
    name: Office Shade
    host: 192.168.1.79
    target_id: 160328
    key: FBE90399BA25B4B67DC1B23BE0D9C086
```

---

### Using Secrets

**Recommended**: Store sensitive values in `secrets.yaml`

**configuration.yaml**:
```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Living Room Shade
    host: !secret somfy_living_room_ip
    target_id: !secret somfy_living_room_target_id
    key: !secret somfy_living_room_key
```

**secrets.yaml**:
```yaml
# Somfy motors
somfy_living_room_ip: 192.168.1.77
somfy_living_room_target_id: "160326"
somfy_living_room_key: "FBE90399BA25B4B67DC1B23BE0D9C084"
```

---

### Validation

After adding YAML configuration:

1. Check configuration: `Developer Tools` → `YAML` → `Check Configuration`
2. Look for errors related to `cover` platform
3. If valid, restart Home Assistant

**Common YAML Errors**:

```yaml
# ❌ Wrong indentation
cover:
- platform: woow_tech_somfy_cover
  name: Living Room

# ✓ Correct indentation
cover:
  - platform: woow_tech_somfy_cover
    name: Living Room

# ❌ Missing quotes (for values that look like numbers)
target_id: 123456  # Interpreted as number

# ✓ With quotes (or use v1.0.2+ which handles this)
target_id: "123456"
```

---

## Multiple Motors

### Mixed Configuration (Recommended)

You can use both Config Flow and YAML for different motors:

**YAML** (configuration.yaml):
```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Living Room Shade
    host: 192.168.1.77
    target_id: "160326"
    key: "FBE90399BA25B4B67DC1B23BE0D9C084"
```

**Config Flow**: Add another motor via UI for bedroom

**Result**:
- `cover.living_room_shade` (from YAML)
- `cover.bedroom_shade` (from Config Flow)

Both work independently without conflicts.

---

### All Config Flow

**Pros**:
- Easy to add/remove
- Built-in validation
- No file editing

**Setup**:
1. Add first motor via Config Flow
2. Add second motor via Config Flow
3. Add third motor via Config Flow
4. etc.

---

### All YAML

**Pros**:
- Version controlled
- Easy bulk changes
- Can use templates/secrets

**Setup**:
```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Living Room Shade
    host: 192.168.1.77
    target_id: "160326"
    key: "FBE90399BA25B4B67DC1B23BE0D9C084"

  - platform: woow_tech_somfy_cover
    name: Bedroom Shade
    host: 192.168.1.78
    target_id: "160327"
    key: "FBE90399BA25B4B67DC1B23BE0D9C085"

  - platform: woow_tech_somfy_cover
    name: Kitchen Shade
    host: 192.168.1.79
    target_id: "160328"
    key: "FBE90399BA25B4B67DC1B23BE0D9C086"
```

---

### Groups

Create groups of covers for synchronized control:

```yaml
# configuration.yaml
cover:
  # Individual covers
  - platform: woow_tech_somfy_cover
    name: Living Room Left
    host: 192.168.1.77
    target_id: "160326"
    key: "FBE90399BA25B4B67DC1B23BE0D9C084"

  - platform: woow_tech_somfy_cover
    name: Living Room Right
    host: 192.168.1.78
    target_id: "160327"
    key: "FBE90399BA25B4B67DC1B23BE0D9C085"

  # Group
  - platform: group
    name: Living Room Shades
    entities:
      - cover.living_room_left
      - cover.living_room_right
```

Now you can control both shades together via `cover.living_room_shades`.

---

## Troubleshooting

### Connection Issues

**Problem**: `cannot_connect` error

**Solutions**:
1. **Verify IP address**
   ```bash
   ping 192.168.1.77
   ```
   Should get responses.

2. **Check network**
   - Motor and HA on same network?
   - Firewall blocking port 55055?
   - VLANs isolated?

3. **Test from HA host**
   ```bash
   # SSH into HA host
   nc -u 192.168.1.77 55055
   # Type anything and press Enter
   # Should not give "connection refused"
   ```

4. **Verify motor is powered**
   - Check power LED
   - Try accessing web interface: `https://192.168.1.77`

---

### Invalid Credentials

**Problem**: `invalid_target_id` or `invalid_key` error

**Solutions**:
1. **Check target_id format**
   - Exactly 6 hex characters
   - No colons, dashes, or spaces
   - Derived from last 6 chars of MAC address
   - Example: MAC `4C:C2:06:16:03:26` → Target ID `160326`

2. **Check key format**
   - Exactly 32 hex characters
   - No spaces or dashes
   - Should be one continuous string
   - Example: `FBE90399BA25B4B67DC1B23BE0D9C084`

3. **Copy/paste carefully**
   - Extra spaces at start/end
   - Wrong case (though both work)
   - Typos in manual entry

---

### Port Conflicts

**Problem**: Motor responds sometimes but not always

**Cause**: Another process is using port 55055

**Solutions**:
1. **Check what's using the port**
   ```bash
   # Linux/macOS
   lsof -i :55055

   # Or
   netstat -an | grep 55055
   ```

2. **Stop conflicting process**
   - Stop test scripts
   - Close other integrations using same motor

3. **Restart Home Assistant**
   - Ensures clean state

---

### YAML Errors

**Problem**: Configuration not loading

**Solutions**:
1. **Check YAML syntax**
   - Use `Check Configuration` in Developer Tools
   - Look for indentation errors
   - Verify all required fields present

2. **Common mistakes**:
   ```yaml
   # ❌ Wrong platform name
   platform: somfy_poe

   # ✓ Correct
   platform: woow_tech_somfy_cover

   # ❌ Missing quotes for numeric-looking IDs (pre-v1.0.2)
   target_id: 123456

   # ✓ With quotes (or use v1.0.2+)
   target_id: "123456"

   # ❌ Wrong indentation
   cover:
   - platform: woow_tech_somfy_cover

   # ✓ Correct indentation
   cover:
     - platform: woow_tech_somfy_cover
   ```

---

### Motor Not Responding

**Problem**: Entity unavailable or commands timeout

**Solutions**:
1. **Check logs**
   ```yaml
   # configuration.yaml
   logger:
     logs:
       custom_components.woow_tech_somfy_cover: debug
   ```
   Look for timeout or connection errors.

2. **First command slow?**
   - This is normal (motor wake-up)
   - Wait 2-3 seconds
   - Subsequent commands should be fast

3. **Network issues?**
   - Check WiFi/Ethernet connection
   - Restart motor (power cycle)
   - Check router/switch

4. **Motor locked?**
   - Check if Somfy app is connected
   - Close other applications controlling motor
   - Wait a few minutes and retry

---

## Advanced Configuration

### Custom Entity ID

Config Flow entities get auto-generated entity IDs based on the name. To customize:

**Option 1**: Rename in UI
1. Go to entity
2. Click settings icon
3. Change entity ID

**Option 2**: Use YAML with specific name
```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: lr_shade  # Creates entity_id: cover.lr_shade
    host: 192.168.1.77
    target_id: "160326"
    key: "FBE90399BA25B4B67DC1B23BE0D9C084"
```

---

### Customize Cover

Add custom icons, names, or attributes:

```yaml
# configuration.yaml or customize.yaml
homeassistant:
  customize:
    cover.living_room_shade:
      friendly_name: "Living Room Window Shade"
      icon: mdi:blinds
      device_class: shade
```

---

### Automations

**Example: Close at sunset**
```yaml
automation:
  - alias: "Close shades at sunset"
    trigger:
      - platform: sun
        event: sunset
    action:
      - service: cover.close_cover
        target:
          entity_id: cover.living_room_shade
```

**Example: Open at sunrise**
```yaml
automation:
  - alias: "Open shades at sunrise"
    trigger:
      - platform: sun
        event: sunrise
    action:
      - service: cover.open_cover
        target:
          entity_id: cover.living_room_shade
```

**Example: Set position based on sun elevation**
```yaml
automation:
  - alias: "Adjust shade based on sun"
    trigger:
      - platform: numeric_state
        entity_id: sun.sun
        attribute: elevation
        above: 30
    action:
      - service: cover.set_cover_position
        target:
          entity_id: cover.living_room_shade
        data:
          position: 50  # Half closed
```

---

### Debug Logging

Enable detailed logs for troubleshooting:

```yaml
# configuration.yaml
logger:
  default: warning
  logs:
    custom_components.woow_tech_somfy_cover: debug
    custom_components.woow_tech_somfy_cover.api: debug
    custom_components.woow_tech_somfy_cover.coordinator: debug
```

Logs will show:
- Connection attempts
- Commands sent/received
- Encryption details
- Position updates
- Wake-up mechanism

---

## Summary

### Quick Start Checklist

- [ ] Find motor IP address
- [ ] Find target ID (last 6 chars of MAC)
- [ ] Find encryption key (from web interface)
- [ ] Choose configuration method (Config Flow or YAML)
- [ ] Add integration
- [ ] Test controls (open/close/stop)
- [ ] Set up automations (optional)

### Best Practices

1. **Use static IPs** for motors (or DHCP reservation)
2. **Store keys in secrets.yaml** for security
3. **Test manually** before creating automations
4. **Monitor logs** when troubleshooting
5. **Update integration** when new versions available
6. **Document your configuration** for future reference

---

## Getting Help

If you encounter issues:

1. **Check logs** with debug logging enabled
2. **Verify credentials** are correct
3. **Test network connectivity** (ping motor)
4. **Search existing issues** on GitHub
5. **Ask for help** with logs and configuration details

**Include in support requests**:
- Home Assistant version
- Integration version
- Motor model and firmware
- Configuration method (YAML or Config Flow)
- Relevant log entries (with sensitive data removed)
