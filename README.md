# Somfy PoE Motor - Home Assistant Integration

A Home Assistant custom component for controlling Somfy PoE (Power over Ethernet) motorized covers using the Synergy JSON-RPC API.

## Features

- ✅ Full cover control (open, close, stop, set position)
- ✅ Real-time position tracking
- ✅ AES-128-CBC encryption for secure communication
- ✅ Automatic polling optimization (fast during movement, slow when idle)
- ✅ Config flow for easy setup via UI
- ✅ Incremental testing approach
- ✅ Clean architecture with separated network layer

## Screenshots

The integration creates a standard Home Assistant cover entity that can be controlled from the UI:

- **Open/Close buttons**: Fully open or close the cover
- **Stop button**: Stop movement at any position
- **Position slider**: Set precise position (0-100%)
- **State display**: Shows current position and movement state

## Supported Devices

- Somfy Sonesse 30 PoE
- Somfy Sonesse 40 PoE
- Somfy Curtain PoE

## Installation

### Method 1: Manual Installation

1. Copy the `custom_components/somfy_poe` directory to your Home Assistant `custom_components` folder:
   ```bash
   cp -r custom_components/somfy_poe /config/custom_components/
   ```

2. Restart Home Assistant

3. Add the integration:
   - Go to **Settings** → **Devices & Services**
   - Click **+ Add Integration**
   - Search for "Somfy PoE Motor"
   - Follow the configuration steps

### Method 2: HACS (Future)

This integration will be available through HACS in the future.

## Configuration

You'll need the following information from your Somfy PoE motor:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Friendly name for the cover | "Living Shade" |
| **IP Address** | Device IP on your network | 10.1.1.10 |
| **Target ID** | 6-character hex (last 3 bytes of MAC) | 160326 |
| **Encryption Key** | 32-character hex key | FBE90399BA25B4B67DC1B23BE0D9C084 |

### Finding Target ID

The Target ID is derived from the MAC address:
- MAC Address: `4C:C2:06:16:03:26`
- Target ID: `160326` (last 3 bytes)

### Finding the Encryption Key

The encryption key should be:
1. Printed on the motor label
2. Provided in your motor documentation
3. Configured via the Somfy web interface

## Testing

Before installing to Home Assistant, you can test the integration incrementally:

```bash
# Install dependencies
pip install cryptography

# Run tests (update configuration in each script first)
python tests/test_phase1_ping.py          # Test basic UDP communication
python tests/test_phase2_encryption.py    # Test encryption
python tests/test_phase3_status.py        # Test status queries
python tests/test_phase4_movement.py      # Test movement commands (⚠️ moves cover!)
python tests/test_phase5_position.py      # Test position control (⚠️ moves cover!)
```

See `tests/README.md` for detailed testing instructions.

## Architecture

The integration follows a clean, layered architecture:

```
┌─────────────────────────────────────┐
│     Home Assistant Integration      │
│  (cover.py, coordinator.py, etc.)   │
├─────────────────────────────────────┤
│         API Client Layer            │
│          (client.py)                │
├─────────────────────────────────────┤
│       Protocol & Transport          │
│   (protocol.py, transport.py)       │
├─────────────────────────────────────┤
│       Encryption Layer              │
│      (encryption.py)                │
├─────────────────────────────────────┤
│         UDP Network                 │
└─────────────────────────────────────┘
```

### Key Components

- **`api/encryption.py`**: AES-128-CBC encryption/decryption
- **`api/transport.py`**: UDP communication with encryption
- **`api/protocol.py`**: JSON-RPC message building/parsing
- **`api/client.py`**: High-level API methods
- **`coordinator.py`**: Data update coordinator with adaptive polling
- **`cover.py`**: Home Assistant cover entity
- **`config_flow.py`**: UI configuration flow

## API Reference

Based on the Somfy PoE Motor API for System Integration (Rev 007, 2023).

### Position Convention

- **Somfy API**: 0 = fully open/up, 100 = fully closed/down
- **Home Assistant**: 0 = fully closed, 100 = fully open
- The integration automatically handles this conversion

### Supported Commands

| Command | Description |
|---------|-------------|
| `move.up` | Open the cover (move up) |
| `move.down` | Close the cover (move down) |
| `move.stop` | Stop current movement |
| `move.to` | Move to specific position (0-100%) |
| `status.position` | Get current position and state |
| `status.info` | Get device information |

## Troubleshooting

### Device Not Connecting

1. **Check network connectivity**:
   ```bash
   ping 10.1.1.10
   ```

2. **Verify UDP port 55055 is accessible**:
   - Check firewall rules
   - Ensure no port blocking on network

3. **Validate configuration**:
   - Target ID must be exactly 6 hex characters
   - Encryption key must be exactly 32 hex characters

### Position Not Updating

1. **Check end limits are set** on the device
2. **Verify polling is working** (check logs for update messages)
3. **Test with manual commands** using test scripts

### Commands Not Working

1. **Check for device errors** in Home Assistant logs
2. **Verify encryption key** is correct
3. **Test basic connectivity** with `test_phase1_ping.py`

### Enable Debug Logging

Add to `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.somfy_poe: debug
```

## Known Limitations

- **Single motor per config entry**: Configure each motor separately
- **No group control**: Groups must be configured on the motors themselves
- **Position precision**: API supports 3 decimal places, HA shows integers
- **No calibration support**: End limits must be set via motor controls

## Technical Details

### Encryption

- **Algorithm**: AES-128-CBC
- **IV**: Random 16-byte initialization vector per message
- **Padding**: PKCS7
- **Packet Structure**: `[IV (16 bytes)][Encrypted Data (padded)]`

### Polling Strategy

- **Normal mode**: 30 seconds (when stopped)
- **Fast mode**: 2 seconds (during movement)
- **Automatic switching**: Based on motor state

### Error Handling

The integration handles various API error codes:

- Device locked (code 32)
- End limits not set (code 34)
- Thermal protection (code 48)
- Obstacle detection (code 49)
- Device busy (code 255)

## Contributing

Contributions are welcome! Please:

1. Test thoroughly using the provided test scripts
2. Follow Home Assistant development guidelines
3. Add tests for new functionality
4. Update documentation

## License

This project is provided as-is for personal use.

## Acknowledgments

- Based on Somfy PoE Motor API documentation (Rev 007, 2023)
- Built for Home Assistant community
- Uses the `cryptography` library for encryption

## Support

For issues and feature requests, please check:

1. **Test scripts** in `tests/` directory
2. **Debug logs** in Home Assistant
3. **API documentation** for command reference
4. **Home Assistant logs** for detailed error messages

## References

- [Somfy PoE Motor API Documentation](./Somfy%20PoE%20Motor%20API%20for%20Integration.pdf)
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [AES Encryption](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)
