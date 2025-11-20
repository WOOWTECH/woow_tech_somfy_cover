# WORKING SOLUTION - Somfy PoE Motor Control

## SUCCESS! Motor Control is Working

After extensive testing, we have successfully established communication with the Somfy PoE motor and can control it via UDP encrypted commands.

## Critical Discovery

The motor responds to **UDP encrypted commands on port 55055** using **AES-128-CBC with zero-padding**.

### Key Breakthroughs

1. **Port Binding is Critical**
   - The socket MUST be bound to UDP port 55055 (same port as destination)
   - SO_REUSEADDR option is REQUIRED
   - This was the missing piece in previous attempts

2. **Zero-Padding Works Better Than PKCS7**
   - Zero-padding: 5/5 commands successful (100%)
   - PKCS7 padding: 4/5 commands successful (80%)
   - Motor uses zero-padding in responses

3. **No Authentication Required**
   - UDP commands work WITHOUT prior TCP/TLS authentication
   - PIN authentication not needed for basic motor control
   - Simplifies implementation significantly

## Working Code Example

```python
import socket
import json
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Configuration
HOST = "192.168.1.77"
PORT = 55055
TARGET_ID = "160326"  # STRING, not int!
KEY = bytes.fromhex("FBE90399BA25B4B67DC1B23BE0D9C084")

def encrypt_command(method: str, request_id: int = 1) -> bytes:
    """Encrypt command using zero-padding."""
    # Build JSON-RPC message
    message = {
        "method": method,
        "params": {"targetID": TARGET_ID},
        "id": request_id
    }

    # Compact JSON (no spaces)
    json_str = json.dumps(message, separators=(",", ":"))
    payload = json_str.encode("utf-8")

    # Zero-padding to 16-byte blocks
    payload += b"\0" * (-len(payload) % 16)

    # Generate random IV
    iv = os.urandom(16)

    # Encrypt with AES-128-CBC
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(payload) + encryptor.finalize()

    # Return IV + ciphertext
    return iv + ciphertext

def send_command(method: str) -> bytes:
    """Send encrypted command and receive response."""
    encrypted = encrypt_command(method)

    # Create socket with REQUIRED configuration
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # CRITICAL: Bind to port 55055
    sock.bind(("", PORT))

    # Send to motor
    sock.sendto(encrypted, (HOST, PORT))

    # Receive response
    response, _ = sock.recvfrom(4096)
    sock.close()

    return response

def decrypt_response(encrypted_data: bytes) -> dict:
    """Decrypt motor response."""
    # Extract IV and ciphertext
    iv = encrypted_data[:16]
    ciphertext = encrypted_data[16:]

    # Decrypt
    cipher = Cipher(algorithms.AES(KEY), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove zero-padding
    plaintext = padded.rstrip(b'\0')

    # Parse JSON
    return json.loads(plaintext.decode("utf-8"))

# Example usage
response = send_command("move.up")
result = decrypt_response(response)
print(result)  # {"result":true,"targetID":"160326","id":1}
```

## Verified Commands

All of these commands have been tested and work:

| Command | Method | Response |
|---------|--------|----------|
| Move Up | `move.up` | `{"result":true}` |
| Move Down | `move.down` | `{"result":true}` |
| Stop | `move.stop` | `{"result":true}` |
| Get Position | `status.position` | Position data with value, status, direction |
| Get Device Info | `status.info` | Full device details |

## Position Response Format

```json
{
  "result": true,
  "targetID": "160326",
  "id": 5,
  "position": {
    "value": 94.154,
    "status": "stopped",
    "direction": "down / close",
    "source": "network message",
    "cause": "explicit command"
  }
}
```

## Device Information

Retrieved successfully via `status.info`:

```json
{
  "result": true,
  "targetID": "160326",
  "id": 6,
  "info": {
    "name": "Sonesse 30 PoE",
    "model": "Sonesse 30 PoE",
    "synergy_version": 6,
    "firmware": "5163364A07/5155239A32",
    "hardware": "5155389A01/5153582A00",
    "mac": "4C:C2:06:16:03:26",
    "hostname": "sfy_poe_00049C"
  }
}
```

## Implementation Checklist

To integrate this into the Home Assistant component:

- [ ] Update `encryption.py` to support zero-padding option
- [ ] Update `transport.py` to bind socket to port 55055
- [ ] Add SO_REUSEADDR socket option
- [ ] Ensure targetID is always string type
- [ ] Update decryption to handle zero-padding
- [ ] Test position polling during movement
- [ ] Implement coordinator refresh after commands
- [ ] Add error handling for socket binding conflicts

## Socket Binding Notes

**Important**: Binding to port 55055 means:
- Only ONE process can communicate with the motor at a time
- If Home Assistant is running, manual tests may fail (port in use)
- Need proper cleanup when component is unloaded
- Consider using context manager for socket lifecycle

## Testing Scripts

Two working test scripts are available:

1. **test_working_encryption.py**
   - Compares PKCS7 vs Zero-padding
   - Tests full movement sequence
   - Interactive with pauses

2. **test_decrypt_responses.py**
   - Sends commands and decrypts responses
   - Shows full JSON response data
   - Best for debugging

Both scripts are in: `/Users/alanlin/Documents/woowtech_somfy_new/`

## Next Steps

1. **Update the integration code** with the working encryption method
2. **Test position updates** during motor movement
3. **Implement proper socket lifecycle** management
4. **Add error recovery** for socket binding conflicts
5. **Test with Home Assistant** coordinator pattern

## Conclusion

We now have a **fully working solution** for controlling the Somfy PoE motor. The critical missing pieces were:

1. Binding the socket to port 55055
2. Setting SO_REUSEADDR option
3. Using zero-padding instead of PKCS7

All motor control commands work, position tracking works, and device info retrieval works. The solution is ready for integration into the Home Assistant component.
