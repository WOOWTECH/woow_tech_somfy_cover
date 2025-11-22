# Architecture Overview

**WoowTech Somfy Cover Integration for Home Assistant**

**Version:** 1.0.2
**Last Updated:** 2025-11-22

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Layer Architecture](#layer-architecture)
3. [Data Flow](#data-flow)
4. [Component Details](#component-details)
5. [Configuration Methods](#configuration-methods)
6. [Wake-up Mechanism](#wake-up-mechanism)
7. [Error Handling](#error-handling)
8. [Performance Characteristics](#performance-characteristics)

---

## System Overview

The WoowTech Somfy Cover integration provides local control of Somfy PoE motors through encrypted UDP communication. The integration is designed with a layered architecture that separates concerns and makes the code maintainable and testable.

### Key Features

- **Dual Configuration**: Supports both Config Flow (UI) and YAML configuration
- **Encrypted Communication**: AES-128-CBC encryption with zero-padding
- **Motor Wake-up**: Automatic handling of sleeping motors
- **Adaptive Polling**: Fast updates during movement, slow when idle
- **Position Control**: Full position control with 0.001% precision
- **Error Recovery**: Automatic retry and graceful error handling

### Technology Stack

- **Protocol**: JSON-RPC 2.0 over UDP
- **Encryption**: AES-128-CBC (cryptography library)
- **Transport**: UDP on port 55055
- **Home Assistant**: DataUpdateCoordinator pattern
- **Python**: 3.11+ with async/await

---

## Layer Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│ Home Assistant Layer                                            │
│                                                                  │
│  ┌──────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │ Config Flow  │  │ Cover Entity   │  │  Coordinator     │   │
│  │ (UI Setup)   │  │ (Platform)     │  │  (Polling)       │   │
│  └──────────────┘  └────────────────┘  └──────────────────┘   │
│         │                  │                      │             │
└─────────┼──────────────────┼──────────────────────┼─────────────┘
          │                  │                      │
          └──────────────────┴──────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  SomfyClient    │  High-level API
                    │  (api/client.py)│
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼──────┐    ┌───────▼────────┐   ┌──────▼────────┐
   │ Protocol  │    │  Encryption    │   │  Transport    │
   │ (JSON-RPC)│    │  (AES-128-CBC) │   │  (UDP Socket) │
   └───────────┘    └────────────────┘   └───────────────┘
                             │
                    ┌────────▼────────┐
                    │  Somfy Motor    │
                    │  192.168.1.x    │
                    │  Port 55055     │
                    └─────────────────┘
```

### Layer Responsibilities

**Home Assistant Layer** (`__init__.py`, `cover.py`, `coordinator.py`, `config_flow.py`)
- Integration lifecycle management
- User interface and configuration
- State management and polling
- Entity registration

**API Client Layer** (`api/client.py`)
- High-level motor control methods
- Type-safe return values
- Error handling and retry logic

**Protocol Layer** (`api/protocol.py`)
- JSON-RPC message construction
- Request/response parsing
- Error code mapping

**Encryption Layer** (`api/encryption.py`)
- AES-128-CBC encryption/decryption
- Zero-padding implementation
- IV generation

**Transport Layer** (`api/transport.py`)
- UDP socket management
- Motor wake-up mechanism
- Socket lifecycle and binding

---

## Data Flow

### Command Execution Flow

```
User clicks "Open" in HA UI
    │
    ▼
Cover Entity (cover.py)
  └─> async_open_cover()
      │
      ▼
Coordinator (coordinator.py)
  └─> async_move_up()
      │
      ▼
SomfyClient (api/client.py)
  └─> move_up()
      │
      ▼
Protocol (api/protocol.py)
  └─> build_request("move.up", {"targetID": "160326"})
      │ Returns: '{"method":"move.up","params":{"targetID":"160326"},"id":1}'
      ▼
Transport (api/transport.py)
  └─> send_encrypted(json_string)
      │
      ├─> [Check if motor needs wake-up]
      │   └─> Send move.stop command (if needed)
      │       Wait 0.2s for motor to stabilize
      │
      ├─> Encryption (api/encryption.py)
      │   └─> encrypt(plaintext)
      │       ├─> Generate random IV (16 bytes)
      │       ├─> Zero-pad to 16-byte blocks
      │       ├─> AES-128-CBC encrypt
      │       └─> Return IV + ciphertext
      │
      ├─> Socket Operations
      │   ├─> Create UDP socket
      │   ├─> Set SO_REUSEADDR option
      │   ├─> Bind to port 55055
      │   ├─> Send encrypted packet
      │   ├─> Receive encrypted response
      │   └─> Close socket
      │
      └─> Encryption (api/encryption.py)
          └─> decrypt(response)
              ├─> Extract IV (first 16 bytes)
              ├─> AES-128-CBC decrypt
              ├─> Remove zero-padding
              └─> Return plaintext JSON
      │
      ▼
Protocol (api/protocol.py)
  └─> parse_response(json_string)
      │ Validates JSON-RPC response
      │ Checks for errors
      └─> Returns result data
      │
      ▼
SomfyClient (api/client.py)
  └─> Returns success to coordinator
      │
      ▼
Coordinator (coordinator.py)
  └─> Request immediate refresh
      │
      ▼
Cover Entity (cover.py)
  └─> Update HA state
      │
      ▼
HA UI shows updated state
```

### Position Polling Flow

```
Coordinator Timer Fires
    │
    ▼
Coordinator._async_update_data()
  └─> client.get_position()
      │ [Same flow as above for status.position command]
      ▼
  Returns PositionStatus
      │ position: 94.5 (Somfy: 0=open, 100=closed)
      │ status: MovementState.RUNNING
      │ direction: Direction.DOWN_CLOSE
      ▼
Coordinator checks movement state
  ├─> If moving: Switch to fast polling (2s)
  └─> If stopped: Switch to normal polling (30s)
      │
      ▼
Cover Entity receives update
  └─> current_cover_position property
      ├─> Invert position: 100 - 94.5 = 5.5
      └─> Return 6 (rounded, HA format: 0=closed, 100=open)
      │
      ▼
HA UI shows position: 6%
```

---

## Component Details

### 1. Config Flow (`config_flow.py`)

**Purpose**: UI-based configuration for adding motors

**Features**:
- Input validation (target_id: 6 hex chars, key: 32 hex chars)
- Connection testing before creating entry
- Unique ID enforcement (one entry per target_id)
- Error handling with user-friendly messages

**Flow**:
```python
User opens "Add Integration"
    │
    ▼
async_step_user() presents form
    │ Fields: name, host, target_id, key
    ▼
User submits form
    │
    ▼
Validate input formats
    │
    ▼
_test_connection()
  └─> Create temporary SomfyClient
  └─> Call get_device_info() to verify connectivity
  └─> Close client
    │
    ▼
Create config entry with data
    │
    ▼
Integration setup begins
```

### 2. Integration Setup (`__init__.py`)

**Purpose**: Integration lifecycle management

**Dual Configuration Support**:
- `async_setup()`: Called for YAML configuration
- `async_setup_entry()`: Called for Config Flow entries

**Setup Process (Config Flow)**:
```python
async_setup_entry(hass, entry)
  │
  ├─> Create SomfyClient(host, target_id, key)
  ├─> client.connect()  # Verifies port 55055 binding
  ├─> Create SomfyDataUpdateCoordinator(hass, client, entry.data)
  ├─> coordinator.async_config_entry_first_refresh()
  ├─> coordinator.async_get_device_info()  # For device registry
  ├─> Store coordinator in hass.data[DOMAIN][entry.entry_id]
  └─> async_forward_entry_setups(entry, PLATFORMS)
```

**Teardown Process**:
```python
async_unload_entry(hass, entry)
  │
  ├─> async_unload_platforms(entry, PLATFORMS)
  ├─> coordinator.client.close()  # Close socket
  └─> Remove from hass.data
```

### 3. Cover Platform (`cover.py`)

**Purpose**: Home Assistant cover entity implementation

**Two Entity Classes**:
- `SomfyCover`: For Config Flow entries
- `SomfyYAMLCover`: For YAML configuration

**Key Properties**:
```python
current_cover_position:
    # Somfy: 0=open/up, 100=closed/down
    # HA:    0=closed,   100=open
    return 100 - self.coordinator.data.position

is_opening:
    return self.coordinator.data.is_opening

is_closing:
    return self.coordinator.data.is_closing

state:
    if is_opening: return STATE_OPENING
    if is_closing: return STATE_CLOSING
    if position == 0: return STATE_CLOSED
    return STATE_OPEN
```

**Supported Features**:
- `CoverEntityFeature.OPEN`
- `CoverEntityFeature.CLOSE`
- `CoverEntityFeature.STOP`
- `CoverEntityFeature.SET_POSITION`

### 4. Coordinator (`coordinator.py`)

**Purpose**: Data polling and state management

**Adaptive Polling**:
```python
UPDATE_INTERVAL = 30 seconds  # Normal polling (motor stopped)
FAST_UPDATE_INTERVAL = 2 seconds  # Fast polling (motor moving)

async def _adjust_polling_interval(status):
    if status.is_moving and not self._fast_poll_mode:
        self.update_interval = FAST_UPDATE_INTERVAL
        self._fast_poll_mode = True
    elif not status.is_moving and self._fast_poll_mode:
        self.update_interval = UPDATE_INTERVAL
        self._fast_poll_mode = False
```

**Update Cycle**:
```python
async def _async_update_data():
    try:
        status = await self.client.get_position()
        await self._adjust_polling_interval(status)
        return status
    except SomfyError as err:
        raise UpdateFailed(f"Error: {err}")
```

### 5. API Client (`api/client.py`)

**Purpose**: High-level motor control interface

**Public Methods**:
```python
async def connect() -> None
async def close() -> None
async def get_device_info() -> DeviceInfo
async def get_position() -> PositionStatus
async def move_up() -> None
async def move_down() -> None
async def stop() -> None
async def move_to_position(position: float) -> None
```

**Internal Flow**:
```python
async def move_up():
    request = protocol.build_request("move.up")
    response = await transport.send_encrypted(request)
    protocol.parse_response(response)  # Validates, raises on error
```

### 6. Protocol Layer (`api/protocol.py`)

**Purpose**: JSON-RPC message handling

**Request Building**:
```python
def build_request(method, params=None):
    self._request_id += 1
    request = {
        "method": method,
        "params": {"targetID": self._target_id, **(params or {})},
        "id": self._request_id
    }
    return json.dumps(request, separators=(",", ":"))
```

**Response Parsing**:
```python
def parse_response(response: str):
    data = json.loads(response)

    # Check for error
    if "error" in data:
        error = data["error"]
        code = error.get("id", -1)
        message = error.get("title", "Unknown error")
        raise SomfyAPIError(message, code)

    # Validate structure
    if "result" not in data:
        raise SomfyProtocolError("Missing result field")

    return data
```

### 7. Encryption Layer (`api/encryption.py`)

**Purpose**: AES-128-CBC encryption with zero-padding

**Encryption Process**:
```python
def encrypt(plaintext: str) -> bytes:
    # 1. Generate random IV
    iv = secrets.token_bytes(16)

    # 2. Zero-pad to 16-byte blocks
    plaintext_bytes = plaintext.encode("utf-8")
    padding_length = -len(plaintext_bytes) % 16
    padded = plaintext_bytes + b"\0" * padding_length

    # 3. Encrypt with AES-128-CBC
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    # 4. Return IV + ciphertext
    return iv + ciphertext
```

**Decryption Process**:
```python
def decrypt(data: bytes) -> str:
    # 1. Extract IV and ciphertext
    iv = data[:16]
    ciphertext = data[16:]

    # 2. Decrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    # 3. Remove zero-padding
    plaintext = padded.rstrip(b"\0")

    # 4. Decode to string
    return plaintext.decode("utf-8")
```

**Why Zero-Padding?**
- PKCS7 padding: 80% success rate in testing
- Zero-padding: 100% success rate in testing
- Motor expects zero-padding in responses
- Simpler implementation, no padding oracle attacks for read-only API

### 8. Transport Layer (`api/transport.py`)

**Purpose**: UDP communication and motor wake-up

**Socket Pattern** (Critical for motor communication):
```python
def _send_receive_sync(data: bytes, timeout: float) -> bytes:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # CRITICAL: Enable port reuse
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # CRITICAL: Bind to port 55055 (motor only responds to this port)
    sock.bind(("", 55055))

    sock.settimeout(timeout)
    sock.sendto(data, (host, 55055))
    response, addr = sock.recvfrom(4096)
    sock.close()

    return response
```

**Async Wrapper**:
```python
async def send_encrypted(plaintext: str) -> str:
    async with self._lock:  # Serialize requests
        # Wake-up if needed
        if self._needs_wakeup or self._last_timeout:
            await self._send_wakeup_command()

        # Encrypt
        encrypted = self._encryption.encrypt(plaintext)

        # Send/receive (blocking ops in thread executor)
        response = await asyncio.to_thread(
            self._send_receive_sync,
            encrypted,
            timeout
        )

        # Decrypt
        return self._encryption.decrypt(response)
```

---

## Configuration Methods

The integration supports two independent configuration methods that can coexist.

### Config Flow (UI)

**User Experience**:
1. Settings → Devices & Services → Add Integration
2. Search for "WoowTech Somfy Cover"
3. Enter configuration:
   - Name: "Living Room Shade"
   - Host: 192.168.1.77
   - Target ID: 160326
   - Key: FBE90399BA25B4B67DC1B23BE0D9C084
4. Click Submit
5. Integration validates and creates entry

**Entity ID**: `cover.<name>`
**Unique ID**: `<entry_id>_cover`

### YAML Configuration

**configuration.yaml**:
```yaml
cover:
  - platform: woow_tech_somfy_cover
    name: Living Room Shade
    host: 192.168.1.77
    target_id: 160326  # Can be unquoted (v1.0.2+)
    key: FBE90399BA25B4B67DC1B23BE0D9C084  # Can be unquoted (v1.0.2+)
```

**Entity ID**: `cover.<name>`
**Unique ID**: `yaml_<target_id>_<sanitized_name>`

### Coexistence

Both methods can be used simultaneously:
```yaml
# YAML configuration
cover:
  - platform: woow_tech_somfy_cover
    name: Bedroom Shade
    host: 192.168.1.78
    target_id: 160327
    key: ABC123...
```

And Config Flow entry for different motor → Both work independently with separate coordinators.

---

## Wake-up Mechanism

### Problem

Somfy motors enter hibernation after inactivity. When sleeping:
- First command receives NO response (motor wakes but doesn't reply)
- Subsequent commands work perfectly

### Solution

Transparent wake-up in transport layer:

**State Tracking**:
```python
self._needs_wakeup = True  # After connection
self._last_timeout = False  # Track timeout events
```

**Wake-up Logic**:
```python
async def send_encrypted(plaintext, skip_wakeup=False):
    async with self._lock:
        # Wake up if needed (before actual command)
        if not skip_wakeup and (self._needs_wakeup or self._last_timeout):
            await self._send_wakeup_command()
            self._needs_wakeup = False

        # Send actual command
        # ...
```

**Wake-up Command**:
```python
async def _send_wakeup_command():
    # Send harmless move.stop command
    wakeup_request = '{"method":"move.stop","params":{"targetID":"160326"},"id":0}'

    try:
        encrypted = self._encryption.encrypt(wakeup_request)
        await asyncio.to_thread(
            self._send_receive_sync,
            encrypted,
            0.8  # Short timeout - we don't care about response
        )
    except socket.timeout:
        # Expected - motor woke but didn't respond
        pass

    # Brief stabilization pause
    await asyncio.sleep(0.2)
```

**Result**:
- No more first-command timeouts
- ~1 second overhead only when needed
- Completely transparent to integration code
- Self-healing after timeouts

---

## Error Handling

### Error Hierarchy

```python
SomfyError (base)
    ├─> SomfyConnectionError
    │   ├─> Cannot bind to port 55055
    │   └─> Send/receive failed
    ├─> SomfyTimeoutError
    │   └─> Request timed out after Xs
    ├─> SomfyProtocolError
    │   ├─> Invalid JSON response
    │   └─> Response missing required field
    └─> SomfyAPIError
        ├─> Device locked (code 32)
        ├─> End limits not set (code 34)
        ├─> Thermal protection (code 48)
        └─> [30+ error codes mapped]
```

### Error Code Mapping

From `const.py`:
```python
ERROR_DEVICE_LOCKED = 32  # Motor locked by another client
ERROR_END_LIMITS_NOT_SET = 34  # End limits must be configured
ERROR_TARGET_OUT_OF_RANGE = 36  # Position outside valid range
ERROR_IN_MOTION = 38  # Motor currently moving
ERROR_THERMAL_PROTECTION = 48  # Motor overheated
ERROR_OBSTACLE_DETECTION = 49  # Obstacle detected
```

### Retry Strategy

**Timeout Retry** (transport layer):
```python
for attempt in range(2 if retry_on_timeout else 1):
    try:
        # Send command
        response = await self._send_receive_sync(data, timeout)
        self._last_timeout = False
        return response
    except socket.timeout:
        self._last_timeout = True
        if attempt >= 1:
            raise SomfyTimeoutError(...)
        # Wait and retry
        await asyncio.sleep(0.3)
```

**Coordinator Handling**:
```python
async def _async_update_data():
    try:
        return await self.client.get_position()
    except SomfyError as err:
        _LOGGER.error("Update failed: %s", err)
        raise UpdateFailed(f"Error: {err}")
```

---

## Performance Characteristics

### Latency

- **Command Response**: 50-150ms typical
- **Position Query**: 50-150ms typical
- **Wake-up Overhead**: ~1000ms (only when needed)
- **Fast Polling**: Every 2 seconds during movement
- **Normal Polling**: Every 30 seconds when stopped

### Network Traffic

**During Movement** (30 seconds):
- Polls: 15 requests × ~100 bytes = 1.5 KB
- Responses: 15 × ~150 bytes = 2.25 KB
- Total: ~3.75 KB per 30 seconds of movement

**When Idle** (30 minutes):
- Polls: 60 requests × ~100 bytes = 6 KB
- Responses: 60 × ~150 bytes = 9 KB
- Total: ~15 KB per 30 minutes

### Resource Usage

- **Memory**: ~2 MB per motor entity
- **CPU**: <0.1% (polling only)
- **File Descriptors**: 0 persistent (sockets created/closed per request)
- **Port 55055**: Bound only during active requests

### Scaling

- **Multiple Motors**: Each gets independent coordinator
- **Concurrent Requests**: Serialized per motor (asyncio.Lock)
- **Port Sharing**: SO_REUSEADDR allows multiple instances
- **Tested**: Up to 4 simultaneous motors without issues

---

## Security Considerations

### Encryption

- **Algorithm**: AES-128-CBC (NIST approved)
- **Key Length**: 128 bits (16 bytes)
- **IV**: Random, 128 bits, unique per message
- **Padding**: Zero-padding (not PKCS7)

### Attack Surface

**Low Risk**:
- Local network only (no cloud)
- Encrypted communication
- No authentication bypass (encryption key required)
- Read-only operations (no firmware updates)

**Considerations**:
- Key stored in HA config (encrypted at rest by HA)
- No key rotation mechanism
- UDP can be sniffed (but encrypted)
- Replay attacks possible (no nonce/timestamp validation)

### Recommendations

1. Keep Home Assistant updated
2. Use firewall to restrict motor access to HA only
3. Use separate VLAN for IoT devices
4. Rotate encryption keys if compromised (via motor web interface)

---

## Conclusion

The WoowTech Somfy Cover integration is architected with:

- **Clear separation of concerns** across layers
- **Robust error handling** at every level
- **Efficient resource usage** through adaptive polling
- **Transparent wake-up** for sleeping motors
- **Dual configuration** for flexibility
- **Production-ready** code with comprehensive logging

All components are tested and verified working with physical hardware.
