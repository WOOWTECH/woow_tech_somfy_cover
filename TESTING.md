# Testing Guide - Somfy PoE Integration

Comprehensive guide for testing the Somfy PoE motor integration at all levels.

## Table of Contents

1. [Test Philosophy](#test-philosophy)
2. [Prerequisites](#prerequisites)
3. [Test Levels](#test-levels)
4. [Standalone Tests](#standalone-tests)
5. [Integration Tests](#integration-tests)
6. [Test Matrix](#test-matrix)
7. [Continuous Testing](#continuous-testing)
8. [Troubleshooting Tests](#troubleshooting-tests)

## Test Philosophy

This integration uses a **bottom-up testing approach**:

1. **Layer 1**: Network connectivity (can we reach the motor?)
2. **Layer 2**: Encryption (can we encrypt/decrypt messages?)
3. **Layer 3**: Protocol (can we send valid commands?)
4. **Layer 4**: Motor control (does the motor physically respond?)
5. **Layer 5**: Integration (does Home Assistant work correctly?)

Each layer builds on the previous one, making it easy to isolate issues.

## Prerequisites

### Stop Home Assistant First!

**CRITICAL**: Only ONE process can use UDP port 55055 at a time.

```bash
# Stop Home Assistant
sudo systemctl stop home-assistant
# OR if using Docker:
docker stop homeassistant

# Verify port is free
lsof -i :55055
# Should return nothing
```

### Install Dependencies

```bash
# For standalone tests
pip install cryptography

# For integration tests (optional)
pip install pytest pytest-asyncio pytest-homeassistant-custom-component
```

### Configuration

You'll need:
- **Motor IP**: e.g., `192.168.1.77`
- **Target ID**: e.g., `"160326"` (STRING!)
- **Encryption Key**: e.g., `"FBE90399BA25B4B67DC1B23BE0D9C084"`

## Test Levels

### Level 1: Connectivity Tests

**Goal**: Verify basic network connectivity to the motor.

```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests

# Test 1: Network ping
ping 192.168.1.77

# Test 2: UDP ping (unencrypted)
python3 test_01_udp_ping.py
```

**Expected Results**:
- Network ping: < 10ms response time
- UDP ping: Should receive response (even if it's an error)

**If fails**: Check network, firewall, motor power

---

### Level 2: Encryption Tests

**Goal**: Verify encryption and decryption work correctly.

```bash
# Test 3: Basic encrypted communication
python3 test_05_udp_encrypted.py

# Test 4: Padding comparison (PKCS7 vs zero-padding)
python3 test_working_encryption.py
```

**Expected Results**:
- Zero-padding: 100% success rate
- PKCS7: May work but less reliable
- Responses decrypt successfully to valid JSON

**If fails**: Check encryption key, verify target ID is STRING

---

### Level 3: Protocol Tests

**Goal**: Verify JSON-RPC commands are formatted correctly.

```bash
# Test 5: Command formatting and response decryption
python3 test_decrypt_responses.py
```

**Expected Results**:
- All commands send successfully
- All responses decrypt to valid JSON
- Responses contain `result` or `error` fields
- Request IDs match in responses

**If fails**: Check JSON formatting, target ID format

---

### Level 4: Motor Control Tests

**Goal**: Verify motor physically responds to commands.

```bash
# Test 6: Motor movement (WARNING: Motor will move!)
python3 test_motor_movement_with_position.py
```

**Expected Results**:
- Motor physically moves UP when commanded
- Motor physically moves DOWN when commanded
- Motor stops when commanded
- Position values update in real-time
- Move.to command moves to specific position

**If fails**: Check end limits, motor status, physical obstructions

---

### Level 5: Integration Tests

**Goal**: Verify Home Assistant integration works end-to-end.

```bash
# Start Home Assistant
sudo systemctl start home-assistant

# Check logs
tail -f /config/home-assistant.log | grep somfy_poe

# Manual testing in HA UI:
# 1. Add integration via UI
# 2. Configure with motor details
# 3. Test open/close/stop buttons
# 4. Test position slider
# 5. Observe state updates
```

**Expected Results**:
- Integration adds successfully
- Cover entity appears
- Commands execute within 1 second
- Position updates during movement
- UI reflects motor state accurately

**If fails**: Check HA logs, verify config, re-run standalone tests

---

## Standalone Tests

Detailed documentation for each standalone test script.

### Quick Test (5 minutes)

The fastest way to verify everything works:

```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests

# 1. Configure your motor IP/ID/Key in test_decrypt_responses.py
# 2. Run the test
python3 test_decrypt_responses.py

# Should show:
# - All commands send successfully
# - All responses decrypt
# - Motor should MOVE (you'll hear/see it)
```

### Full Test Suite (15 minutes)

Complete test of all functionality:

```bash
#!/bin/bash
# save as run_all_tests.sh

cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests

echo "=== CONNECTIVITY TESTS ==="
python3 test_01_udp_ping.py

echo "\n=== ENCRYPTION TESTS ==="
python3 test_05_udp_encrypted.py

echo "\n=== PROTOCOL TESTS ==="
python3 test_decrypt_responses.py

echo "\n=== MOTOR CONTROL TESTS ==="
read -p "Press ENTER to test motor movement (motor will move!) or Ctrl+C to skip..."
python3 test_motor_movement_with_position.py

echo "\n=== DIAGNOSTIC TESTS ==="
python3 test_somfy_direct.py

echo "\n=== ALL TESTS COMPLETE ==="
```

### Test Output Examples

#### Successful Test Output

```
======================================================================
DECRYPT AND ANALYZE MOTOR RESPONSES
======================================================================

Device: 192.168.1.77:55055
Target ID: 160326

======================================================================
Test: Move motor UP
Method: move.up
======================================================================
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

#### Failed Test Output

```
======================================================================
Test: Move motor UP
Method: move.up
======================================================================
Sent: move.up
  ✗ No response (timeout)
```

Or:

```
Sent: move.up
  Response: 64 bytes
  ✗ Could not decrypt with zero-padding: Invalid padding
  ✗ Could not decrypt with PKCS7: Invalid padding
  Raw response: a1b2c3d4...
```

## Integration Tests

### Manual Integration Testing

After adding the integration to Home Assistant:

#### Test Checklist

- [ ] **Installation**
  - [ ] Integration appears in list
  - [ ] Config flow completes without errors
  - [ ] Device appears in Devices page
  - [ ] Cover entity is created

- [ ] **Basic Commands**
  - [ ] Open button works
  - [ ] Close button works
  - [ ] Stop button works
  - [ ] Commands execute within 1 second
  - [ ] No errors in logs

- [ ] **Position Control**
  - [ ] Position slider appears
  - [ ] Can set position to 0%
  - [ ] Can set position to 50%
  - [ ] Can set position to 100%
  - [ ] Motor moves to requested position
  - [ ] Position is accurate (±2%)

- [ ] **State Updates**
  - [ ] State shows "opening" during up movement
  - [ ] State shows "closing" during down movement
  - [ ] State shows "open" or "closed" when stopped
  - [ ] Position updates during movement (every 2s)
  - [ ] Position updates when stopped (every 30s)

- [ ] **Error Handling**
  - [ ] Timeout shows entity as unavailable
  - [ ] Network error recovers automatically
  - [ ] Invalid command shows error in log
  - [ ] Motor error (e.g., obstacle) displays in UI

- [ ] **Edge Cases**
  - [ ] Rapid commands (open/stop/close) work
  - [ ] Multiple position changes in sequence work
  - [ ] Home Assistant restart preserves config
  - [ ] Integration reload works
  - [ ] Removing integration cleans up properly

### Automated Integration Testing

If you have pytest configured:

```bash
# Run integration tests
pytest tests/

# Run with coverage
pytest --cov=custom_components.somfy_poe tests/

# Run specific test
pytest tests/test_cover.py -v
```

## Test Matrix

### Compatibility Matrix

| Component | Tested | Working | Notes |
|-----------|--------|---------|-------|
| **Motors** |
| Somfy Sonesse 30 PoE | ✓ | ✓ | Fully tested |
| Somfy Sonesse 40 PoE | ✗ | ? | Should work (untested) |
| Somfy Curtain PoE | ✗ | ? | Should work (untested) |
| **Platforms** |
| Home Assistant 2024.x | ✓ | ✓ | Tested |
| Home Assistant 2023.x | ✗ | ? | Should work (untested) |
| **Python** |
| Python 3.11 | ✓ | ✓ | Tested |
| Python 3.10 | ✗ | ? | Should work (untested) |
| Python 3.9 | ✗ | ? | Should work (untested) |
| **Networks** |
| IPv4 LAN | ✓ | ✓ | Tested |
| IPv6 | ✗ | ? | Untested |
| WiFi | ✓ | ✓ | Tested |
| Ethernet | ✗ | ? | Should work (untested) |

### Feature Matrix

| Feature | Status | Test File | Notes |
|---------|--------|-----------|-------|
| **Commands** |
| move.up | ✓ Working | test_decrypt_responses.py | Tested |
| move.down | ✓ Working | test_decrypt_responses.py | Tested |
| move.stop | ✓ Working | test_decrypt_responses.py | Tested |
| move.to | ✓ Working | test_motor_movement_with_position.py | Tested |
| status.position | ✓ Working | test_decrypt_responses.py | Tested |
| status.info | ✓ Working | test_decrypt_responses.py | Tested |
| **Encryption** |
| AES-128-CBC | ✓ Working | test_working_encryption.py | Tested |
| Zero-padding | ✓ Working | All tests | Tested |
| PKCS7 padding | ⚠ Partial | test_working_encryption.py | Works but unreliable |
| **Protocols** |
| UDP port 55055 | ✓ Working | All tests | Tested |
| TCP/TLS | ✗ Failed | test_03_tcp_tls_auth.py | Not supported |
| HTTPS | ✗ Failed | test_04_https_check.py | Not supported |
| **Features** |
| Position tracking | ✓ Working | test_motor_movement_with_position.py | Tested |
| Real-time updates | ✓ Working | HA integration | Tested |
| Adaptive polling | ✓ Working | HA integration | Tested |
| Error handling | ✓ Working | All tests | Tested |

## Continuous Testing

### Before Each Commit

Run quick smoke test:

```bash
cd working_tests/
python3 test_decrypt_responses.py
```

Should complete in < 30 seconds with all tests passing.

### Before Each Release

Run full test suite:

```bash
cd working_tests/
./run_all_tests.sh  # (create this script from Full Test Suite above)
```

Should complete in < 15 minutes with all tests passing.

### Regression Testing

After any code changes:

1. Run all standalone tests
2. Test in Home Assistant
3. Verify no new errors in logs
4. Test all commands work
5. Verify position tracking works

## Troubleshooting Tests

### Test Fails: Connection Timeout

**Symptoms**: Test sends command but receives no response

**Diagnosis**:
```bash
# Check network
ping 192.168.1.77

# Check port
lsof -i :55055

# Check firewall
sudo iptables -L | grep 55055  # Linux
sudo pfctl -s rules | grep 55055  # macOS
```

**Solutions**:
1. Verify motor IP is correct
2. Check motor is powered on
3. Verify no firewall blocking
4. Stop other processes using port 55055

---

### Test Fails: Decryption Error

**Symptoms**: Response received but can't decrypt

**Diagnosis**:
```bash
# Verify encryption key
# Key should be exactly 32 hex characters
echo "FBE90399BA25B4B67DC1B23BE0D9C084" | wc -c
# Should output: 33 (32 chars + newline)
```

**Solutions**:
1. Verify encryption key from motor label
2. Check key has no spaces or dashes
3. Ensure key is uppercase hex (0-9, A-F)
4. Try zero-padding if PKCS7 fails

---

### Test Fails: Motor Doesn't Move

**Symptoms**: Commands accepted but motor doesn't physically move

**Diagnosis**:
```bash
# Check motor status
python3 test_decrypt_responses.py | grep -A10 "status.info"

# Look for:
# - End limits set?
# - Motor locked?
# - Error state?
```

**Solutions**:
1. Configure end limits on motor
2. Check for physical obstructions
3. Verify motor is not in error state
4. Try physical controls to verify motor works

---

### Test Fails: Port In Use

**Symptoms**: `OSError: [Errno 48] Address already in use`

**Diagnosis**:
```bash
# Find what's using the port
lsof -i :55055
```

**Solutions**:
```bash
# Stop Home Assistant
sudo systemctl stop home-assistant

# Or kill specific process
kill -9 <PID>

# Or wait 30 seconds for socket to close
```

---

### Test Fails: Invalid Target ID

**Symptoms**: Commands timeout or receive errors

**Diagnosis**:
```python
# Verify target ID format
TARGET_ID = "160326"  # CORRECT (string)
# NOT:
TARGET_ID = 160326  # WRONG (integer)
```

**Solutions**:
1. Ensure target ID is a STRING
2. Verify it's last 3 bytes of MAC
3. Use exact format: 6 hex chars, no colons
4. Check JSON has: `{"targetID": "160326"}`

---

## Test Environment Setup

### Recommended Test Setup

```
┌─────────────────┐
│  Test Machine   │
│  (Laptop/PC)    │
│                 │
│  - Python 3.11  │
│  - Test scripts │
└────────┬────────┘
         │
         │ WiFi/Ethernet
         │
┌────────┴────────┐
│    Network      │
│    Router       │
└────────┬────────┘
         │
         │ PoE
         │
┌────────┴────────┐
│  Somfy Motor    │
│  192.168.1.77   │
└─────────────────┘
```

### Test Network Requirements

- **Same subnet**: Test machine and motor must be on same network
- **No VLANs**: Avoid VLAN segmentation during testing
- **No firewalls**: Disable firewall rules for port 55055 during testing
- **Static IP**: Assign static IP to motor for consistent testing

### Test Data Logging

Enable logging during tests for debugging:

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='somfy_test.log'
)
```

## Performance Testing

### Response Time Test

Measure command response times:

```python
import time

start = time.time()
response = send_command("move.up")
elapsed = time.time() - start

print(f"Response time: {elapsed*1000:.2f}ms")
# Should be < 100ms
```

### Throughput Test

Test rapid command succession:

```python
for i in range(10):
    response = send_command("status.position")
    time.sleep(0.1)

# All commands should succeed
# No timeouts or errors
```

### Stress Test

Test continuous operation:

```python
# Run for 1 hour
for i in range(3600):
    response = send_command("status.position")
    time.sleep(1)

# Should maintain stable performance
# No memory leaks or degradation
```

## Test Best Practices

1. **Always stop Home Assistant** before running standalone tests
2. **Test incrementally** - don't skip levels
3. **Log everything** during development
4. **Clear area** before motor movement tests
5. **Use version control** - commit working states
6. **Document failures** - note what didn't work
7. **Test on real hardware** - simulators aren't enough
8. **Verify physically** - don't just trust logs
9. **Test error cases** - disconnect network, wrong keys, etc.
10. **Automate** - script repetitive tests

## CI/CD Notes

For automated testing in CI/CD:

- **Cannot test motor control** (requires physical hardware)
- **Can test**: Encryption, protocol, JSON formatting
- **Mock motor responses** for unit tests
- **Use pytest fixtures** for test data
- **Separate integration tests** from unit tests

Example CI workflow:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements.txt
      - run: pytest tests/ --ignore=tests/integration
```

## Summary

**Quick Test** (every change):
```bash
python3 working_tests/test_decrypt_responses.py
```

**Full Test** (before release):
```bash
./working_tests/run_all_tests.sh
```

**Integration Test** (with Home Assistant):
- Manual UI testing
- Check all commands work
- Verify position tracking
- Test error handling

**Remember**: Always stop Home Assistant before running standalone tests!

---

For more details on specific tests, see [working_tests/README.md](working_tests/README.md).
