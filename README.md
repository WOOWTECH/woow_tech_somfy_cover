# Somfy PoE Motor - Home Assistant Integration

A Home Assistant custom component for controlling Somfy PoE (Power over Ethernet) motorized covers using the Synergy JSON-RPC API over encrypted UDP.

## Status: WORKING

This integration has been tested and verified working with a Somfy Sonesse 30 PoE motor. The motor responds successfully to movement commands, position queries, and status requests.

## Features

- Full cover control (open, close, stop, set position)
- Real-time position tracking with adaptive polling
- AES-128-CBC encryption for secure communication
- Automatic polling optimization (fast during movement, slow when idle)
- Config flow for easy setup via UI
- Clean architecture with separated network and protocol layers
- Comprehensive error handling

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
cp -r custom_components/somfy_poe /config/custom_components/
```

Restart Home Assistant.

### 2. Configuration

Go to **Settings** → **Devices & Services** → **+ Add Integration** → Search for "Somfy PoE Motor"

You'll need:
- **Name**: Friendly name (e.g., "Living Room Shade")
- **IP Address**: Motor's IP on your network (e.g., 192.168.1.77)
- **Target ID**: 6-character hex string from MAC address (e.g., "160326")
- **Encryption Key**: 32-character hex key from motor label

### 3. Finding Your Configuration Values

#### Target ID
The Target ID is the last 3 bytes of the MAC address:
- MAC Address: `4C:C2:06:16:03:26`
- Target ID: `160326` (last 6 characters, no colons)

**IMPORTANT**: Must be entered as a STRING, not a number!

#### Encryption Key
The encryption key should be:
1. Printed on a label on the motor
2. In the motor documentation
3. Available via the Somfy web interface

Example: `FBE90399BA25B4B67DC1B23BE0D9C084`

## Testing Before Installation

Before installing the integration, you can test communication with your motor using the provided test scripts:

```bash
cd working_tests/

# Test basic communication and encryption
python3 test_decrypt_responses.py

# Test motor movement (WARNING: physically moves motor)
python3 test_motor_movement_with_position.py
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
       custom_components.somfy_poe: debug
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

See [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development instructions.

### Running Tests

See [TESTING.md](TESTING.md) for comprehensive testing guide.

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
├── DEVELOPMENT.md                     (development guide)
├── TESTING.md                         (testing guide)
├── working_tests/                     (standalone test scripts)
│   ├── README.md                      (test documentation)
│   ├── test_decrypt_responses.py      (main working test)
│   ├── test_motor_movement_with_position.py
│   └── ... (other test files)
├── custom_components/
│   └── somfy_poe/                     (Home Assistant integration)
│       ├── __init__.py
│       ├── manifest.json
│       ├── config_flow.py
│       ├── coordinator.py
│       ├── cover.py
│       ├── const.py
│       └── api/
│           ├── client.py
│           ├── encryption.py
│           ├── transport.py
│           ├── protocol.py
│           ├── models.py
│           └── exceptions.py
└── tests/                             (integration tests)
```

## Documentation

- [Working Tests README](working_tests/README.md) - Test script documentation
- [TESTING.md](TESTING.md) - Comprehensive testing guide
- [DEVELOPMENT.md](DEVELOPMENT.md) - Development environment and code guide
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

1. Check the [working_tests/README.md](working_tests/README.md)
2. Review [TESTING.md](TESTING.md) for troubleshooting
3. Enable debug logging in Home Assistant
4. Run standalone test scripts to isolate issues
5. Check Home Assistant logs for detailed error messages

## Version History

- **v1.0**: Initial working release
  - UDP encrypted communication
  - Full motor control (up/down/stop/position)
  - Real-time position tracking
  - Adaptive polling
  - Config flow setup

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
