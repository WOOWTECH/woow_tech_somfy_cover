# WoowTech Somfy Cover - Home Assistant Integration

A Home Assistant custom component for controlling Somfy PoE (Power over Ethernet) motorized covers using the Synergy JSON-RPC API over encrypted UDP.

## Status: WORKING

This integration has been tested and verified working with a Somfy Sonesse 30 PoE motor. The motor responds successfully to movement commands, position queries, and status requests.

## Features

- Full cover control (open, close, stop, set position)
- Real-time position tracking with adaptive polling
- AES-128-CBC encryption for secure communication
- Automatic polling optimization (fast during movement, slow when idle)
- **Dual configuration methods**: Config Flow (UI) and YAML (both can coexist)
- Clean architecture with separated network and protocol layers
- Comprehensive error handling
- **Extensive documentation suite**: 66,000+ words covering architecture, API, configuration, testing, and development

## Supported Devices

Tested and working:
- Somfy Sonesse 30 PoE

Should also work with:
- Somfy Sonesse 40 PoE
- Somfy Curtain PoE
- Any Somfy PoE motor using the Synergy API

## Quick Start

### 1. Installation

Copy the integration to your Home Assistant custom_components folder:

```bash
cp -r custom_components/woow_tech_somfy_cover /config/custom_components/
```

Restart Home Assistant.

### 2. Configuration

You can configure this integration using **either** method (or both - they can coexist):

#### Option A: Config Flow (UI Setup)

Go to **Settings** → **Devices & Services** → **+ Add Integration** → Search for "WoowTech Somfy Cover"

You'll need:
- **Name**: Friendly name (e.g., "Living Room Shade")
- **Host**: Motor's IP address on your network (e.g., "192.168.1.77")
  - Validation: Must be a valid IPv4 address
- **Target ID**: 6-character hexadecimal string from MAC address (e.g., "160326")
  - Validation: Exactly 6 hex characters
- **Key**: 32-character hexadecimal encryption key from motor label
  - Validation: Exactly 32 hex characters

The integration will test the connection before creating the entry.

#### Option B: YAML Configuration (configuration.yaml)

Add to your `configuration.yaml`:

```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Living Room Shade          # Optional, default: "Somfy Cover"
    host: 192.168.1.77               # Required: IP address
    target_id: 160326                # Required: Can be quoted or unquoted (v1.0.2+)
    key: FBE90399BA25B4B67DC1B23BE0D9C084  # Required: Can be quoted or unquoted (v1.0.2+)
```

**Note**: Since v1.0.2, `target_id` and `key` can be specified with or without quotes for better UX.

Restart Home Assistant after editing `configuration.yaml`.

### 3. Finding Your Configuration Values

#### Target ID
The Target ID is the last 3 bytes of the MAC address:
- MAC Address: `4C:C2:06:16:03:26`
- Target ID: `160326` (last 6 characters, no colons)

**Note**: In UI, enter as string. In YAML (v1.0.2+), can be quoted or unquoted.

#### Encryption Key
The encryption key should be:
1. Printed on a label on the motor
2. In the motor documentation
3. Available via the Somfy web interface

Example: `FBE90399BA25B4B67DC1B23BE0D9C084`

**Note**: In UI, enter as string. In YAML (v1.0.2+), can be quoted or unquoted.

## Testing Before Installation

Before installing the integration, you can test communication with your motor using the verified test scripts:

```bash
cd working_tests/

# Test basic low-level commands and encryption
python3 test_decrypt_responses.py

# Test encrypted ping
python3 test_01_udp_ping_encrypted.py

# Test wake-up mechanism
python3 test_wakeup_mechanism.py

# Test Home Assistant integration API
python3 test_ha_integration_debug.py
```

See [working_tests/README.md](working_tests/README.md) for detailed testing instructions.

## Architecture Overview

The integration follows a clean, layered architecture:

```
┌─────────────────────────────────────┐
│   Home Assistant Integration        │
│   - cover.py (Cover entity)         │
│   - coordinator.py (State mgmt)     │
│   - config_flow.py (UI config)      │
├─────────────────────────────────────┤
│   API Client Layer                  │
│   - client.py (High-level methods)  │
│   - models.py (Data structures)     │
├─────────────────────────────────────┤
│   Protocol & Transport              │
│   - protocol.py (JSON-RPC)          │
│   - transport.py (UDP socket)       │
├─────────────────────────────────────┤
│   Encryption Layer                  │
│   - encryption.py (AES-128-CBC)     │
└─────────────────────────────────────┘
```

### Key Components

- **`api/encryption.py`**: Handles AES-128-CBC encryption/decryption with zero-padding
- **`api/transport.py`**: Manages UDP communication on port 55055 with proper socket options
- **`api/protocol.py`**: Builds and parses JSON-RPC messages
- **`api/client.py`**: Provides high-level API methods (move, stop, get_position, etc.)
- **`api/models.py`**: Data models for position, status, and device info
- **`coordinator.py`**: Data update coordinator with adaptive polling
- **`cover.py`**: Home Assistant cover entity implementation
- **`config_flow.py`**: UI-based configuration flow

## Technical Details

### Communication Protocol

- **Protocol**: UDP (not TCP)
- **Port**: 55055 (both source and destination)
- **Encryption**: AES-128-CBC with zero-padding
- **Message Format**: JSON-RPC 2.0
- **Packet Structure**: `[IV (16 bytes)][Encrypted JSON payload]`

### Important Technical Notes

1. **Port Binding**: Only ONE process can bind to UDP port 55055 at a time
   - Stop Home Assistant before running test scripts
   - Socket must use SO_REUSEADDR option
   - Socket must bind to port 55055, not just send to it

2. **Encryption**: Uses zero-padding, NOT PKCS7
   - Zero-padding: `data + b"\0" * (-len(data) % 16)`
   - Unpadding: `data.rstrip(b'\0')`
   - Random 16-byte IV per message

3. **Target ID**: Must be STRING type in JSON
   - Correct: `{"targetID": "160326"}`
   - Wrong: `{"targetID": 160326}`

4. **No Authentication Required**: UDP commands work without TCP/TLS authentication

### Position Convention

- **Somfy API**: 0 = fully open/up, 100 = fully closed/down
- **Home Assistant**: 0 = fully closed, 100 = fully open
- The integration automatically handles this conversion

### Supported Commands

| Command | Method | Description |
|---------|--------|-------------|
| Open | `move.up` | Open the cover (move up) |
| Close | `move.down` | Close the cover (move down) |
| Stop | `move.stop` | Stop current movement |
| Set Position | `move.to` | Move to specific position (0-100%) |
| Get Position | `status.position` | Get current position and movement state |
| Get Info | `status.info` | Get device information |

### Polling Strategy

The integration uses adaptive polling:

- **Normal mode**: 30 seconds (when stopped)
- **Fast mode**: 2 seconds (during movement)
- **Automatic switching**: Based on motor movement state

This minimizes network traffic while ensuring responsive UI updates during movement.

## Known Issues and Limitations

### Port Conflict
- **Issue**: Only one process can use port 55055 at a time
- **Impact**: Cannot run test scripts while Home Assistant integration is active
- **Solution**: Stop Home Assistant before running tests

### Single Motor per Entry
- **Issue**: One config entry = one motor
- **Impact**: Must create separate config entries for each motor
- **Workaround**: Add multiple integrations via UI

### Position Precision
- **Issue**: API supports 3 decimal places, HA displays integers
- **Impact**: Minor display difference only
- **Workaround**: None needed

### No Calibration Support
- **Issue**: Cannot set end limits via integration
- **Impact**: Must calibrate motors using physical controls or Somfy tools
- **Workaround**: Use motor configuration tools before Home Assistant setup

## Troubleshooting

### Device Not Responding

1. **Check network connectivity**:
   ```bash
   ping <motor-ip>
   ```

2. **Verify port 55055 is accessible**:
   ```bash
   # Check what's using the port
   lsof -i :55055
   # or on Linux:
   sudo netstat -tulpn | grep 55055
   ```

3. **Test with standalone script**:
   ```bash
   cd working_tests/
   python3 test_decrypt_responses.py
   ```

4. **Enable debug logging** in Home Assistant:
   ```yaml
   logger:
     default: info
     logs:
       custom_components.woow_tech_somfy_cover: debug
   ```

### Commands Not Working

1. **Verify encryption key** is correct (check motor label)
2. **Confirm Target ID** is correct (last 3 bytes of MAC)
3. **Check motor status** - ensure end limits are set
4. **Review logs** for error codes (see Error Codes section below)

### Position Not Updating

1. **Check end limits are configured** on the motor
2. **Verify polling is working** (check logs for update messages)
3. **Ensure motor is responsive** (test with physical controls)

## Error Codes

Common API error codes and their meanings:

| Code | Title | Meaning | Solution |
|------|-------|---------|----------|
| 32 | Device locked | Motor is locked | Unlock via motor controls |
| 34 | End limits not set | Motor needs calibration | Configure end limits |
| 48 | Thermal protection | Motor overheated | Wait for motor to cool |
| 49 | Obstacle detected | Safety feature triggered | Clear obstruction, reset motor |
| 255 | Device busy | Processing another command | Wait and retry |

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone <repository-url>
cd woowtech_somfy_new

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install cryptography homeassistant

# Run tests
cd working_tests/
python3 test_decrypt_responses.py
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for detailed development instructions.

### Running Tests

See [docs/TESTING.md](docs/TESTING.md) for comprehensive testing guide (12,000+ words).

### Contributing

Contributions are welcome! Please:

1. Test thoroughly using the provided test scripts
2. Follow Home Assistant development guidelines
3. Add tests for new functionality
4. Update documentation
5. Submit pull request with clear description

## Project Structure

```
woowtech_somfy_new/
├── README.md                          (this file)
├── docs/                              (comprehensive documentation - 66,000+ words)
│   ├── DOCUMENTATION_INDEX.md         (documentation hub)
│   ├── ARCHITECTURE.md                (system architecture - 23,000 words)
│   ├── API_REFERENCE.md               (complete API docs - 17,000 words)
│   ├── CONFIGURATION.md               (configuration guide - 14,000 words)
│   ├── TESTING.md                     (testing guide - 12,000 words)
│   ├── DEVELOPMENT.md                 (development guide)
│   └── WAKEUP_IMPLEMENTATION.md       (wake-up mechanism details)
├── working_tests/                     (verified standalone test scripts)
│   ├── README.md                      (test documentation)
│   ├── test_decrypt_responses.py      (low-level command test)
│   ├── test_01_udp_ping_encrypted.py  (encrypted ping test)
│   ├── test_wakeup_mechanism.py       (wake-up mechanism test)
│   ├── test_ha_integration_debug.py   (HA integration API test)
│   └── ... (other test files)
├── custom_components/
│   └── woow_tech_somfy_cover/         (Home Assistant integration)
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py             (UI configuration flow)
│       ├── coordinator.py             (data update coordinator)
│       ├── cover.py                   (cover entity)
│       ├── const.py                   (constants)
│       └── api/
│           ├── client.py              (high-level API client)
│           ├── encryption.py          (AES-128-CBC encryption)
│           ├── transport.py           (UDP communication)
│           ├── protocol.py            (JSON-RPC protocol)
│           ├── models.py              (data models)
│           └── exceptions.py          (custom exceptions)
└── tests/                             (integration tests)
```

## Documentation

### Comprehensive Documentation Suite (66,000+ words)

Start here:
- [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) - Documentation hub and navigation

Core documentation:
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - System architecture and design (23,000 words)
- [docs/API_REFERENCE.md](docs/API_REFERENCE.md) - Complete API reference (17,000 words)
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) - Configuration guide (14,000 words)
- [docs/TESTING.md](docs/TESTING.md) - Comprehensive testing guide (12,000 words)
- [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) - Development environment and workflow
- [docs/WAKEUP_IMPLEMENTATION.md](docs/WAKEUP_IMPLEMENTATION.md) - Wake-up mechanism details

Testing documentation:
- [working_tests/README.md](working_tests/README.md) - Test script documentation

Official references:
- [Somfy PoE Motor API Documentation](Somfy%20PoE%20Motor%20API%20for%20Integration.pdf) - Official API docs

## References

- **Somfy API Documentation**: "Somfy PoE Motor API for System Integration" (Rev 007, 2023)
- **Home Assistant Developer Docs**: https://developers.home-assistant.io/
- **AES Encryption**: https://en.wikipedia.org/wiki/Advanced_Encryption_Standard
- **JSON-RPC 2.0**: https://www.jsonrpc.org/specification

## License

This project is provided as-is for personal use.

## Acknowledgments

- Based on Somfy PoE Motor API documentation (Rev 007, 2023)
- Built for the Home Assistant community
- Uses the `cryptography` library for AES encryption

## Support

For issues and questions:

1. Start with [docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md) for navigation
2. Check [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for setup help
3. Review [docs/TESTING.md](docs/TESTING.md) for troubleshooting
4. Check [working_tests/README.md](working_tests/README.md) for test scripts
5. Enable debug logging in Home Assistant (see Troubleshooting section)
6. Run standalone test scripts to isolate issues
7. Check Home Assistant logs for detailed error messages

## Version History

- **v1.0.3** (2025-11-22): Documentation release
  - Comprehensive documentation suite (66,000+ words)
  - Architecture guide (23,000 words)
  - Complete API reference (17,000 words)
  - Configuration guide (14,000 words)
  - Testing guide (12,000 words)
  - Development guide
  - Wake-up implementation details

- **v1.0.2** (2025-11-22): YAML UX improvement
  - Improved YAML configuration user experience
  - `target_id` and `key` can now be specified with or without quotes
  - Better developer experience for configuration.yaml setup

- **v1.0.1** (2025-11-22): YAML configuration support
  - Added YAML platform configuration method
  - Config Flow and YAML can now coexist
  - Dual configuration options for flexibility

- **v1.0.0** (2025-11-22): Initial working release
  - UDP encrypted communication (AES-128-CBC)
  - Full motor control (up/down/stop/position)
  - Real-time position tracking
  - Adaptive polling (fast during movement, slow when idle)
  - Config Flow setup (UI configuration)

## Tested Configuration

This integration has been tested with:
- **Motor**: Somfy Sonesse 30 PoE
- **Firmware**: 5163364A07/5155239A32
- **Synergy Version**: 6
- **Home Assistant**: 2024.x
- **Python**: 3.11+

## Security Notes

- All communication is encrypted with AES-128-CBC
- Encryption key should be kept secure
- Communication is local network only (UDP, no internet access)
- No cloud services involved
- No authentication credentials stored

## Performance

- Command response time: < 100ms typical
- Position update frequency: 2 seconds during movement, 30 seconds when idle
- Network traffic: Minimal (small UDP packets)
- CPU usage: Negligible
- Memory usage: < 5MB

---

**Need help?** Check the documentation links above or run the test scripts in `working_tests/` to verify your setup.
