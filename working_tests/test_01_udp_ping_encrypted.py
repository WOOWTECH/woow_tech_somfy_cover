#!/usr/bin/env python3
"""
Test: UDP Ping with Encryption
FIXED VERSION: Ping requires encryption like all other commands!
Port: 55055
"""

import socket
import json
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Device configuration
HOST = "192.168.1.77"
PORT = 55055
TARGET_ID = "160326"
KEY_BYTES = bytes.fromhex("FBE90399BA25B4B67DC1B23BE0D9C084")

BLOCK_SIZE = 16


def pad_zero(data: bytes) -> bytes:
    """Zero-padding."""
    padding_needed = -len(data) % BLOCK_SIZE
    return data + b"\0" * padding_needed


def unpad_zero(data: bytes) -> bytes:
    """Remove zero-padding."""
    return data.rstrip(b'\0')


def udp_ping_encrypted():
    print("=" * 60)
    print("TEST: UDP PING (Encrypted)")
    print("=" * 60)

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", PORT))

    try:
        # Prepare ping request
        request = {
            "method": "status.ping",
            "params": {
                "targetID": TARGET_ID
            },
            "id": 1
        }

        request_str = json.dumps(request, separators=(",", ":"))
        print(f"\nPlaintext request:")
        print(request_str)

        # Encrypt
        payload = request_str.encode("utf-8")
        payload = pad_zero(payload)
        iv = os.urandom(BLOCK_SIZE)

        cipher = Cipher(algorithms.AES(KEY_BYTES), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(payload) + encryptor.finalize()

        encrypted = iv + ciphertext

        print(f"\nEncrypted message: {len(encrypted)} bytes")
        print(f"IV: {iv.hex()}")

        # Send request
        sock.sendto(encrypted, (HOST, PORT))
        print(f"\nSent to {HOST}:{PORT}")

        # Wait for response
        print("\nWaiting for response...")
        data, addr = sock.recvfrom(4096)

        print(f"\nEncrypted response received from {addr}: {len(data)} bytes")

        # Decrypt response
        response_iv = data[:BLOCK_SIZE]
        response_ciphertext = data[BLOCK_SIZE:]

        cipher = Cipher(algorithms.AES(KEY_BYTES), modes.CBC(response_iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded_plaintext = decryptor.update(response_ciphertext) + decryptor.finalize()

        plaintext = unpad_zero(padded_plaintext).decode("utf-8")

        print(f"\nDecrypted response:")
        print(plaintext)

        # Parse response
        response = json.loads(plaintext)
        print(f"\nParsed JSON:")
        print(json.dumps(response, indent=2))

        if response.get("result"):
            print("\n✓ SUCCESS: Motor responded to encrypted ping")
            return True
        else:
            print("\n✗ FAILED: Motor returned false")
            return False

    except socket.timeout:
        print("\n✗ TIMEOUT: No response received")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        sock.close()


if __name__ == "__main__":
    result = udp_ping_encrypted()
    exit(0 if result else 1)
