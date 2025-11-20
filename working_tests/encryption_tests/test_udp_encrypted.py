#!/usr/bin/env python3
"""
Test UDP with AES encryption using the provided key.
This might be the missing piece for local control.
"""

import socket
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import binascii
import time

HOST = "192.168.1.77"
UDP_PORT = 55055
TARGET_ID = "160326"
PIN = "9679"
KEY_HEX = "FBE90399BA25B4B67DC1B23BE0D9C084"
KEY = bytes.fromhex(KEY_HEX)

def encrypt_aes_ecb(plaintext, key):
    """Encrypt using AES ECB mode"""
    cipher = AES.new(key, AES.MODE_ECB)
    padded = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded)

def decrypt_aes_ecb(ciphertext, key):
    """Decrypt using AES ECB mode"""
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted = cipher.decrypt(ciphertext)
    return unpad(decrypted, AES.block_size)

def encrypt_aes_cbc(plaintext, key, iv):
    """Encrypt using AES CBC mode"""
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded = pad(plaintext, AES.block_size)
    return cipher.encrypt(padded)

def send_encrypted_udp(message, description, mode="ecb"):
    """Send encrypted UDP message"""
    print(f"\n{description}")
    print(f"  Plaintext: {message}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)

        # Encrypt message
        plaintext = json.dumps(message).encode()

        if mode == "ecb":
            ciphertext = encrypt_aes_ecb(plaintext, KEY)
            print(f"  Encrypted (ECB): {ciphertext.hex()}")
        else:  # cbc
            iv = b'\x00' * 16  # Try zero IV first
            ciphertext = encrypt_aes_cbc(plaintext, KEY, iv)
            print(f"  Encrypted (CBC): {ciphertext.hex()}")

        # Send
        sock.sendto(ciphertext, (HOST, UDP_PORT))

        # Try to receive
        try:
            response, addr = sock.recvfrom(4096)
            print(f"  Response received: {response.hex()}")

            # Try to decrypt
            try:
                if mode == "ecb":
                    decrypted = decrypt_aes_ecb(response, KEY)
                else:
                    decrypted = unpad(response, AES.block_size)

                print(f"  Decrypted: {decrypted}")
                try:
                    print(f"  JSON: {json.loads(decrypted)}")
                except:
                    pass
            except Exception as e:
                print(f"  Could not decrypt: {e}")

            return True

        except socket.timeout:
            print(f"  No response")

        sock.close()

    except Exception as e:
        print(f"  Error: {e}")

    return False

def send_plain_with_auth_header(message, description):
    """Try sending with authentication in a header-like format"""
    print(f"\n{description}")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)

        # Create packet with auth header
        auth_header = {
            "targetID": TARGET_ID,
            "code": PIN,
            "key": KEY_HEX
        }

        packet = {
            "auth": auth_header,
            "command": message
        }

        data = json.dumps(packet).encode()
        print(f"  Sending: {packet}")

        sock.sendto(data, (HOST, UDP_PORT))

        try:
            response, addr = sock.recvfrom(4096)
            print(f"  Response: {response}")
            return True
        except socket.timeout:
            print(f"  No response")

        sock.close()

    except Exception as e:
        print(f"  Error: {e}")

    return False

def test_all_encrypted_formats():
    """Test various encrypted formats"""

    print("="*60)
    print("UDP ENCRYPTED COMMANDS TEST")
    print(f"Using KEY: {KEY_HEX}")
    print("="*60)

    # Test 1: Encrypted auth
    send_encrypted_udp(
        {"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 1},
        "Test 1: Encrypted Auth (ECB)",
        "ecb"
    )
    time.sleep(1)

    # Test 2: Encrypted move
    send_encrypted_udp(
        {"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 2},
        "Test 2: Encrypted Move Up (ECB)",
        "ecb"
    )
    time.sleep(3)

    # Test 3: Encrypted stop
    send_encrypted_udp(
        {"method": "move.stop", "params": {"targetID": TARGET_ID}, "id": 3},
        "Test 3: Encrypted Stop (ECB)",
        "ecb"
    )
    time.sleep(1)

    # Test 4: CBC mode
    send_encrypted_udp(
        {"method": "move.down", "params": {"targetID": TARGET_ID}, "id": 4},
        "Test 4: Encrypted Move Down (CBC)",
        "cbc"
    )
    time.sleep(3)

    send_encrypted_udp(
        {"method": "move.stop", "params": {"targetID": TARGET_ID}, "id": 5},
        "Test 5: Encrypted Stop (CBC)",
        "cbc"
    )
    time.sleep(1)

    # Test 6: Plain with auth header
    send_plain_with_auth_header(
        {"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 6},
        "Test 6: Plain JSON with Auth Header"
    )
    time.sleep(3)

    # Test 7: Try binary protocol
    print("\nTest 7: Binary Protocol")
    print("  Trying custom binary format...")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)

        # Simple binary: [target_id (4 bytes)][command (1 byte)]
        # target_id = 160326 = 0x0002727E
        # command: 1=up, 2=down, 3=stop
        binary_cmd = bytes.fromhex("0002727E01")  # Move up
        print(f"  Binary: {binary_cmd.hex()}")

        sock.sendto(binary_cmd, (HOST, UDP_PORT))

        try:
            response, addr = sock.recvfrom(4096)
            print(f"  Response: {response.hex()}")
        except socket.timeout:
            print(f"  No response")

        sock.close()

    except Exception as e:
        print(f"  Error: {e}")

    # Test 8: Encrypted binary
    print("\nTest 8: Encrypted Binary")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)

        binary_cmd = bytes.fromhex("0002727E02")  # Move down
        encrypted = encrypt_aes_ecb(binary_cmd, KEY)
        print(f"  Encrypted binary: {encrypted.hex()}")

        sock.sendto(encrypted, (HOST, UDP_PORT))

        try:
            response, addr = sock.recvfrom(4096)
            print(f"  Response: {response.hex()}")
        except socket.timeout:
            print(f"  No response")

        sock.close()

    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "="*60)
    print("ENCRYPTED UDP TESTS COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_all_encrypted_formats()
    print("\nDid the motor move? If yes, we found the right format!")
