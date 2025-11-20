# Development Guide - Somfy PoE Integration

Comprehensive guide for developers working on the Somfy PoE Home Assistant integration.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Code Structure](#code-structure)
3. [Architecture Deep Dive](#architecture-deep-dive)
4. [Adding New Features](#adding-new-features)
5. [Debugging Tips](#debugging-tips)
6. [Common Pitfalls](#common-pitfalls)
7. [Code Style](#code-style)
8. [Testing During Development](#testing-during-development)

## Development Environment Setup

### Prerequisites

- Python 3.11 or higher
- Git
- Home Assistant development instance (optional)
- Physical Somfy PoE motor for testing

### Initial Setup

```bash
# Clone the repository
git clone <repository-url>
cd woowtech_somfy_new

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install cryptography
pip install homeassistant  # Optional, for full HA testing

# Install development dependencies (optional)
pip install pytest pytest-asyncio black isort pylint mypy
```

### IDE Setup

#### VS Code

Recommended extensions:
- Python (Microsoft)
- Pylance
- Python Test Explorer

`.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.linting.pylintArgs": [
    "--max-line-length=100",
    "--disable=C0111"
  ],
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

#### PyCharm

1. Open project folder
2. Configure Python interpreter (select venv)
3. Enable pylint inspection
4. Set code style to Black

### Running in Development Mode

#### Option 1: Standalone Scripts (Fastest)

```bash
cd working_tests/

# Edit configuration in script
vim test_decrypt_responses.py
# Update HOST, TARGET_ID, KEY_HEX

# Run test
python3 test_decrypt_responses.py
```

This is the fastest way to test changes without Home Assistant.

#### Option 2: Home Assistant Development Mode

```bash
# Link integration to HA config folder
ln -s $(pwd)/custom_components/somfy_poe ~/.homeassistant/custom_components/

# Or copy
cp -r custom_components/somfy_poe ~/.homeassistant/custom_components/

# Restart Home Assistant
ha core restart

# Watch logs
tail -f ~/.homeassistant/home-assistant.log | grep somfy_poe
```

#### Option 3: Home Assistant Container

```bash
# Create docker-compose.yml
version: '3'
services:
  homeassistant:
    container_name: homeassistant
    image: homeassistant/home-assistant:latest
    volumes:
      - ./config:/config
      - ./custom_components/somfy_poe:/config/custom_components/somfy_poe
    network_mode: host
    restart: unless-stopped
```

## Code Structure

### Project Layout

```
woowtech_somfy_new/
├── custom_components/somfy_poe/    # Home Assistant integration
│   ├── __init__.py                 # Component setup
│   ├── manifest.json               # Integration metadata
│   ├── config_flow.py              # UI configuration flow
│   ├── coordinator.py              # Data update coordinator
│   ├── cover.py                    # Cover entity implementation
│   ├── const.py                    # Constants and configuration
│   ├── errors.py                   # Custom exceptions
│   └── api/                        # Protocol implementation
│       ├── __init__.py
│       ├── client.py               # High-level API client
│       ├── encryption.py           # AES-128-CBC encryption
│       ├── transport.py            # UDP socket handling
│       ├── protocol.py             # JSON-RPC protocol
│       ├── models.py               # Data models
│       └── exceptions.py           # API exceptions
├── working_tests/                  # Standalone test scripts
├── tests/                          # Integration tests
├── README.md                       # Main documentation
├── TESTING.md                      # Testing guide
└── DEVELOPMENT.md                  # This file
```

### Module Responsibilities

#### Home Assistant Layer

**`__init__.py`**
- Integration entry point
- Creates SomfyClient and coordinator
- Registers platforms (cover)
- Handles setup and teardown

**`config_flow.py`**
- UI-based configuration
- Input validation
- Device discovery (future)
- Configuration update/reconfigure

**`coordinator.py`**
- Manages data updates
- Adaptive polling (2s moving, 30s stopped)
- Command execution
- State management

**`cover.py`**
- Home Assistant cover entity
- Translates HA commands to API calls
- Position conversion (HA vs Somfy)
- State reporting

**`const.py`**
- Configuration keys
- Default values
- Method names
- Constants

#### API Layer

**`client.py`**
- High-level API interface
- Wraps protocol/transport/encryption
- Type-safe return values
- Error handling

**`encryption.py`**
- AES-128-CBC encryption
- Zero-padding (NOT PKCS7)
- IV generation
- Encrypt/decrypt functions

**`transport.py`**
- UDP socket management
- Port 55055 binding
- SO_REUSEADDR option
- Send/receive with timeout

**`protocol.py`**
- JSON-RPC message building
- Request/response parsing
- Target ID formatting (STRING!)
- Compact JSON serialization

**`models.py`**
- PositionStatus dataclass
- DeviceInfo dataclass
- MovementState enum
- Direction enum

**`exceptions.py`**
- Custom exception hierarchy
- API error codes
- Error messages

## Architecture Deep Dive

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Home Assistant                                              │
│                                                             │
│  ┌──────────┐   commands    ┌─────────────┐              │
│  │  User    │──────────────>│  Cover      │              │
│  │   UI     │<──────────────│  Entity     │              │
│  └──────────┘    state       └──────┬──────┘              │
│                                      │                      │
│                                      │ async calls          │
│                                      v                      │
│                            ┌──────────────────┐            │
│                            │  Coordinator     │            │
│                            │  - Polling       │            │
│                            │  - State cache   │            │
│                            └────────┬─────────┘            │
│                                     │                      │
└─────────────────────────────────────┼──────────────────────┘
                                      │
                                      │ async API calls
                                      v
┌─────────────────────────────────────────────────────────────┐
│ API Layer (custom_components/somfy_poe/api/)               │
│                                                             │
│  ┌──────────────┐                                          │
│  │  SomfyClient │  Orchestrates everything                 │
│  └──────┬───────┘                                          │
│         │                                                   │
│         ├──> ┌──────────┐  Builds JSON-RPC                │
│         │    │ Protocol │  {"method":"move.up",...}       │
│         │    └──────────┘                                  │
│         │                                                   │
│         ├──> ┌─────────────┐  AES-128-CBC                 │
│         │    │ Encryption  │  Zero-padding                │
│         │    └─────────────┘                               │
│         │                                                   │
│         └──> ┌───────────┐  UDP socket                    │
│              │ Transport │  Port 55055                    │
│              └───────────┘  SO_REUSEADDR                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                                      │
                                      │ UDP packets
                                      v
                              ┌──────────────┐
                              │ Somfy Motor  │
                              │ 192.168.1.77 │
                              └──────────────┘
```

### Encryption Flow

```python
# Sending a command
message = {
    "method": "move.up",
    "params": {"targetID": "160326"},  # STRING!
    "id": 1
}

# 1. Serialize to compact JSON
json_str = json.dumps(message, separators=(",", ":"))
# '{"method":"move.up","params":{"targetID":"160326"},"id":1}'

# 2. Encode to bytes
plaintext = json_str.encode("utf-8")

# 3. Zero-padding to 16-byte blocks
padding_needed = -len(plaintext) % 16
padded = plaintext + b"\0" * padding_needed

# 4. Generate random IV
iv = os.urandom(16)

# 5. Encrypt with AES-128-CBC
cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
encryptor = cipher.encryptor()
ciphertext = encryptor.update(padded) + encryptor.finalize()

# 6. Combine IV + ciphertext
encrypted_packet = iv + ciphertext

# 7. Send via UDP
sock.sendto(encrypted_packet, (host, 55055))
```

### Response Decryption Flow

```python
# Receiving a response
response_packet = sock.recvfrom(4096)

# 1. Split IV and ciphertext
iv = response_packet[:16]
ciphertext = response_packet[16:]

# 2. Decrypt
cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
decryptor = cipher.decryptor()
padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

# 3. Remove zero-padding
plaintext = padded_plaintext.rstrip(b'\0')

# 4. Decode to string
json_str = plaintext.decode("utf-8")

# 5. Parse JSON
response = json.loads(json_str)
# {"result":"ok","id":1}
```

### Coordinator Polling Strategy

```python
# Adaptive polling based on motor state

if motor_is_moving:
    # Fast polling during movement
    update_interval = 2 seconds
else:
    # Slow polling when idle
    update_interval = 30 seconds

# Automatically switches based on motor state
# Minimizes network traffic
# Ensures responsive UI during movement
```

## Adding New Features

### Adding a New Command

1. **Add method constant** to `const.py`:
```python
METHOD_MOVE_PRESET_1 = "move.preset1"
```

2. **Add protocol method** to `protocol.py`:
```python
def build_move_preset1_request(self, request_id: int = 1) -> dict:
    """Build move to preset 1 request."""
    return self._build_request(METHOD_MOVE_PRESET_1, request_id)
```

3. **Add client method** to `client.py`:
```python
async def move_to_preset1(self) -> bool:
    """Move to preset position 1."""
    _LOGGER.debug("Moving to preset 1")
    response = await self._send_command(METHOD_MOVE_PRESET_1)
    return response.get("result") == "ok"
```

4. **Add coordinator method** to `coordinator.py`:
```python
async def async_move_to_preset1(self) -> None:
    """Move to preset position 1."""
    await self.client.move_to_preset1()
```

5. **Add cover method** to `cover.py`:
```python
async def async_move_to_preset1(self) -> None:
    """Move to preset 1."""
    _LOGGER.debug("Moving to preset 1")
    await self.coordinator.async_move_to_preset1()
    await self.coordinator.async_request_refresh()
```

6. **Test standalone** in `working_tests/`:
```python
response = send_and_receive("move.preset1")
print(response)
```

### Adding a New Data Field

1. **Update model** in `models.py`:
```python
@dataclass
class PositionStatus:
    """Position status information."""
    position: float | None
    status: MovementState
    direction: Direction
    battery_level: int | None = None  # NEW FIELD
```

2. **Update parsing** in `client.py`:
```python
def _parse_position_response(self, response: dict) -> PositionStatus:
    position_data = response.get("position", {})
    return PositionStatus(
        position=position_data.get("value"),
        status=MovementState(position_data.get("status", "unknown")),
        direction=Direction(position_data.get("direction", "none")),
        battery_level=position_data.get("battery"),  # NEW
    )
```

3. **Expose in cover** via `extra_state_attributes`:
```python
@property
def extra_state_attributes(self) -> dict:
    """Return extra state attributes."""
    if self.coordinator.data:
        return {
            "battery_level": self.coordinator.data.battery_level
        }
    return {}
```

### Adding Configuration Options

1. **Add to config flow** in `config_flow.py`:
```python
DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_HOST): str,
    vol.Required(CONF_TARGET_ID): str,
    vol.Required(CONF_KEY): str,
    vol.Optional(CONF_SCAN_INTERVAL, default=30): int,  # NEW
})
```

2. **Add constant** to `const.py`:
```python
CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 30
```

3. **Use in coordinator** in `coordinator.py`:
```python
def __init__(self, hass, client, entry_data):
    scan_interval = entry_data.get(
        CONF_SCAN_INTERVAL,
        DEFAULT_SCAN_INTERVAL
    )
    super().__init__(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=scan_interval),
    )
```

## Debugging Tips

### Enable Debug Logging

Add to Home Assistant `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.somfy_poe: debug
    custom_components.somfy_poe.api: debug
    custom_components.somfy_poe.coordinator: debug
```

### Add Debug Statements

```python
import logging

_LOGGER = logging.getLogger(__name__)

# In your code:
_LOGGER.debug("Sending command: %s", method)
_LOGGER.debug("Received response: %s", response)
_LOGGER.debug("Encrypted data: %s", encrypted.hex())
```

### Test Without Home Assistant

Use standalone scripts for faster iteration:

```bash
cd working_tests/

# Edit test file
vim test_decrypt_responses.py

# Add your test code
# ...

# Run immediately
python3 test_decrypt_responses.py
```

### Inspect Network Traffic

```bash
# Capture UDP traffic on port 55055
sudo tcpdump -i any -n udp port 55055 -X

# Or with Wireshark
# Filter: udp.port == 55055
```

### Test Encryption/Decryption

```python
# Quick encryption test
from custom_components.somfy_poe.api.encryption import SomfyEncryption

enc = SomfyEncryption(key_hex="FBE90399BA25B4B67DC1B23BE0D9C084")
plaintext = b'{"method":"move.up","params":{"targetID":"160326"},"id":1}'

encrypted = enc.encrypt(plaintext)
print(f"Encrypted: {encrypted.hex()}")

decrypted = enc.decrypt(encrypted)
print(f"Decrypted: {decrypted}")
```

### Test Protocol

```python
# Quick protocol test
from custom_components.somfy_poe.api.protocol import SomfyProtocol

proto = SomfyProtocol(target_id="160326")
request = proto.build_move_up_request(request_id=1)
print(f"Request: {request}")

# Should output:
# {'method': 'move.up', 'params': {'targetID': '160326'}, 'id': 1}
```

### Check Socket State

```bash
# Check if port is in use
lsof -i :55055

# Check socket options
netstat -an | grep 55055

# Force close sockets (if needed)
kill -9 $(lsof -t -i:55055)
```

## Common Pitfalls

### 1. Target ID as Integer

**WRONG**:
```python
TARGET_ID = 160326  # Integer
message = {"params": {"targetID": 160326}}
```

**RIGHT**:
```python
TARGET_ID = "160326"  # String
message = {"params": {"targetID": "160326"}}
```

**Why**: The motor expects targetID as a string in JSON.

---

### 2. PKCS7 Padding

**WRONG**:
```python
from cryptography.hazmat.primitives import padding

padder = padding.PKCS7(128).padder()
padded = padder.update(data) + padder.finalize()
```

**RIGHT**:
```python
# Zero-padding
padding_needed = -len(data) % 16
padded = data + b"\0" * padding_needed
```

**Why**: Motor uses zero-padding, not PKCS7. PKCS7 works but less reliably.

---

### 3. Forgetting SO_REUSEADDR

**WRONG**:
```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 55055))
```

**RIGHT**:
```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.bind(("", 55055))
```

**Why**: Allows quick restart without "address already in use" errors.

---

### 4. Not Binding to Port 55055

**WRONG**:
```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(data, (host, 55055))
response = sock.recvfrom(4096)  # May timeout!
```

**RIGHT**:
```python
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("", 55055))  # MUST bind!
sock.sendto(data, (host, 55055))
response = sock.recvfrom(4096)  # Works!
```

**Why**: Motor sends responses back to port 55055. Must bind to receive them.

---

### 5. Position Inversion

**WRONG** (in cover.py):
```python
def current_cover_position(self):
    return self.coordinator.data.position  # Inverted!
```

**RIGHT**:
```python
def current_cover_position(self):
    # Somfy: 0=open/up, 100=closed/down
    # HA: 0=closed, 100=open
    return 100 - self.coordinator.data.position
```

**Why**: Somfy and Home Assistant use opposite position conventions.

---

### 6. Synchronous Code in Async Functions

**WRONG**:
```python
async def async_move_up(self):
    sock = socket.socket(...)  # Blocking!
    sock.sendto(...)
    response = sock.recvfrom(...)  # Blocks event loop!
```

**RIGHT**:
```python
async def async_move_up(self):
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None,
        self._sync_send_command,
        "move.up"
    )
```

**Why**: Don't block the Home Assistant event loop.

---

### 7. Not Closing Sockets

**WRONG**:
```python
def send_command(cmd):
    sock = socket.socket(...)
    sock.sendto(...)
    # Forgot to close!
```

**RIGHT**:
```python
def send_command(cmd):
    sock = socket.socket(...)
    try:
        sock.sendto(...)
        response = sock.recvfrom(...)
        return response
    finally:
        sock.close()  # Always close
```

**Why**: Leaks file descriptors, port conflicts.

---

## Code Style

### Follow Home Assistant Guidelines

- Use Black for formatting (max line length 100)
- Use isort for import sorting
- Follow PEP 8
- Use type hints
- Document with docstrings

### Type Hints

```python
from typing import Any

async def async_move_up(self) -> bool:
    """Move cover up."""
    response: dict[str, Any] = await self._send_command("move.up")
    return response.get("result") == "ok"
```

### Docstrings

```python
def encrypt(self, plaintext: bytes) -> bytes:
    """Encrypt data using AES-128-CBC with zero-padding.

    Args:
        plaintext: Data to encrypt

    Returns:
        Encrypted data with IV prepended

    Raises:
        SomfyEncryptionError: If encryption fails
    """
```

### Logging

```python
# Use appropriate log levels
_LOGGER.debug("Encrypting %d bytes", len(plaintext))  # Verbose
_LOGGER.info("Motor moved to position %s", position)   # Important events
_LOGGER.warning("Command timeout, retrying")           # Recoverable issues
_LOGGER.error("Failed to connect: %s", err)           # Errors
```

### Error Handling

```python
try:
    response = await self.client.move_up()
except SomfyTimeoutError:
    _LOGGER.warning("Command timeout")
    return False
except SomfyError as err:
    _LOGGER.error("Command failed: %s", err)
    raise
```

## Testing During Development

### Quick Test Loop

```bash
# 1. Edit code
vim custom_components/somfy_poe/api/encryption.py

# 2. Test standalone
cd working_tests/
python3 test_decrypt_responses.py

# 3. If works, test in HA
cp -r custom_components/somfy_poe ~/.homeassistant/custom_components/
ha core restart

# 4. Check logs
tail -f ~/.homeassistant/home-assistant.log | grep somfy_poe
```

### Test Checklist Before Commit

- [ ] Standalone test passes
- [ ] No pylint errors
- [ ] Code formatted with Black
- [ ] Type hints added
- [ ] Docstrings updated
- [ ] Home Assistant integration works
- [ ] No errors in HA logs
- [ ] Motor physically responds correctly

### Performance Considerations

- **UDP is fast**: Response time < 100ms typical
- **Don't poll too fast**: Respect motor resources
- **Use adaptive polling**: Fast when moving, slow when idle
- **Cache position**: Don't query on every attribute access
- **Async everything**: Never block the event loop

## Development Workflow

### Feature Development

1. **Design**: Plan the feature, API changes
2. **Test script**: Create standalone test first
3. **Implement**: Add to API layer
4. **Test**: Verify with standalone script
5. **Integrate**: Add to HA layer
6. **Test**: Verify in Home Assistant
7. **Document**: Update docs
8. **Commit**: Clean commit with good message

### Bug Fixing

1. **Reproduce**: Create test case that fails
2. **Diagnose**: Use debug logging, standalone tests
3. **Fix**: Make minimal changes
4. **Verify**: Test case now passes
5. **Regression**: Run all tests
6. **Document**: Update comments/docs
7. **Commit**: Reference issue number

### Refactoring

1. **Tests first**: Ensure all tests pass
2. **Small changes**: One refactor at a time
3. **Test after each**: Don't break functionality
4. **Document**: Update architecture docs
5. **Review**: Check for unintended changes

## Resources

### Documentation
- [Home Assistant Developer Docs](https://developers.home-assistant.io/)
- [Somfy PoE Motor API](../Somfy%20PoE%20Motor%20API%20for%20Integration.pdf)
- [AES Encryption](https://en.wikipedia.org/wiki/Advanced_Encryption_Standard)
- [JSON-RPC 2.0](https://www.jsonrpc.org/specification)

### Code Examples
- [working_tests/](../working_tests/) - Standalone test scripts
- [custom_components/somfy_poe/](../custom_components/somfy_poe/) - Integration code

### Tools
- [Black](https://black.readthedocs.io/) - Code formatter
- [Pylint](https://pylint.org/) - Code linter
- [MyPy](https://mypy.readthedocs.io/) - Type checker
- [Pytest](https://pytest.org/) - Testing framework

## Getting Help

1. **Check docs**: README.md, TESTING.md, this file
2. **Run tests**: working_tests/ scripts to isolate issues
3. **Check logs**: Enable debug logging
4. **Test standalone**: Remove HA from equation
5. **Check network**: tcpdump, wireshark
6. **Review working code**: Look at test scripts that work

---

**Happy coding!** Remember to test incrementally and use the standalone scripts for fast iteration.
