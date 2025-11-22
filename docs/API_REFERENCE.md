# API Reference

**WoowTech Somfy Cover Integration**

Complete reference for the API layer that communicates with Somfy PoE motors.

---

## Table of Contents

1. [Client API](#client-api)
2. [Protocol Layer](#protocol-layer)
3. [Encryption Layer](#encryption-layer)
4. [Transport Layer](#transport-layer)
5. [Data Models](#data-models)
6. [Error Codes](#error-codes)
7. [Examples](#examples)

---

## Client API

### SomfyClient

High-level interface for motor control.

**Location**: `custom_components/woow_tech_somfy_cover/api/client.py`

#### Constructor

```python
def __init__(
    self,
    host: str,
    target_id: str,
    key: str,
    port: int = 55055,
    timeout: float = 5.0,
) -> None
```

**Parameters**:
- `host` (str): Motor IP address (e.g., "192.168.1.77")
- `target_id` (str): 6-character hex target ID (e.g., "160326")
- `key` (str): 32-character hex encryption key
- `port` (int, optional): UDP port, default 55055
- `timeout` (float, optional): Request timeout in seconds, default 5.0

**Raises**:
- `ValueError`: If target_id or key format is invalid

**Example**:
```python
client = SomfyClient(
    host="192.168.1.77",
    target_id="160326",
    key="FBE90399BA25B4B67DC1B23BE0D9C084"
)
```

#### Methods

##### async connect() -> None

Connect to the motor and verify communication is possible.

**Returns**: None

**Raises**:
- `SomfyConnectionError`: If cannot bind to port 55055
- `SomfyError`: If connection verification fails

**Example**:
```python
await client.connect()
# Motor is ready for commands
```

**Implementation Note**: This method verifies socket binding capability and sends a wake-up command to ensure the motor is responsive.

---

##### async close() -> None

Close the client connection and release resources.

**Returns**: None

**Example**:
```python
await client.close()
# Socket released, client unusable
```

---

##### async get_device_info() -> DeviceInfo

Retrieve device information from the motor.

**Returns**: `DeviceInfo` object containing:
- `name` (str): Device name
- `model` (str): Model name
- `hostname` (str): Network hostname
- `synergy_version` (str): Protocol version
- `target_id` (str): Target ID
- `firmware` (str): Firmware version
- `hardware` (str): Hardware version
- `mac_address` (str): MAC address

**Raises**:
- `SomfyError`: If request fails
- `SomfyTimeoutError`: If motor doesn't respond

**Example**:
```python
info = await client.get_device_info()
print(f"Motor: {info.model}")
print(f"Firmware: {info.firmware}")
print(f"MAC: {info.mac_address}")
```

**API Call**: `status.info`

---

##### async get_position() -> PositionStatus

Get current position and movement status.

**Returns**: `PositionStatus` object containing:
- `position` (float | None): Current position 0-100 (0=open/up, 100=closed/down)
- `status` (MovementState): STOPPED, RUNNING, BLOCKED, UNKNOWN
- `direction` (Direction): UP_OPEN, DOWN_CLOSE, UNKNOWN
- `source` (str | None): Source of last command
- `cause` (str | None): Cause of current state

**Raises**:
- `SomfyError`: If request fails
- `SomfyTimeoutError`: If motor doesn't respond

**Example**:
```python
status = await client.get_position()
print(f"Position: {status.position}%")
print(f"Status: {status.status}")
print(f"Direction: {status.direction}")

if status.is_opening:
    print("Motor is opening")
elif status.is_closing:
    print("Motor is closing")
else:
    print("Motor is stopped")
```

**API Call**: `status.position`

---

##### async move_up() -> None

Start moving the motor up (opening direction).

**Returns**: None

**Raises**:
- `SomfyError`: If command fails
- `SomfyAPIError`: If motor rejects command (e.g., locked, in thermal protection)
- `SomfyTimeoutError`: If motor doesn't respond

**Example**:
```python
await client.move_up()
# Motor starts moving up
```

**API Call**: `move.up`

**Notes**:
- Command returns immediately (motor moves in background)
- Use `get_position()` to track movement progress
- Motor will stop at upper limit automatically

---

##### async move_down() -> None

Start moving the motor down (closing direction).

**Returns**: None

**Raises**:
- `SomfyError`: If command fails
- `SomfyAPIError`: If motor rejects command
- `SomfyTimeoutError`: If motor doesn't respond

**Example**:
```python
await client.move_down()
# Motor starts moving down
```

**API Call**: `move.down`

---

##### async stop() -> None

Stop motor movement immediately.

**Returns**: None

**Raises**:
- `SomfyError`: If command fails
- `SomfyTimeoutError`: If motor doesn't respond

**Example**:
```python
await client.stop()
# Motor stops (if moving)
```

**API Call**: `move.stop`

**Notes**:
- Safe to call even if motor is already stopped
- Used internally for wake-up mechanism

---

##### async move_to_position(position: float) -> None

Move to a specific position.

**Parameters**:
- `position` (float): Target position 0-100 (0=open/up, 100=closed/down)
  - Precision: Up to 3 decimal places (e.g., 50.125)
  - Range: 0.0 to 100.0

**Returns**: None

**Raises**:
- `ValueError`: If position is out of range
- `SomfyError`: If command fails
- `SomfyAPIError`: If motor rejects command (e.g., position out of configured limits)
- `SomfyTimeoutError`: If motor doesn't respond

**Example**:
```python
# Move to 50% (half-open)
await client.move_to_position(50.0)

# Move to 75.5% (precise positioning)
await client.move_to_position(75.5)

# Fully open
await client.move_to_position(0.0)

# Fully closed
await client.move_to_position(100.0)
```

**API Call**: `move.to` with `{"position": 50.0}`

**Notes**:
- Motor will stop automatically at target position
- Position is rounded to 3 decimal places
- Motor must have end limits configured

---

#### Properties

##### is_connected -> bool

Check if client is connected and ready for commands.

**Returns**: `True` if connected, `False` otherwise

**Example**:
```python
if client.is_connected:
    await client.move_up()
else:
    await client.connect()
```

---

##### host -> str

Get motor IP address.

**Returns**: IP address string

**Example**:
```python
print(f"Connected to {client.host}")
```

---

##### target_id -> str

Get motor target ID.

**Returns**: 6-character hex string

**Example**:
```python
print(f"Target ID: {client.target_id}")
```

---

#### Context Manager Support

```python
async with SomfyClient(host, target_id, key) as client:
    info = await client.get_device_info()
    await client.move_up()
# Automatically closes connection
```

---

## Protocol Layer

### SomfyProtocol

JSON-RPC message builder and parser.

**Location**: `custom_components/woow_tech_somfy_cover/api/protocol.py`

#### Constructor

```python
def __init__(self, target_id: str) -> None
```

**Parameters**:
- `target_id` (str): 6-character hex target ID

**Raises**:
- `ValueError`: If target_id format is invalid

---

#### Methods

##### build_request(method: str, params: dict | None = None) -> str

Build JSON-RPC request.

**Parameters**:
- `method` (str): RPC method name (e.g., "move.up", "status.position")
- `params` (dict, optional): Additional parameters (targetID added automatically)

**Returns**: Compact JSON string

**Example**:
```python
protocol = SomfyProtocol("160326")

# Simple command
request = protocol.build_request("move.up")
# Returns: '{"method":"move.up","params":{"targetID":"160326"},"id":1}'

# Command with parameters
request = protocol.build_request("move.to", {"position": 50.0})
# Returns: '{"method":"move.to","params":{"targetID":"160326","position":50.0},"id":2}'
```

**Notes**:
- Uses compact JSON (no spaces): `separators=(",", ":")`
- Auto-increments request ID
- targetID is ALWAYS a string (critical!)

---

##### parse_response(response: str) -> dict

Parse JSON-RPC response.

**Parameters**:
- `response` (str): JSON response from motor

**Returns**: Parsed response dictionary

**Raises**:
- `SomfyProtocolError`: If JSON is invalid or structure is wrong
- `SomfyAPIError`: If response contains error

**Example**:
```python
response = '{"result":true,"targetID":"160326","id":1}'
data = protocol.parse_response(response)
# Returns: {"result": True, "targetID": "160326", "id": 1}

# Error response
response = '{"error":{"id":32,"title":"Device locked"},"id":1}'
protocol.parse_response(response)
# Raises: SomfyAPIError("Device locked", code=32)
```

---

## Encryption Layer

### SomfyEncryption

AES-128-CBC encryption with zero-padding.

**Location**: `custom_components/woow_tech_somfy_cover/api/encryption.py`

#### Constructor

```python
def __init__(self, key: str) -> None
```

**Parameters**:
- `key` (str): 32-character hex string (16 bytes)

**Raises**:
- `ValueError`: If key format is invalid

**Example**:
```python
enc = SomfyEncryption("FBE90399BA25B4B67DC1B23BE0D9C084")
```

---

#### Methods

##### encrypt(plaintext: str, use_zero_padding: bool = True) -> bytes

Encrypt plaintext with random IV.

**Parameters**:
- `plaintext` (str): UTF-8 string to encrypt
- `use_zero_padding` (bool, optional): Use zero-padding (default) or PKCS7

**Returns**: IV (16 bytes) + encrypted ciphertext

**Example**:
```python
plaintext = '{"method":"move.up","params":{"targetID":"160326"},"id":1}'
encrypted = enc.encrypt(plaintext)
# Returns: b'\x12\x34...(16 bytes IV)...\xab\xcd...(encrypted data)...'
```

**Process**:
1. Generate random 16-byte IV
2. Encode plaintext to UTF-8
3. Pad to 16-byte multiple (zero-padding)
4. Encrypt with AES-128-CBC
5. Return IV + ciphertext

**Note**: Zero-padding has 100% success rate with Somfy motors (tested).

---

##### decrypt(data: bytes, use_zero_padding: bool = True) -> str

Decrypt data with prepended IV.

**Parameters**:
- `data` (bytes): IV (16 bytes) + ciphertext
- `use_zero_padding` (bool, optional): Expect zero-padding (default) or PKCS7

**Returns**: Decrypted UTF-8 string

**Raises**:
- `ValueError`: If data is too short or padding is invalid

**Example**:
```python
encrypted = b'\x12\x34...(IV + ciphertext)...'
plaintext = enc.decrypt(encrypted)
# Returns: '{"result":true,"targetID":"160326","id":1}'
```

**Process**:
1. Extract IV (first 16 bytes)
2. Extract ciphertext (remaining bytes)
3. Decrypt with AES-128-CBC
4. Remove zero-padding
5. Decode to UTF-8 string

---

## Transport Layer

### SomfyTransport

UDP communication with motor wake-up.

**Location**: `custom_components/woow_tech_somfy_cover/api/transport.py`

#### Constructor

```python
def __init__(
    self,
    host: str,
    encryption: SomfyEncryption | None,
    port: int = 55055,
    default_timeout: float = 5.0,
    target_id: str | None = None,
) -> None
```

**Parameters**:
- `host` (str): Motor IP address
- `encryption` (SomfyEncryption | None): Encryption instance (None for unencrypted)
- `port` (int, optional): UDP port, default 55055
- `default_timeout` (float, optional): Default timeout in seconds
- `target_id` (str, optional): Target ID for wake-up commands

---

#### Methods

##### async send_encrypted(plaintext: str, timeout: float | None = None, retry_on_timeout: bool = True, skip_wakeup: bool = False) -> str

Send encrypted message and receive encrypted response.

**Parameters**:
- `plaintext` (str): Unencrypted JSON-RPC message
- `timeout` (float, optional): Request timeout (uses default if None)
- `retry_on_timeout` (bool, optional): Retry once on timeout, default True
- `skip_wakeup` (bool, optional): Skip wake-up logic (internal use), default False

**Returns**: Decrypted response string

**Raises**:
- `SomfyConnectionError`: If transport is closed or encryption not configured
- `SomfyTimeoutError`: If request times out after retry
- `OSError`: If socket operation fails

**Example**:
```python
transport = SomfyTransport(host, encryption, target_id=target_id)
await transport.connect()

request = '{"method":"move.up","params":{"targetID":"160326"},"id":1}'
response = await transport.send_encrypted(request)
# Returns: '{"result":true,"targetID":"160326","id":1}'
```

**Process**:
1. Check if wake-up needed (first command or after timeout)
2. Send wake-up command if needed (transparent)
3. Encrypt plaintext
4. Create UDP socket
5. Set SO_REUSEADDR option
6. Bind to port 55055
7. Send encrypted packet
8. Receive encrypted response
9. Close socket
10. Decrypt response
11. Return plaintext

**Wake-up Logic**:
- Triggered on first command after connection
- Triggered on first command after timeout
- Sends harmless `move.stop` command
- Ignores timeout (motor wakes but may not respond)
- 0.2s stabilization delay after wake-up

---

##### async connect() -> None

Verify connection capability (test socket binding).

**Returns**: None

**Raises**:
- `SomfyConnectionError`: If cannot bind to port 55055

---

##### async close() -> None

Close transport (marks as closed to prevent new requests).

**Returns**: None

---

#### Properties

##### is_connected -> bool

Check if transport is ready for requests.

**Returns**: `True` if not closed, `False` otherwise

---

## Data Models

### DeviceInfo

**Location**: `custom_components/woow_tech_somfy_cover/api/models.py`

Immutable dataclass for device information.

**Attributes**:
```python
@dataclass(frozen=True)
class DeviceInfo:
    name: str              # Device name (e.g., "Sonesse 30 PoE")
    model: str             # Model name
    hostname: str          # Network hostname (e.g., "sfy_poe_00049C")
    synergy_version: str   # Protocol version (e.g., "6")
    target_id: str         # Target ID (e.g., "160326")
    firmware: str          # Firmware version
    hardware: str          # Hardware version
    mac_address: str       # MAC address (e.g., "4C:C2:06:16:03:26")
```

**Class Method**:
```python
@classmethod
def from_api_response(cls, data: dict) -> DeviceInfo
```

**Example**:
```python
info = DeviceInfo(
    name="Sonesse 30 PoE",
    model="Sonesse 30 PoE",
    hostname="sfy_poe_00049C",
    synergy_version="6",
    target_id="160326",
    firmware="5163364A07/5155239A32",
    hardware="5155389A01/5153582A00",
    mac_address="4C:C2:06:16:03:26"
)
```

---

### PositionStatus

**Location**: `custom_components/woow_tech_somfy_cover/api/models.py`

Immutable dataclass for position and movement status.

**Attributes**:
```python
@dataclass(frozen=True)
class PositionStatus:
    position: float | None    # 0-100 (0=open/up, 100=closed/down), None if unknown
    status: MovementState     # STOPPED, RUNNING, BLOCKED, UNKNOWN
    direction: Direction      # UP_OPEN, DOWN_CLOSE, UNKNOWN
    source: str | None        # Source of last command (e.g., "network message")
    cause: str | None         # Cause of current state (e.g., "explicit command")
```

**Properties**:
```python
@property
def is_moving(self) -> bool:
    """Check if motor is currently moving."""
    return self.status == MovementState.RUNNING

@property
def is_stopped(self) -> bool:
    """Check if motor is stopped."""
    return self.status == MovementState.STOPPED

@property
def is_opening(self) -> bool:
    """Check if motor is opening (moving up)."""
    return self.is_moving and self.direction == Direction.UP_OPEN

@property
def is_closing(self) -> bool:
    """Check if motor is closing (moving down)."""
    return self.is_moving and self.direction == Direction.DOWN_CLOSE
```

**Class Method**:
```python
@classmethod
def from_api_response(cls, data: dict) -> PositionStatus
```

**Example**:
```python
status = PositionStatus(
    position=94.154,
    status=MovementState.RUNNING,
    direction=Direction.DOWN_CLOSE,
    source="network message",
    cause="explicit command"
)

if status.is_closing:
    print(f"Motor closing, position: {status.position}%")
```

---

### MovementState

**Location**: `custom_components/woow_tech_somfy_cover/api/models.py`

Enum for motor movement states.

**Values**:
```python
class MovementState(str, Enum):
    STOPPED = "stopped"  # Motor not moving
    RUNNING = "running"  # Motor moving
    BLOCKED = "blocked"  # Motor blocked (obstacle, error)
    UNKNOWN = "unknown"  # State unknown
```

**Class Method**:
```python
@classmethod
def from_api(cls, status: str | None, direction: str | None = None) -> MovementState
```

---

### Direction

**Location**: `custom_components/woow_tech_somfy_cover/api/models.py`

Enum for movement direction.

**Values**:
```python
class Direction(str, Enum):
    UP_OPEN = "up"       # Moving up/opening
    DOWN_CLOSE = "down"  # Moving down/closing
    UNKNOWN = "unknown"  # Direction unknown
```

**Class Method**:
```python
@classmethod
def from_api(cls, direction: str | None) -> Direction
```

---

## Error Codes

**Location**: `custom_components/woow_tech_somfy_cover/const.py`

### Common Error Codes

| Code | Constant | Description |
|------|----------|-------------|
| 1 | ERROR_DATA_OUT_OF_RANGE | Parameter value out of acceptable range |
| 16 | ERROR_UNKNOWN_MESSAGE | Unrecognized JSON-RPC method |
| 17 | ERROR_MESSAGE_LENGTH | Message exceeds maximum length |
| 32 | ERROR_DEVICE_LOCKED | Motor is locked by another client |
| 33 | ERROR_WRONG_POSITION | Position command invalid for current state |
| 34 | ERROR_END_LIMITS_NOT_SET | End limits must be configured first |
| 35 | ERROR_NO_PRESET_POSITION | Requested preset not configured |
| 36 | ERROR_TARGET_OUT_OF_RANGE | Target position outside valid range |
| 37 | ERROR_FEATURE_NOT_SUPPORTED | Feature not available on this motor |
| 38 | ERROR_IN_MOTION | Motor is currently moving |
| 40 | ERROR_LAST_PRESET_REACHED | Already at the last preset position |
| 42 | ERROR_LOW_PRIORITY | Command rejected due to low priority |
| 43 | ERROR_WINK_IN_PROGRESS | Wink operation in progress |
| 45 | ERROR_DIAGNOSTIC_UNAVAILABLE | Diagnostic data not available |
| 47 | ERROR_END_LIMITS_SET | End limits already configured |
| 48 | ERROR_THERMAL_PROTECTION | Motor thermal protection activated |
| 49 | ERROR_OBSTACLE_DETECTION | Obstacle detected during movement |
| 50 | ERROR_INCORRECT_PARAMS | Invalid or missing parameters |
| 254 | ERROR_UNKNOWN | Unknown error occurred |
| 255 | ERROR_BUSY | Motor is busy processing another command |

---

## Examples

### Complete Usage Example

```python
from custom_components.woow_tech_somfy_cover.api.client import SomfyClient
from custom_components.woow_tech_somfy_cover.api.models import MovementState

async def main():
    # Create client
    client = SomfyClient(
        host="192.168.1.77",
        target_id="160326",
        key="FBE90399BA25B4B67DC1B23BE0D9C084"
    )

    try:
        # Connect
        await client.connect()
        print("Connected to motor")

        # Get device info
        info = await client.get_device_info()
        print(f"Motor: {info.model}")
        print(f"Firmware: {info.firmware}")

        # Get current position
        status = await client.get_position()
        print(f"Position: {status.position}%")

        # Move to 50%
        await client.move_to_position(50.0)
        print("Moving to 50%")

        # Wait for movement to complete
        while True:
            await asyncio.sleep(1)
            status = await client.get_position()
            print(f"Current position: {status.position}%")

            if status.is_stopped:
                print("Movement complete")
                break

    finally:
        await client.close()
```

### Error Handling Example

```python
from custom_components.woow_tech_somfy_cover.api.client import SomfyClient
from custom_components.woow_tech_somfy_cover.errors import (
    SomfyAPIError,
    SomfyTimeoutError,
    SomfyConnectionError
)

async def safe_move_up(client):
    try:
        await client.move_up()
        return True

    except SomfyTimeoutError:
        print("Motor didn't respond - may be offline")
        return False

    except SomfyAPIError as err:
        if err.code == 32:  # ERROR_DEVICE_LOCKED
            print("Motor is locked by another client")
        elif err.code == 48:  # ERROR_THERMAL_PROTECTION
            print("Motor overheated - wait for cooldown")
        elif err.code == 34:  # ERROR_END_LIMITS_NOT_SET
            print("End limits not configured")
        else:
            print(f"Motor error: {err.message} (code {err.code})")
        return False

    except SomfyConnectionError:
        print("Connection error - check network")
        return False
```

### Direct API Usage (Without Client)

```python
from custom_components.woow_tech_somfy_cover.api.protocol import SomfyProtocol
from custom_components.woow_tech_somfy_cover.api.encryption import SomfyEncryption
from custom_components.woow_tech_somfy_cover.api.transport import SomfyTransport

# Initialize components
protocol = SomfyProtocol("160326")
encryption = SomfyEncryption("FBE90399BA25B4B67DC1B23BE0D9C084")
transport = SomfyTransport(
    host="192.168.1.77",
    encryption=encryption,
    target_id="160326"
)

# Connect
await transport.connect()

# Build request
request = protocol.build_request("move.up")

# Send encrypted
response = await transport.send_encrypted(request)

# Parse response
data = protocol.parse_response(response)
print(f"Result: {data}")

# Close
await transport.close()
```

---

## Thread Safety

All API methods are thread-safe:

- `SomfyClient`: Uses transport lock
- `SomfyTransport`: Uses `asyncio.Lock` to serialize requests
- `SomfyProtocol`: Stateless (incremental ID is not thread-critical)
- `SomfyEncryption`: Stateless (random IV per call)

Multiple requests to the same motor are automatically serialized. Multiple motors can be controlled concurrently.

---

## Performance Tips

1. **Reuse client instances**: Creating a client per request is inefficient
2. **Use async context manager**: Ensures proper cleanup
3. **Batch operations**: Send multiple commands only if needed (motor processes one at a time)
4. **Monitor is_moving**: Poll position only when needed
5. **Handle timeouts gracefully**: First command after idle may be slow (wake-up)

---

## Version History

- **v1.0.0**: Initial API implementation
- **v1.0.1**: Added YAML support
- **v1.0.2**: Improved YAML parsing (unquoted hex values)
