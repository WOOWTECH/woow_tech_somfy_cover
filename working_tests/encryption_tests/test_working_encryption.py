#!/usr/bin/env python3
"""
Test 9: Working Encryption Method Comparison
============================================
This test implements BOTH encryption methods to find which one works:
1. PKCS7 padding (current implementation)
2. Zero-padding (mentioned by user as "old working code")

We'll test both methods and see which one actually moves the motor.
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
TARGET_ID = "160326"  # MUST be string, not int
KEY_HEX = "FBE90399BA25B4B67DC1B23BE0D9C084"
KEY_BYTES = bytes.fromhex(KEY_HEX)

BLOCK_SIZE = 16


def pad_pkcs7(data: bytes) -> bytes:
    """PKCS7 padding (current implementation)."""
    padding_length = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    padding = bytes([padding_length] * padding_length)
    return data + padding


def pad_zero(data: bytes) -> bytes:
    """Zero-padding (mentioned as "old working code")."""
    padding_needed = -len(data) % BLOCK_SIZE
    return data + b"\0" * padding_needed


def encrypt_method_pkcs7(plaintext: str) -> bytes:
    """Encrypt using PKCS7 padding (current implementation)."""
    # Generate random IV
    iv = os.urandom(BLOCK_SIZE)

    # Pad plaintext to block size (PKCS7)
    plaintext_bytes = plaintext.encode("utf-8")
    padded = pad_pkcs7(plaintext_bytes)

    # Encrypt
    cipher = Cipher(
        algorithms.AES(KEY_BYTES), modes.CBC(iv), backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    # Return IV + ciphertext
    return iv + ciphertext


def encrypt_method_zero(plaintext: str) -> bytes:
    """Encrypt using zero-padding (user's "old working code")."""
    # Generate random IV
    iv = os.urandom(BLOCK_SIZE)

    # Pad plaintext to block size (zero-padding)
    plaintext_bytes = plaintext.encode("utf-8")
    padded = pad_zero(plaintext_bytes)

    # Encrypt
    cipher = Cipher(
        algorithms.AES(KEY_BYTES), modes.CBC(iv), backend=default_backend()
    )
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded) + encryptor.finalize()

    # Return IV + ciphertext
    return iv + ciphertext


def send_udp_command(payload: bytes, description: str) -> bool:
    """Send UDP command and wait for response."""
    print(f"\n{description}")
    print(f"  Payload size: {len(payload)} bytes")
    print(f"  IV: {payload[:16].hex()}")
    print(f"  Ciphertext: {payload[16:].hex()}")

    try:
        # Create socket with same configuration as working code
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind to same port (as per working code)
        sock.bind(("", UDP_PORT))

        # Send to device
        sock.sendto(payload, (HOST, UDP_PORT))
        print(f"  ✓ Sent to {HOST}:{UDP_PORT}")

        # Try to receive response
        try:
            response, addr = sock.recvfrom(4096)
            print(f"  ✓ Response received from {addr}: {len(response)} bytes")
            print(f"  Response hex: {response.hex()}")
            return True
        except socket.timeout:
            print(f"  ⚠ No response (timeout)")
            return False
        finally:
            sock.close()

    except Exception as e:
        print(f"  ✗ Error: {type(e).__name__}: {e}")
        return False


def build_json_rpc_message(method: str, request_id: int = 1) -> str:
    """Build JSON-RPC message with exact format."""
    message = {
        "method": method,
        "params": {"targetID": TARGET_ID},  # String, not int!
        "id": request_id
    }

    # Use compact JSON (no spaces) as per working code
    return json.dumps(message, separators=(",", ":"))


def test_sequence_with_method(method_name: str, encrypt_func):
    """Test a complete movement sequence with one encryption method."""
    print("\n" + "=" * 70)
    print(f"Testing with {method_name}")
    print("=" * 70)

    results = []

    # 1. Move up
    json_msg = build_json_rpc_message("move.up", 1)
    print(f"\n[1] Command: move.up")
    print(f"    JSON: {json_msg}")
    encrypted = encrypt_func(json_msg)
    result = send_udp_command(encrypted, f"Sending move.up ({method_name})")
    results.append(("move.up", result))

    print("\n    Waiting 2 seconds for motor to move...")
    time.sleep(2)

    # 2. Stop
    json_msg = build_json_rpc_message("move.stop", 2)
    print(f"\n[2] Command: move.stop")
    print(f"    JSON: {json_msg}")
    encrypted = encrypt_func(json_msg)
    result = send_udp_command(encrypted, f"Sending move.stop ({method_name})")
    results.append(("move.stop", result))

    print("\n    Waiting 1 second...")
    time.sleep(1)

    # 3. Move down
    json_msg = build_json_rpc_message("move.down", 3)
    print(f"\n[3] Command: move.down")
    print(f"    JSON: {json_msg}")
    encrypted = encrypt_func(json_msg)
    result = send_udp_command(encrypted, f"Sending move.down ({method_name})")
    results.append(("move.down", result))

    print("\n    Waiting 2 seconds for motor to move...")
    time.sleep(2)

    # 4. Stop
    json_msg = build_json_rpc_message("move.stop", 4)
    print(f"\n[4] Command: move.stop")
    print(f"    JSON: {json_msg}")
    encrypted = encrypt_func(json_msg)
    result = send_udp_command(encrypted, f"Sending move.stop ({method_name})")
    results.append(("move.stop", result))

    # 5. Try to get position
    json_msg = build_json_rpc_message("status.position", 5)
    print(f"\n[5] Command: status.position")
    print(f"    JSON: {json_msg}")
    encrypted = encrypt_func(json_msg)
    result = send_udp_command(encrypted, f"Sending status.position ({method_name})")
    results.append(("status.position", result))

    # Summary
    print("\n" + "=" * 70)
    print(f"Results for {method_name}:")
    print("=" * 70)
    for command, received_response in results:
        status = "✓ Response" if received_response else "✗ No response"
        print(f"  {command:20s}: {status}")

    return results


def main():
    """Run complete test comparing both methods."""
    print("=" * 70)
    print("TEST 9: WORKING ENCRYPTION METHOD COMPARISON")
    print("=" * 70)
    print(f"\nDevice: {HOST}:{UDP_PORT}")
    print(f"Target ID: {TARGET_ID} (string)")
    print(f"Key: {KEY_HEX}")
    print("\nThis test compares two encryption methods:")
    print("  1. PKCS7 padding (current implementation)")
    print("  2. Zero-padding (mentioned as 'old working code')")
    print("\nWATCH THE MOTOR - does it move?")
    print("=" * 70)

    input("\nPress ENTER to start test with PKCS7 padding...")

    # Test Method 1: PKCS7
    pkcs7_results = test_sequence_with_method("PKCS7 Padding", encrypt_method_pkcs7)

    print("\n\n")
    input("Press ENTER to start test with Zero-padding...")

    # Test Method 2: Zero-padding
    zero_results = test_sequence_with_method("Zero-padding", encrypt_method_zero)

    # Final comparison
    print("\n\n")
    print("=" * 70)
    print("FINAL COMPARISON")
    print("=" * 70)

    pkcs7_responses = sum(1 for _, r in pkcs7_results if r)
    zero_responses = sum(1 for _, r in zero_results if r)

    print(f"\nPKCS7 Padding: {pkcs7_responses}/5 responses received")
    print(f"Zero-padding:  {zero_responses}/5 responses received")

    print("\n" + "=" * 70)
    print("IMPORTANT: Did the motor physically move during ANY test?")
    print("=" * 70)
    print("\nIf YES:")
    print("  - Which method made it move? (PKCS7 or Zero-padding?)")
    print("  - Did you receive UDP responses back?")
    print("\nIf NO:")
    print("  - The issue might be:")
    print("    * Motor not configured/commissioned")
    print("    * Need TCP/TLS authentication first")
    print("    * Different packet format needed")
    print("    * Network/firewall issue")
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
