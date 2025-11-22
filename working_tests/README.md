# Working Test Scripts for Somfy PoE Integration

This directory contains verified, working test scripts for the Somfy PoE motor integration. These scripts have been tested and confirmed to successfully control a Somfy Sonesse 30 PoE motor via UDP.

## Overview

These test scripts demonstrate the core functionality needed for Home Assistant integration:
- Encrypted UDP communication (AES-128-CBC with zero-padding)
- Motor movement control (up/down/stop)
- Position querying and tracking
- Response decryption and parsing
- Home Assistant integration API testing

## CRITICAL PREREQUISITES

### Stop Home Assistant First!
**IMPORTANT**: Only ONE process can use UDP port 55055 at a time. Before running these tests:

```bash
# Stop Home Assistant or Docker container using the integration
# Otherwise you'll get "Address already in use" errors
sudo systemctl stop home-assistant
# OR
docker stop homeassistant
```

### Python Version
- Python 3.8 or higher

### Required Dependencies
```bash
pip install cryptography
```

### Network Requirements
- Motor must be accessible on your local network
- UDP port 55055 must be accessible (bidirectional)
- No firewall blocking between test machine and motor

### Configuration Information
You'll need:
- **Motor IP Address**: e.g., `192.168.1.77`
- **Target ID**: 6-character hex string (last 3 bytes of MAC address), e.g., `"160326"`
- **Encryption Key**: 32-character hex string, e.g., `"FBE90399BA25B4B67DC1B23BE0D9C084"`

**CRITICAL**:
- Target ID must be a STRING, not an integer: `"160326"` NOT `160326`
- Only ONE process can bind to port 55055 at a time

## Quick Start

### 1. Configure Test Scripts
Edit the configuration section at the top of each test script:

```python
HOST = "192.168.1.77"        # Your motor's IP address
TARGET_ID = "160326"         # Your motor's target ID (STRING!)
KEY_HEX = "FBE90399BA25B4B67DC1B23BE0D9C084"  # Your encryption key
```

### 2. Run Tests in Order

**Test the Home Assistant integration API** (recommended order):
```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests

# 1. Basic integration test - verify client API works
PYTHONPATH=/Users/alanlin/core python3 test_ha_integration_debug.py

# 2. Wake-up mechanism test - verify motor hibernation handling
PYTHONPATH=/Users/alanlin/core python3 test_wakeup_mechanism.py

# 3. Encrypted ping test - verify encryption works
python3 test_01_udp_ping_encrypted.py

# 4. Full command test - verify all operations
python3 test_decrypt_responses.py
```

## Test Scripts Description

### Main Working Tests (Root Directory)

#### `test_ha_integration_debug.py` (VERIFIED WORKING - INTEGRATION TEST)
**Purpose**: Test the Home Assistant integration using the actual client API

**What it does**:
- Uses the exact same `SomfyClient` API that the HA integration uses
- Mimics the config_flow.py connection validation process
- Tests client.connect(), client.get_device_info(), client.get_position()
- Verifies end-to-end integration functionality
- Tests transport, encryption, and protocol layers

**Use this to**:
- Verify the HA integration client works correctly
- Debug integration issues without running full HA
- Test API changes before deploying to HA
- Validate configuration (host, target_id, key) before adding to HA
- Troubleshoot connection problems

**Expected output**:
```
======================================================================
TESTING HA INTEGRATION CONNECTION (exact config_flow pattern)
======================================================================

Configuration:
  Host: 192.168.1.77
  Target ID: 160326
  Key: FBE90399BA25B4B67DC1B23BE0D9C084

======================================================================

1. Client created
   Using transport: <custom_components.woow_tech_somfy_cover.api.transport.SomfyTransport object at 0x...>
   Using encryption: <custom_components.woow_tech_somfy_cover.api.encryption.SomfyEncryption object at 0x...>
   Using protocol: <custom_components.woow_tech_somfy_cover.api.protocol.SomfyProtocol object at 0x...>

2. Connecting...
   ✓ Connection successful!

3. Getting device info...
   ✓ Device info retrieved successfully!
   Name: Sonesse 30 PoE
   Model: Sonesse 30 PoE
   Firmware: 5163364A07/5155239A32
   MAC: 4C:C2:06:16:03:26

4. Getting position...
   ✓ Position: 0.0%
   Status: stopped

======================================================================
SUCCESS - All tests passed!
======================================================================

5. Client closed
```

**Run with**:
```bash
# Must be run from HA core directory or have integration in Python path
cd /Users/alanlin/core  # Or wherever your HA installation is
python3 working_tests/test_ha_integration_debug.py

# OR add custom_components to Python path:
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests
PYTHONPATH=/Users/alanlin/core python3 test_ha_integration_debug.py
```

**Configuration**:
Edit the `config` dictionary in the script:
```python
config = {
    "host": "192.168.1.77",        # Your motor's IP
    "target_id": "160326",         # Your target ID (STRING)
    "key": "FBE90399BA25B4B67DC1B23BE0D9C084",  # Your encryption key
}
```

**Why this test is important**:
- Tests the ACTUAL integration code (not a reimplementation)
- Catches API changes or breaking modifications
- Validates the entire client stack works correctly
- Faster than restarting HA for every test
- Same code path as config_flow validation

---

#### `test_wakeup_mechanism.py` (VERIFIED WORKING - WAKE-UP TEST)
**Purpose**: Test the integration's wake-up mechanism for sleeping motors

**What it does**:
- Tests that first command after idle works without timeout
- Verifies wake-up mechanism handles sleeping motor transparently
- Tests subsequent commands work without wake-up overhead
- Simulates motor hibernation scenarios
- Runs 4 test scenarios:
  1. First command after connection (motor likely sleeping)
  2. Second command (motor awake, should be fast)
  3. Movement command (harmless stop command)
  4. After reconnection with idle time (motor may have slept again)

**Use this to**:
- Verify the wake-up mechanism works correctly
- Test motor behavior after idle periods
- Ensure no timeout issues with sleeping motors
- Validate transparent wake-up (user doesn't notice delay)
- Debug wake-up related connection problems

**Expected output**:
```
======================================================================
TESTING WAKE-UP MECHANISM
======================================================================

Device: 192.168.1.77:55055
Target ID: 160326

This test verifies that the wake-up mechanism works correctly.
The motor should respond to the first command without timing out.
======================================================================

[TEST 1] First command after connection (motor likely sleeping)
----------------------------------------------------------------------
Sending: status.position (first command)
SUCCESS - Got position: 0.0%
  Status: stopped
  Direction: none

Waiting 2 seconds...

[TEST 2] Second command (motor awake, should be fast)
----------------------------------------------------------------------
Sending: status.info
SUCCESS - Got device info:
  Name: Sonesse 30 PoE
  MAC: 4C:C2:06:16:03:26
  Firmware: 5163364A07/5155239A32

[TEST 3] Movement command (stop - harmless)
----------------------------------------------------------------------
Sending: move.stop
SUCCESS - Stop command accepted

[TEST 4] After reconnection (motor may have slept)
----------------------------------------------------------------------
Waiting 3 seconds (simulating idle time)...
Sending: status.position (after reconnect)
SUCCESS - Got position: 0.0%

======================================================================
ALL TESTS PASSED
======================================================================

Wake-up mechanism is working correctly:
  - First commands after connection work without timeout
  - Wake-up command is sent transparently
  - Subsequent commands work without overhead
======================================================================
```

**Run with**:
```bash
# Must be run from HA core directory or have integration in Python path
cd /Users/alanlin/core
python3 working_tests/test_wakeup_mechanism.py

# OR add custom_components to Python path:
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests
PYTHONPATH=/Users/alanlin/core python3 test_wakeup_mechanism.py
```

**Configuration**:
Edit the device configuration in the script:
```python
HOST = "192.168.1.77"
UDP_PORT = 55055
TARGET_ID = "160326"
KEY_HEX = "FBE90399BA25B4B67DC1B23BE0D9C084"
```

**Technical details**:
The wake-up mechanism works by:
1. Detecting when motor might be sleeping (first command after connection/timeout)
2. Sending a harmless `move.stop` command with short timeout to wake motor
3. Proceeding with actual command after motor is awake
4. Only adds ~1s overhead when needed, zero overhead for subsequent commands

**Why wake-up is needed**:
Somfy PoE motors enter hibernation mode after idle periods to save power. When hibernating:
- First command may timeout or be ignored
- Motor takes ~500ms to wake up
- Wake-up mechanism ensures reliability without user noticing

---

#### `test_01_udp_ping_encrypted.py` (VERIFIED WORKING - ENCRYPTED PING)
**Purpose**: Test encrypted ping command (all commands require encryption!)

**What it does**:
- Sends encrypted status.ping request using AES-128-CBC
- Demonstrates that ping REQUIRES encryption (unlike documentation claims)
- Tests basic encrypted communication without full integration client
- Validates encryption key and target ID are correct

**Use this to**:
- Verify encryption setup is working
- Test basic connectivity with encryption
- Confirm motor responds to encrypted commands
- Debug encryption issues

**Expected output**:
```
============================================================
TEST: UDP PING (Encrypted)
============================================================

Plaintext request:
{"method":"status.ping","params":{"targetID":"160326"},"id":1}

Encrypted message: 64 bytes
IV: a1b2c3d4e5f6...

Sent to 192.168.1.77:55055

Waiting for response...

Encrypted response received from ('192.168.1.77', 55055): 32 bytes

Decrypted response:
{"result":true,"id":1}

Parsed JSON:
{
  "result": true,
  "id": 1
}

✓ SUCCESS: Motor responded to encrypted ping
```

**Run with**:
```bash
python3 test_01_udp_ping_encrypted.py
```

**Key Discovery**: This test proves that **ALL commands require encryption**, including ping. The documentation stating ping doesn't need encryption is incorrect.

---

#### `test_decrypt_responses.py` (VERIFIED WORKING - MAIN TEST)
**Purpose**: Send encrypted commands and decrypt/analyze responses

**What it does**:
- Sends move.up, move.stop, move.down commands
- Queries status.position and status.info
- Decrypts and parses all responses
- Shows detailed response data
- Uses zero-padding (the working method)

**Use this to**:
- Verify encryption is working correctly
- Test motor responsiveness
- Debug communication issues
- See actual response data structure

**Expected output**:
```
==========================================
Test: Move motor UP
Method: move.up
==========================================
Sent: move.up
  Response: 64 bytes
  ✓ Decrypted (zero-padding):
    Raw: {"result":"ok","id":1}
    Parsed JSON:
      {
            "result": "ok",
            "id": 1
      }

    ✓ SUCCESS - Result:
      "ok"
```

**Run with**:
```bash
python3 test_decrypt_responses.py
```

---

#### `test_motor_movement_with_position.py` (VERIFIED WORKING - MOVEMENT TEST)
**Purpose**: Test motor movement with real-time position tracking

**WARNING**: This will physically move your motor!

**What it does**:
- Gets initial position
- Moves motor UP for 3 seconds (polls position every 0.3s)
- Stops motor
- Moves motor DOWN for 3 seconds (polls position)
- Stops motor
- Tests move.to command (moves to 50%)
- Tracks position changes in real-time

**Use this to**:
- Verify motor control works end-to-end
- Test position tracking accuracy
- Observe position update frequency
- Test move.to absolute positioning

**Expected output**:
```
[1] Getting initial position...
    Initial position: 25.5%
    Status: stopped
    Direction: none

Press ENTER to move motor UP for 3 seconds...

[2] Sending move.up command...
    Response: ok

  Polling position for 3.0 seconds (every 0.3s)...
  ----------------------------------------------------------------------
  [ 0.00s] Position: 25.500% | Status: moving     | Direction: up
  [ 0.30s] Position: 26.320% | Status: moving     | Direction: up
  [ 0.60s] Position: 27.140% | Status: moving     | Direction: up
  ...
```

**Run with**:
```bash
python3 test_motor_movement_with_position.py
```

---

#### `test_working_encryption.py` (Comparison Test)
**Purpose**: Compare PKCS7 vs zero-padding encryption methods

**What it does**:
- Tests both PKCS7 and zero-padding
- Sends full movement sequence with each method
- Compares response rates and shows why zero-padding works better

**Use this to**:
- Understand which padding method works
- Compare encryption implementations
- Debug padding issues

**Expected output**:
- Zero-padding: 100% success rate
- PKCS7: May fail or get inconsistent responses

**Run with**:
```bash
python3 test_working_encryption.py
```

---

### Diagnostic Tests (Connectivity and Protocol Testing)

#### `test_01_udp_ping.py`
**Purpose**: Test basic UDP communication without encryption

**What it does**:
- Sends unencrypted status.ping request
- Tests basic network connectivity

**Use this to**:
- Verify motor is reachable
- Test UDP port accessibility
- Debug network issues

**Note**: Ping commands don't require encryption according to documentation.

**Run with**:
```bash
python3 test_01_udp_ping.py
```

---

#### `test_02_udp_ping_wildcard.py` - `test_07_tcp_tls_legacy.py`
**Purpose**: Series of diagnostic tests for different protocols and methods

**What they do**:
- Test UDP broadcast discovery
- Test TCP with TLS
- Test HTTPS endpoints
- Port scanning
- Various authentication methods

**Use these to**:
- Diagnose connection issues
- Understand what protocols the motor supports
- Test alternative communication methods

**Run with**:
```bash
python3 test_02_udp_ping_wildcard.py
python3 test_03_tcp_tls_auth.py
# ... etc
```

---

#### `test_somfy_direct.py` (Comprehensive Diagnostics)
**Purpose**: Comprehensive diagnostic test suite

**What it does**:
- Tests TCP plain (without TLS)
- Tests TCP with TLS
- Tests UDP plain
- Tests UDP with authentication
- Tests broadcast discovery
- Tests alternative ports
- Tests different command formats

**Use this to**:
- Diagnose connection issues
- Discover what protocols work
- Test different communication methods

**Expected output**: Test matrix showing which methods work/fail

**Run with**:
```bash
python3 test_somfy_direct.py
```

---

#### Other Legacy Tests
The directory also contains several legacy test files (test_alternative_formats.py, test_port443.py, test_single_command.py, test_udp_encrypted.py, test_working_connection.py) that were used during initial development. These are kept for reference but the main working tests above are recommended.

---

## Troubleshooting

### No Response from Motor

**Symptoms**: Commands send but no response received

**Possible causes**:
1. **Wrong IP address**
   - Solution: Verify motor IP with `ping 192.168.1.77`

2. **Firewall blocking UDP port 55055**
   - Solution: Check firewall rules, allow UDP 55055 bidirectional

3. **Socket not bound with SO_REUSEADDR**
   - Solution: All scripts use this - verify code has:
     ```python
     sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
     sock.bind(("", UDP_PORT))
     ```

4. **Wrong Target ID**
   - Solution: Verify Target ID is last 3 bytes of MAC address
   - Must be STRING, not integer: `"160326"` not `160326`

### Decryption Fails

**Symptoms**: Response received but decryption errors

**Possible causes**:
1. **Wrong encryption key**
   - Solution: Verify key from motor label/documentation

2. **Wrong padding method**
   - Solution: Use zero-padding, not PKCS7
   - Working code uses: `data.rstrip(b'\0')`

3. **Corrupted response**
   - Solution: Check response length is multiple of 16 bytes

### Motor Doesn't Move

**Symptoms**: Commands accepted but motor doesn't move

**Possible causes**:
1. **Motor not commissioned/configured**
   - Solution: Use Somfy configuration tool to set up motor

2. **End limits not set**
   - Solution: Configure motor end limits via physical controls

3. **Motor locked or in error state**
   - Solution: Check motor status with status.info command

4. **Thermal protection active**
   - Solution: Wait for motor to cool down

### Port Already in Use

**Symptoms**: `OSError: [Errno 48] Address already in use`

**This is the MOST COMMON issue!**

**Cause**: Another process (likely Home Assistant) is already using port 55055.

**Solution**:
```bash
# Find what's using port 55055
lsof -i :55055
# or on Linux:
sudo netstat -tulpn | grep 55055

# Stop Home Assistant if it's running
sudo systemctl stop home-assistant
# OR for Docker:
docker stop homeassistant

# OR kill the specific process
kill -9 <PID>
```

**Prevention**: Always stop Home Assistant before running these tests!

## Expected Outputs

### Successful Communication
```
Sent: move.up
  Response: 64 bytes
  ✓ Decrypted (zero-padding):
    Raw: {"result":"ok","id":1}
    ✓ SUCCESS - Result: "ok"
```

### Successful Position Query
```
{
  "result": {
    "position": {
      "value": 45.5,
      "status": "stopped",
      "direction": "none"
    }
  },
  "id": 1
}
```

### Error Response
```
{
  "error": {
    "id": 34,
    "title": "End limits not set"
  },
  "id": 1
}
```

### No Response
```
Sent: move.up
  No response (timeout)
```

## Key Technical Details

### Encryption Specification
- **Algorithm**: AES-128-CBC
- **Key Length**: 128 bits (16 bytes)
- **IV**: Random 16 bytes per message
- **Padding**: Zero-padding (NOT PKCS7)
- **Packet Structure**: `[IV (16 bytes)][Encrypted Data]`

### UDP Communication
- **Port**: 55055 (source and destination)
- **Protocol**: UDP (not TCP)
- **Timeout**: 2-5 seconds recommended
- **Socket Options**: Must bind with SO_REUSEADDR

### JSON-RPC Format
```json
{
  "method": "move.up",
  "params": {
    "targetID": "160326"
  },
  "id": 1
}
```

**Critical**:
- `targetID` must be STRING
- Use compact JSON (no extra spaces): `separators=(",", ":")`
- Request ID can be any integer

### Response Format
```json
{
  "result": "ok",
  "id": 1
}
```

Or with error:
```json
{
  "error": {
    "id": 34,
    "title": "End limits not set"
  },
  "id": 1
}
```

## Common Error Codes

| Code | Title | Meaning |
|------|-------|---------|
| 32 | Device locked | Motor is locked, cannot control |
| 34 | End limits not set | Motor needs calibration |
| 48 | Thermal protection | Motor overheated, cooling down |
| 49 | Obstacle detected | Safety feature activated |
| 255 | Device busy | Motor processing another command |

## Integration Notes for Home Assistant

These tests demonstrate the core functionality that the Home Assistant integration uses:

1. **Encryption**: `test_decrypt_responses.py` shows working encryption/decryption
2. **Movement**: `test_motor_movement_with_position.py` shows position tracking during movement
3. **Commands**: All tests show JSON-RPC command format
4. **Error Handling**: Response parsing shows how to handle errors

The Home Assistant integration uses the same:
- AES-128-CBC encryption with zero-padding
- UDP socket with SO_REUSEADDR on port 55055
- JSON-RPC command format
- Response parsing logic

## Running All Tests

To run a complete test suite:

```bash
#!/bin/bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests

echo "Running diagnostic tests..."
python3 diagnostic_tests/test_somfy_direct.py

echo "\nRunning encryption tests..."
python3 encryption_tests/test_decrypt_responses.py

echo "\nRunning movement tests (WARNING: Motor will move!)..."
read -p "Press ENTER to continue or Ctrl+C to cancel..."
python3 movement_tests/test_motor_movement_with_position.py

echo "\nAll tests complete!"
```

## Safety Warnings

1. **Motor Movement**: Movement tests will physically move your motor
2. **Clear Area**: Ensure the motor path is clear of obstacles
3. **Emergency Stop**: Press Ctrl+C to interrupt and stop motor
4. **Multiple Runs**: Allow motor to cool between test runs
5. **End Limits**: Ensure motor has end limits configured to prevent damage

## Getting Help

If tests fail:

1. Check configuration (IP, Target ID, Key)
2. Verify network connectivity (`ping <motor-ip>`)
3. Check firewall rules
4. Review error messages in output
5. Enable verbose output in scripts
6. Check motor physical status (lights, sounds)

## File Organization

```
working_tests/
├── README.md (this file)
│
├── Main Working Tests (Root):
│   ├── test_ha_integration_debug.py           (VERIFIED - HA integration API test)
│   ├── test_wakeup_mechanism.py               (VERIFIED - wake-up mechanism test)
│   ├── test_01_udp_ping_encrypted.py          (VERIFIED - encrypted ping)
│   └── test_decrypt_responses.py              (VERIFIED - low-level command test)
│
└── Subdirectories:
    ├── diagnostic_tests/
    ├── encryption_tests/
    ├── movement_tests/
    └── status_tests/
```

**Note**: Legacy broken tests have been removed. Only verified working tests remain.

## Next Steps

After verifying these tests work:

1. Verify the integration works: `python3 test_ha_integration_debug.py`
2. Install Home Assistant integration from `custom_components/woow_tech_somfy_cover`
3. Configure via UI (Config Flow) or YAML with same IP, Target ID, and Key
4. Monitor Home Assistant logs for issues
5. Use these test scripts to debug any integration problems

## License

These test scripts are provided as-is for testing and development purposes.

## References

- [Main Project README](../README.md)
- [Testing Documentation](../TESTING.md)
- [Somfy PoE Motor API Documentation](../Somfy%20PoE%20Motor%20API%20for%20Integration.pdf)
