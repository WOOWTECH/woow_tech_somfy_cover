#!/usr/bin/env python3
"""
Test 5: UDP with AES-128-CBC Encryption
According to docs:
- Structure: IV (16 bytes) + Encrypted Data (padded to 16-byte multiple)
- All Synergy commands except ping need encryption
Port: 55055
"""

import socket
import json
import os
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Device configuration
HOST = "192.168.1.77"
PORT = 55055
TARGET_ID = "160326"
# Encryption key from docs
KEY = bytes.fromhex("FBE90399BA25B4B67DC1B23BE0D9C084")

def encrypt_message(message_str, key):
    """Encrypt message with AES-128-CBC"""
    # Generate random IV
    iv = os.urandom(16)

    # Pad message to 16-byte multiple with zeros (as per docs)
    message_bytes = message_str.encode('utf-8')
    padding_length = 16 - (len(message_bytes) % 16)
    if padding_length != 16:  # Don't add padding if already multiple of 16
        padded_message = message_bytes + (b'\x00' * padding_length)
    else:
        padded_message = message_bytes

    # Encrypt
    cipher = AES.new(key, AES.MODE_CBC, iv)
    encrypted = cipher.encrypt(padded_message)

    # Return IV + encrypted data
    return iv + encrypted

def udp_encrypted_status():
    print("=" * 60)
    print("TEST 5: UDP with AES-128-CBC Encryption")
    print("=" * 60)

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        # Prepare status.info request
        request = {
            "method": "status.info",
            "params": {
                "targetID": TARGET_ID
            },
            "id": 1
        }

        request_str = json.dumps(request)
        print(f"\nPlaintext request:")
        print(request_str)

        # Encrypt
        encrypted_data = encrypt_message(request_str, KEY)
        print(f"\nEncrypted data length: {len(encrypted_data)} bytes")
        print(f"IV (first 16 bytes): {encrypted_data[:16].hex()}")
        print(f"Encrypted payload: {encrypted_data[16:].hex()[:64]}...")

        # Send request
        sock.sendto(encrypted_data, (HOST, PORT))
        print(f"\nSent to {HOST}:{PORT}")

        # Wait for response
        print("\nWaiting for response...")
        data, addr = sock.recvfrom(1024)

        print(f"\nResponse received from {addr} ({len(data)} bytes):")
        print(f"Raw data: {data.hex()[:128]}...")

        # Try to decrypt response
        try:
            if len(data) >= 16:
                iv = data[:16]
                encrypted = data[16:]

                cipher = AES.new(KEY, AES.MODE_CBC, iv)
                decrypted = cipher.decrypt(encrypted)

                # Remove padding (zero padding)
                decrypted_str = decrypted.rstrip(b'\x00').decode('utf-8')

                print(f"\nDecrypted response:")
                print(decrypted_str)

                response = json.loads(decrypted_str)
                print(f"\nParsed response:")
                print(json.dumps(response, indent=2))

                if response.get("result"):
                    print("\n✓ SUCCESS: Encrypted communication working!")
                    return True
                else:
                    print("\n✗ FAILED: Negative response")
                    return False
            else:
                print("\n✗ Response too short to be encrypted")
                return False

        except Exception as e:
            print(f"\n✗ Failed to decrypt response: {e}")
            print(f"Trying to parse as plain JSON...")
            try:
                response = json.loads(data.decode('utf-8'))
                print(json.dumps(response, indent=2))
            except:
                pass
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
    # Check if pycryptodome is installed
    try:
        from Crypto.Cipher import AES
    except ImportError:
        print("Installing pycryptodome...")
        import subprocess
        subprocess.check_call(["pip3", "install", "pycryptodome"])

    result = udp_encrypted_status()
    exit(0 if result else 1)
