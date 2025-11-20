#!/usr/bin/env python3
"""
Working TLS connection test - Now that we can connect, let's try to control the motor.
"""

import socket
import json
import ssl
import time

HOST = "192.168.1.77"
PORT = 443
TARGET_ID = "160326"
PIN = "9679"

def send_and_receive(ssl_sock, message, description):
    """Send a message and try to receive response"""
    msg_str = json.dumps(message)
    print(f"\n{description}")
    print(f"  Sending: {msg_str}")

    # Try with newline
    ssl_sock.sendall((msg_str + "\n").encode())

    # Try to receive with different strategies
    ssl_sock.settimeout(2)
    responses = []

    for attempt in range(3):
        try:
            data = ssl_sock.recv(4096)
            if data:
                print(f"  Response (attempt {attempt+1}): {data}")
                responses.append(data)
                try:
                    decoded = data.decode()
                    print(f"  Decoded: {decoded}")
                except:
                    print(f"  Hex: {data.hex()}")
        except socket.timeout:
            if attempt == 0:
                print(f"  No immediate response, waiting...")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Recv error: {e}")
            break

    return responses

def test_full_session():
    """Full test session with TLS"""
    print("="*60)
    print("Full Somfy Control Session Test")
    print("="*60)

    try:
        # Connect
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        print(f"Connecting to {HOST}:{PORT}...")
        sock.connect((HOST, PORT))
        print("Connected!")

        # TLS handshake
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')
        context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

        print("Starting TLS handshake...")
        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        print(f"TLS OK: {ssl_sock.version()} / {ssl_sock.cipher()[0]}")

        # Step 1: Authentication
        auth_msg = {
            "method": "security.auth",
            "params": {
                "targetID": TARGET_ID,
                "code": PIN
            },
            "id": 1
        }
        send_and_receive(ssl_sock, auth_msg, "Step 1: Authentication")

        time.sleep(1)

        # Step 2: Try move up
        move_up = {
            "method": "move.up",
            "params": {"targetID": TARGET_ID},
            "id": 2
        }
        send_and_receive(ssl_sock, move_up, "Step 2: Move Up")

        time.sleep(2)

        # Step 3: Try stop
        stop_msg = {
            "method": "move.stop",
            "params": {"targetID": TARGET_ID},
            "id": 3
        }
        send_and_receive(ssl_sock, stop_msg, "Step 3: Stop")

        time.sleep(2)

        # Step 4: Try move down
        move_down = {
            "method": "move.down",
            "params": {"targetID": TARGET_ID},
            "id": 4
        }
        send_and_receive(ssl_sock, move_down, "Step 4: Move Down")

        time.sleep(2)

        # Step 5: Try stop again
        stop_msg2 = {
            "method": "move.stop",
            "params": {"targetID": TARGET_ID},
            "id": 5
        }
        send_and_receive(ssl_sock, stop_msg2, "Step 5: Stop")

        # Step 6: Try to get status
        status_msg = {
            "method": "status.get",
            "params": {"targetID": TARGET_ID},
            "id": 6
        }
        send_and_receive(ssl_sock, status_msg, "Step 6: Get Status")

        # Step 7: Try different method names
        print("\n" + "="*60)
        print("Trying alternative command formats...")
        print("="*60)

        alternatives = [
            {"method": "getPosition", "params": {"targetID": TARGET_ID}, "id": 7},
            {"method": "myPosition", "params": {"targetID": TARGET_ID}, "id": 8},
            {"method": "move.my", "params": {"targetID": TARGET_ID}, "id": 9},
            {"method": "move.position", "params": {"targetID": TARGET_ID, "position": 50}, "id": 10},
            {"method": "hello", "id": 11},
        ]

        for msg in alternatives:
            send_and_receive(ssl_sock, msg, f"Testing: {msg['method']}")
            time.sleep(0.5)

        ssl_sock.close()
        print("\n" + "="*60)
        print("Session complete")
        print("="*60)

    except Exception as e:
        print(f"\nError: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

def test_without_auth():
    """Test sending commands without auth first"""
    print("\n" + "="*60)
    print("Test: Direct Commands Without Auth")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((HOST, PORT))

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')
        context.options |= 0x4

        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        print(f"Connected with TLS")

        # Try move directly without auth
        move_msg = {
            "method": "move.up",
            "params": {"targetID": TARGET_ID},
            "id": 1
        }
        send_and_receive(ssl_sock, move_msg, "Direct Move (no auth)")

        ssl_sock.close()

    except Exception as e:
        print(f"Error: {e}")

def test_multiple_commands_batch():
    """Send multiple commands in one batch"""
    print("\n" + "="*60)
    print("Test: Batch Commands")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((HOST, PORT))

        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')
        context.options |= 0x4

        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        print(f"Connected with TLS")

        # Send batch
        batch = [
            {"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 1},
            {"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 2},
        ]

        batch_str = "\n".join([json.dumps(msg) for msg in batch]) + "\n"
        print(f"Sending batch:\n{batch_str}")
        ssl_sock.sendall(batch_str.encode())

        # Try to read multiple responses
        ssl_sock.settimeout(3)
        for i in range(5):
            try:
                data = ssl_sock.recv(4096)
                if data:
                    print(f"Response {i+1}: {data}")
            except socket.timeout:
                break

        ssl_sock.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_full_session()
    test_without_auth()
    test_multiple_commands_batch()
