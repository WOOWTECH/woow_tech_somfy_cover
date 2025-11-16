# Somfy PoE Motor Integration - Test Scripts

These test scripts help you verify each phase of the integration incrementally.

## Prerequisites

1. Install dependencies:
```bash
pip install cryptography
```

2. Update configuration in each test script:
   - `HOST`: Your device IP address (e.g., "10.1.1.10")
   - `TARGET_ID`: 6-character hex from MAC address (e.g., "160326")
   - `KEY`: 32-character hex encryption key (e.g., "FBE90399BA25B4B67DC1B23BE0D9C084")

## Test Phases

### Phase 1: Unencrypted Ping
Tests basic UDP communication without encryption.

```bash
python tests/test_phase1_ping.py
```

**Expected Output:**
- Sends JSON-RPC ping request
- Receives `{"result": true}` response
- ✓ Ping successful!

### Phase 2: Encrypted Communication
Tests AES-128-CBC encryption and device info retrieval.

```bash
python tests/test_phase2_encryption.py
```

**Expected Output:**
- Fetches device information (name, model, firmware, etc.)
- ✓ Encrypted communication successful!

### Phase 3: Status Queries
Tests position and state queries.

```bash
python tests/test_phase3_status.py
```

**Expected Output:**
- Shows current position, status, direction
- Displays movement state information
- ✓ Status queries successful!

### Phase 4: Movement Commands
Tests basic movement (up, down, stop).

⚠️ **WARNING**: This will physically move your cover!

```bash
python tests/test_phase4_movement.py
```

**Expected Output:**
- Sends move up → status becomes "running"
- Sends stop → status becomes "stopped"
- ✓ Movement commands successful!

### Phase 5: Position Control
Tests precise position control.

⚠️ **WARNING**: This will move your cover to 50%!

```bash
python tests/test_phase5_position.py
```

**Expected Output:**
- Moves cover to target position
- Monitors position updates during movement
- Verifies final position within tolerance
- ✓ Position control successful!

## Troubleshooting

### Connection Errors
- Verify device IP address is correct
- Check network connectivity
- Ensure device is powered on
- Verify firewall allows UDP port 55055

### Encryption Errors
- Verify KEY is correct (32-character hex)
- Check TARGET_ID matches device MAC address

### Position Issues
- Ensure end limits are set on the device
- Check for obstacles
- Verify device is not in thermal protection mode

## Next Steps

After all tests pass:
1. Copy `custom_components/somfy_poe/` to your Home Assistant `custom_components/` directory
2. Restart Home Assistant
3. Add integration via UI (Settings → Devices & Services → Add Integration)
4. Search for "Somfy PoE Motor"
5. Enter your device configuration
