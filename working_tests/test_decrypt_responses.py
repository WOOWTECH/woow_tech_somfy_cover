#!/usr/bin/env python3
"""
Decrypt and analyze the responses we received from the motor.
This will tell us if commands are being accepted and what the motor's status is.
"""

import socket
import json
import os
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Device configuration
HOST = "192.168.1.77"
UDP_PORT = 55055
TARGET_ID = "160326"
KEY_HEX = "FBE90399BA25B4B67DC1B23BE0D9C084"
KEY_BYTES = bytes.fromhex(KEY_HEX)

BLOCK_SIZE = 16


def unpad_pkcs7(data: bytes) -> bytes:
    """Remove PKCS7 padding."""
    if not data:
        raise ValueError("Cannot unpad empty data")

    padding_length = data[-1]
    if padding_length < 1 or padding_length > BLOCK_SIZE:
        raise ValueError(f"Invalid padding length: {padding_length}")

    # Verify all padding bytes are correct
    padding = data[-padding_length:]
    if not all(b == padding_length for b in padding):
        raise ValueError("Invalid PKCS7 padding")

    return data[:-padding_length]


def unpad_zero(data: bytes) -> bytes:
    """Remove zero-padding."""
    return data.rstrip(b'\0')


def decrypt_response(encrypted_data: bytes, unpad_func) -> str:
    """Decrypt a response from the motor."""
    if len(encrypted_data) < BLOCK_SIZE + 1:
        raise ValueError("Data too short to contain IV and ciphertext")

    # Extract IV and ciphertext
    iv = encrypted_data[:BLOCK_SIZE]
    ciphertext = encrypted_data[BLOCK_SIZE:]

    # Decrypt
    cipher = Cipher(
        algorithms.AES(KEY_BYTES), modes.CBC(iv), backend=default_backend()
    )
    decryptor = cipher.decryptor()
    padded_plaintext = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove padding
    plaintext = unpad_func(padded_plaintext)
    return plaintext.decode("utf-8")


def pad_zero(data: bytes) -> bytes:
    """Zero-padding."""
    padding_needed = -len(data) % BLOCK_SIZE
    return data + b"\0" * padding_needed


def encrypt_and_send(method: str, request_id: int) -> tuple[bool, bytes | None]:
    """Send command and receive response."""
    # Build message
    message = {
        "method": method,
        "params": {"targetID": TARGET_ID},
        "id": request_id
    }
    json_str = json.dumps(message, separators=(",", ":"))

    # Encrypt with zero-padding (worked better in test)
    iv = os.urandom(BLOCK_SIZE)
    plaintext_bytes = json_str.encode("utf-8")
    padded = pad_zero(plaintext_bytes)

    cipher = Cipher(
        algorithms.AES(KEY_BYTES), modes.CBC(iv), backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()
    encrypted = iv + ciphertext

    # Send
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", UDP_PORT))

        sock.sendto(encrypted, (HOST, UDP_PORT))
        print(f"Sent: {method}")

        # Receive
        try:
            response, addr = sock.recvfrom(4096)
            print(f"  Response: {len(response)} bytes")
            sock.close()
            return True, response
        except socket.timeout:
            print(f"  No response")
            sock.close()
            return False, None

    except Exception as e:
        print(f"  Error: {e}")
        return False, None


def main():
    """Test commands and decrypt responses."""
    print("=" * 70)
    print("DECRYPT AND ANALYZE MOTOR RESPONSES")
    print("=" * 70)
    print(f"\nDevice: {HOST}:{UDP_PORT}")
    print(f"Target ID: {TARGET_ID}")
    print("\nSending commands and decrypting responses...")
    print("=" * 70)

    tests = [
        ("move.up", "Move motor UP"),
        ("move.stop", "Stop motor (after up)"),
        ("move.down", "Move motor DOWN"),
        ("move.stop", "Stop motor (after down)"),
        ("status.position", "Get position"),
        ("status.info", "Get device info"),
    ]

    request_id = 1
    for method, description in tests:
        print(f"\n{'=' * 70}")
        print(f"Test: {description}")
        print(f"Method: {method}")
        print('=' * 70)

        success, encrypted_response = encrypt_and_send(method, request_id)

        if success and encrypted_response:
            # Try both padding methods to decrypt
            decrypted = None
            padding_method = None

            # Try zero-padding first
            try:
                decrypted = decrypt_response(encrypted_response, unpad_zero)
                padding_method = "zero-padding"
            except Exception as e1:
                # Try PKCS7
                try:
                    decrypted = decrypt_response(encrypted_response, unpad_pkcs7)
                    padding_method = "PKCS7"
                except Exception as e2:
                    print(f"  ✗ Could not decrypt with zero-padding: {e1}")
                    print(f"  ✗ Could not decrypt with PKCS7: {e2}")
                    print(f"  Raw response: {encrypted_response.hex()}")

            if decrypted:
                print(f"  ✓ Decrypted ({padding_method}):")
                print(f"    Raw: {decrypted}")

                # Try to parse JSON
                try:
                    json_data = json.loads(decrypted)
                    print(f"    Parsed JSON:")
                    print(json.dumps(json_data, indent=6))

                    # Check for errors
                    if "error" in json_data:
                        error = json_data["error"]
                        print(f"\n    ⚠ ERROR IN RESPONSE:")
                        if isinstance(error, dict):
                            print(f"      Code: {error.get('id', 'N/A')}")
                            print(f"      Message: {error.get('title', 'Unknown')}")
                        else:
                            print(f"      {error}")
                    elif "result" in json_data:
                        result = json_data["result"]
                        print(f"\n    ✓ SUCCESS - Result:")
                        print(json.dumps(result, indent=6))

                except json.JSONDecodeError as e:
                    print(f"    ⚠ Not valid JSON: {e}")
        else:
            print(f"  ✗ No response received")

        request_id += 1

        # Wait between commands
        if "move" in method:
            print(f"\n  Waiting 2 seconds...")
            time.sleep(2)
        else:
            time.sleep(0.5)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)
    print("\nDid you SEE or HEAR the motor move?")
    print("Check the decrypted responses above for:")
    print("  - Error messages (if commands were rejected)")
    print("  - Position data (if status.position worked)")
    print("  - Device info (if status.info worked)")
    print("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
