# Testing Guide

**WoowTech Somfy Cover Integration**

Comprehensive testing guide for the integration and standalone test scripts.

---

## Table of Contents

1. [Testing Levels](#testing-levels)
2. [Standalone Test Scripts](#standalone-test-scripts)
3. [Integration Testing](#integration-testing)
4. [Manual Testing Procedures](#manual-testing-procedures)
5. [Automated Testing](#automated-testing)
6. [Troubleshooting Tests](#troubleshooting-tests)

---

## Testing Levels

### Level 1: API Layer Testing (Standalone)

Test the API layer without Home Assistant using standalone scripts in `/working_tests/`.

**Purpose**:
- Verify motor communication
- Test encryption
- Debug protocol issues
- Fast iteration during development

**Tools**: Python scripts that directly use the API layer

---

### Level 2: Integration Testing

Test the full integration within Home Assistant.

**Purpose**:
- Verify coordinator functionality
- Test cover entity behavior
- Validate config flow
- Check YAML configuration

**Tools**: Home Assistant test instance

---

### Level 3: End-to-End Testing

Test complete user workflows.

**Purpose**:
- Verify UI controls work
- Test automations
- Validate position tracking
- Check error handling

**Tools**: Production Home Assistant instance

---

## Standalone Test Scripts

Located in: `/Users/alanlin/Documents/woowtech_somfy_new/working_tests/`

### Available Scripts

#### 1. test_decrypt_responses.py

**Purpose**: Comprehensive motor control test with decryption analysis

**Tests**:
- Move up command
- Move down command
- Stop command
- Position status query
- Device info query

**Usage**:
```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests/
python3 test_decrypt_responses.py
```

**Configuration** (edit in file):
```python
HOST = "192.168.1.77"
TARGET_ID = "160326"
KEY_HEX = "FBE90399BA25B4B67DC1B23BE0D9C084"
```

**Expected Output**:
```
Test: Move motor UP
Sent: move.up
  Response: 64 bytes
  Decrypted: {"result":true,"targetID":"160326","id":1}

Test: Move motor DOWN
Sent: move.down
  Response: 64 bytes
  Decrypted: {"result":true,"targetID":"160326","id":2}

Test: Stop motor
Sent: move.stop
  Response: 64 bytes
  Decrypted: {"result":true,"targetID":"160326","id":3}

Test: Get position
Sent: status.position
  Response: 192 bytes
  Decrypted: {"position":{"value":94.154,"status":"stopped",...},...}

Test: Get device info
Sent: status.info
  Response: 368 bytes
  Decrypted: {"info":{"name":"Sonesse 30 PoE",...},...}
```

---

#### 2. test_wakeup_mechanism.py

**Purpose**: Test motor wake-up handling

**Tests**:
- First command after connection (wake-up)
- Second command (no wake-up needed)
- Movement command
- Reconnection scenario

**Usage**:
```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests/
python3 test_wakeup_mechanism.py
```

**Expected Output**:
```
[TEST 1] First command after connection (motor likely sleeping)
SUCCESS - Got position: 100.0%

[TEST 2] Second command (motor awake, should be fast)
SUCCESS - Got device info: Sonesse 30 PoE

[TEST 3] Movement command (stop - harmless)
SUCCESS - Stop command accepted

[TEST 4] After reconnection (motor may have slept)
SUCCESS - Got position: 100.0%

ALL TESTS PASSED
```

---

#### 3. test_01_udp_ping_encrypted.py

**Purpose**: Test encrypted UDP communication

**Tests**:
- Socket binding to port 55055
- Encryption/decryption
- Basic motor response

**Usage**:
```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests/
python3 test_01_udp_ping_encrypted.py
```

---

#### 4. test_ha_integration_debug.py

**Purpose**: Debug Home Assistant integration issues

**Tests**:
- Coordinator creation
- Client initialization
- Position polling
- Error handling

**Usage**:
```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests/
python3 test_ha_integration_debug.py
```

**Note**: Requires Home Assistant libraries installed

---

### Running All Standalone Tests

```bash
cd /Users/alanlin/Documents/woowtech_somfy_new/working_tests/

# Run each test
for test in test_*.py; do
    echo "Running $test..."
    python3 "$test"
    echo "---"
done
```

---

### Creating Your Own Test Script

Template:
```python
#!/usr/bin/env python3
"""Custom test script for Somfy motor."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from custom_components.woow_tech_somfy_cover.api.client import SomfyClient

# Configuration
HOST = "192.168.1.77"
TARGET_ID = "160326"
KEY_HEX = "FBE90399BA25B4B67DC1B23BE0D9C084"

async def main():
    """Run test."""
    client = SomfyClient(host=HOST, target_id=TARGET_ID, key=KEY_HEX)

    try:
        await client.connect()
        print("Connected")

        # Your test code here
        status = await client.get_position()
        print(f"Position: {status.position}%")

    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Integration Testing

### Setup Test Environment

**Option 1: Development Container**
```bash
# Using Home Assistant dev container
git clone https://github.com/home-assistant/core.git
cd core
# Follow HA dev setup instructions
```

**Option 2: Separate Test Instance**
```bash
# Create test HA instance
mkdir ~/ha-test
cd ~/ha-test
python3 -m venv venv
source venv/bin/activate
pip install homeassistant
```

---

### Install Integration

```bash
# Copy integration to custom_components
cp -r /Users/alanlin/Documents/woowtech_somfy_new/custom_components/woow_tech_somfy_cover \
      ~/ha-test/config/custom_components/
```

---

### Enable Debug Logging

**configuration.yaml**:
```yaml
logger:
  default: warning
  logs:
    custom_components.woow_tech_somfy_cover: debug
    custom_components.woow_tech_somfy_cover.api: debug
    custom_components.woow_tech_somfy_cover.coordinator: debug
    custom_components.woow_tech_somfy_cover.cover: debug
    custom_components.woow_tech_somfy_cover.config_flow: debug
```

---

### Test Config Flow

1. Start Home Assistant
2. Go to Settings → Devices & Services
3. Click "+ ADD INTEGRATION"
4. Search for "WoowTech Somfy Cover"
5. Fill in form:
   - Name: Test Motor
   - Host: 192.168.1.77
   - Target ID: 160326
   - Key: FBE90399BA25B4B67DC1B23BE0D9C084
6. Click Submit

**Check Logs**:
```bash
tail -f home-assistant.log | grep woow_tech_somfy_cover
```

**Expected Log Entries**:
```
[custom_components.woow_tech_somfy_cover] Setting up WoowTech Somfy Cover integration
[custom_components.woow_tech_somfy_cover.api.client] Initialized SomfyClient
[custom_components.woow_tech_somfy_cover.api.transport] Transport ready: can bind to port 55055
[custom_components.woow_tech_somfy_cover.coordinator] Initialized coordinator
[custom_components.woow_tech_somfy_cover] Successfully connected to Somfy motor
```

---

### Test YAML Configuration

**configuration.yaml**:
```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Test Motor YAML
    host: 192.168.1.77
    target_id: "160326"
    key: "FBE90399BA25B4B67DC1B23BE0D9C084"
```

1. Check configuration: Developer Tools → YAML → Check Configuration
2. Restart Home Assistant
3. Verify entity appears: `cover.test_motor_yaml`

**Check Logs**:
```bash
tail -f home-assistant.log | grep "test_motor_yaml"
```

---

### Test Cover Entity

**Manual Testing**:
1. Go to entity page: `cover.test_motor`
2. Click **OPEN** → Motor should move up
3. Click **STOP** → Motor should stop
4. Click **CLOSE** → Motor should move down
5. Drag position slider → Motor should move to position

**Automation Testing**:
```yaml
# configuration.yaml
automation:
  - alias: "Test Cover Open"
    trigger:
      - platform: state
        entity_id: input_boolean.test_trigger
        to: "on"
    action:
      - service: cover.open_cover
        target:
          entity_id: cover.test_motor
```

---

## Manual Testing Procedures

### Test Plan: Basic Functionality

**Duration**: 30 minutes

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|----------------|-----------|
| **Installation** | Copy integration to custom_components, restart HA | No errors in logs | ☐ |
| **Config Flow** | Add integration via UI | Device created, entity appears | ☐ |
| **YAML Config** | Add cover in configuration.yaml | Entity appears after restart | ☐ |
| **Open Command** | Click OPEN button | Motor moves up | ☐ |
| **Close Command** | Click CLOSE button | Motor moves down | ☐ |
| **Stop Command** | Click STOP while moving | Motor stops immediately | ☐ |
| **Position Display** | Check position value | Shows 0-100, updates during movement | ☐ |
| **Position Control** | Set position slider to 50% | Motor moves to 50% | ☐ |
| **State Display** | Check state during movement | Shows OPENING/CLOSING/OPEN/CLOSED | ☐ |

---

### Test Plan: Advanced Functionality

**Duration**: 45 minutes

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|----------------|-----------|
| **Wake-up** | Wait 5 min, send command | Command succeeds (may be slow) | ☐ |
| **Fast Polling** | Start movement, watch logs | Polling switches to 2s | ☐ |
| **Normal Polling** | Motor stopped, watch logs | Polling at 30s | ☐ |
| **Position Accuracy** | Set 25%, 50%, 75% | Motor stops at correct positions | ☐ |
| **Multiple Commands** | Send open, immediate stop | Both commands execute | ☐ |
| **Error Recovery** | Disconnect network, reconnect | Entity becomes available again | ☐ |
| **Reload** | Reload integration | No errors, entity remains functional | ☐ |
| **Restart HA** | Restart Home Assistant | Integration loads, entity works | ☐ |

---

### Test Plan: Error Handling

**Duration**: 30 minutes

| Test | Steps | Expected Result | Pass/Fail |
|------|-------|----------------|-----------|
| **Invalid IP** | Configure with wrong IP | "cannot_connect" error | ☐ |
| **Invalid Target ID** | Enter 5-char or 7-char ID | "invalid_target_id" error | ☐ |
| **Invalid Key** | Enter 31-char or 33-char key | "invalid_key" error | ☐ |
| **Network Loss** | Disconnect motor from network | Entity becomes unavailable | ☐ |
| **Motor Off** | Power off motor | Entity becomes unavailable | ☐ |
| **Duplicate Entry** | Add same target_id twice | "already_configured" error | ☐ |
| **Port Conflict** | Run test script while HA running | One succeeds, other retries/fails | ☐ |

---

### Test Plan: Performance

**Duration**: 60 minutes

| Test | Metric | Target | Actual | Pass/Fail |
|------|--------|--------|--------|-----------|
| **Command Latency** | Time from click to motor movement | < 500ms | | ☐ |
| **Position Query** | Time to get position | < 200ms | | ☐ |
| **First Command** | Time for first command after idle | < 2s | | ☐ |
| **Poll Interval (Moving)** | Coordinator update frequency | 2s ± 0.5s | | ☐ |
| **Poll Interval (Stopped)** | Coordinator update frequency | 30s ± 2s | | ☐ |
| **Memory Usage** | Integration memory footprint | < 5 MB | | ☐ |
| **CPU Usage** | CPU % during polling | < 1% | | ☐ |

---

## Automated Testing

### Unit Tests

**Location**: `/Users/alanlin/Documents/woowtech_somfy_new/tests/` (to be created)

**Example Test**:
```python
"""Test encryption module."""
import pytest
from custom_components.woow_tech_somfy_cover.api.encryption import SomfyEncryption

def test_encrypt_decrypt():
    """Test encryption round-trip."""
    enc = SomfyEncryption("FBE90399BA25B4B67DC1B23BE0D9C084")

    plaintext = '{"method":"move.up","params":{"targetID":"160326"},"id":1}'
    encrypted = enc.encrypt(plaintext)
    decrypted = enc.decrypt(encrypted)

    assert decrypted == plaintext

def test_invalid_key():
    """Test invalid key raises error."""
    with pytest.raises(ValueError):
        SomfyEncryption("INVALID")
```

**Run Tests**:
```bash
cd /Users/alanlin/Documents/woowtech_somfy_new
pytest tests/
```

---

### Integration Tests

**Example**:
```python
"""Test coordinator."""
import pytest
from homeassistant.core import HomeAssistant
from custom_components.woow_tech_somfy_cover.coordinator import SomfyDataUpdateCoordinator

@pytest.mark.asyncio
async def test_coordinator_update(hass: HomeAssistant, mock_client):
    """Test coordinator update cycle."""
    coordinator = SomfyDataUpdateCoordinator(hass, mock_client, {
        "name": "Test",
        "host": "192.168.1.77",
        "target_id": "160326"
    })

    await coordinator.async_config_entry_first_refresh()

    assert coordinator.data is not None
    assert coordinator.data.position == 50.0
```

---

### CI/CD Pipeline

**GitHub Actions** (example):
```yaml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r requirements_test.txt
      - run: pytest tests/
      - run: pylint custom_components/
      - run: black --check custom_components/
```

---

## Troubleshooting Tests

### Test Fails: "Cannot bind to port 55055"

**Cause**: Another process is using the port

**Solution**:
```bash
# Find process using port
lsof -i :55055

# Kill process (if safe)
kill -9 <PID>

# Or use different test instance
```

---

### Test Fails: "Motor timeout"

**Cause**: Motor sleeping or network issue

**Solution**:
1. Wait 2-3 seconds and retry (wake-up)
2. Check network connectivity: `ping 192.168.1.77`
3. Verify motor powered on
4. Check firewall rules

---

### Test Fails: "Invalid target_id"

**Cause**: Wrong format or value

**Solution**:
- Verify format: exactly 6 hex characters
- Check value: derived from MAC address
- Example: MAC `4C:C2:06:16:03:26` → Target ID `160326`

---

### Test Passes Standalone, Fails in HA

**Cause**: Integration layer issue

**Solution**:
1. Enable debug logging
2. Check coordinator logs
3. Verify cover entity setup
4. Check for config conflicts (YAML vs Config Flow)

---

### Inconsistent Test Results

**Cause**: Motor sleep state varies

**Solution**:
- Run tests multiple times
- Use wake-up mechanism (automatic in v1.0.0+)
- Add delays between tests
- Power cycle motor between test runs

---

## Test Data Collection

### Logging Test Results

Enable detailed logging:
```yaml
logger:
  default: warning
  logs:
    custom_components.woow_tech_somfy_cover: debug
```

**Collect**:
- Home Assistant version
- Integration version
- Motor model and firmware
- Test results (pass/fail)
- Log excerpts (remove sensitive data)

---

### Performance Metrics

Measure and record:
- Command latency (ms)
- Position query time (ms)
- First command delay (ms)
- Poll intervals (s)
- Memory usage (MB)
- CPU usage (%)

**Tools**:
```bash
# Monitor HA process
top -p $(pgrep -f "home-assistant")

# Monitor logs for timing
tail -f home-assistant.log | grep -E "(Sending|Received|took)"
```

---

## Test Checklist

### Before Release

- [ ] All standalone tests pass
- [ ] Config Flow tested (add/remove/reconfigure)
- [ ] YAML configuration tested (single/multiple motors)
- [ ] All cover controls work (open/close/stop/position)
- [ ] Position tracking accurate
- [ ] State display correct
- [ ] Wake-up mechanism works
- [ ] Adaptive polling works (2s moving, 30s stopped)
- [ ] Error handling tested (network loss, invalid input)
- [ ] Multiple motors tested
- [ ] Integration reload tested
- [ ] Home Assistant restart tested
- [ ] Logs clean (no errors/warnings)
- [ ] Documentation reviewed
- [ ] Version bumped

---

## Continuous Testing

### Daily Checks

- [ ] Entity available in HA
- [ ] Commands respond quickly
- [ ] Position updates accurately
- [ ] No errors in logs

### Weekly Checks

- [ ] Test all controls (open/close/stop/position)
- [ ] Verify automations still work
- [ ] Check for HA updates affecting integration
- [ ] Review logs for warnings

### Monthly Checks

- [ ] Test error recovery (network disconnect)
- [ ] Verify performance (latency, CPU, memory)
- [ ] Check for integration updates
- [ ] Review and update documentation

---

## Getting Help with Testing

If tests fail:

1. **Collect Information**:
   - Integration version
   - Home Assistant version
   - Motor model and firmware
   - Test that failed
   - Log output (with sensitive data removed)

2. **Check Documentation**:
   - README.md
   - CONFIGURATION.md
   - API_REFERENCE.md
   - This file (TESTING.md)

3. **Search Issues**:
   - GitHub issues for similar problems
   - Home Assistant forums

4. **Report Issue**:
   - Create GitHub issue with collected information
   - Include steps to reproduce
   - Attach relevant logs

---

## Summary

Testing the WoowTech Somfy Cover integration involves:

1. **Standalone testing**: Fast iteration with test scripts
2. **Integration testing**: Verify HA components work
3. **Manual testing**: User workflow validation
4. **Automated testing**: Regression prevention
5. **Performance testing**: Ensure efficiency
6. **Error testing**: Verify robustness

**Test often, test thoroughly, report issues clearly.**
