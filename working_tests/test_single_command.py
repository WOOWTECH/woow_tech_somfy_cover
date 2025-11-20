#!/usr/bin/env python3
"""
Test sending single commands per connection.
The device might process commands even without sending responses.
"""

import socket
import json
import ssl
import time

HOST = "192.168.1.77"
PORT = 443
TARGET_ID = "160326"
PIN = "9679"

def send_single_command(message, description):
    """Send a single command in a fresh connection"""
    print(f"\n{'='*60}")
    print(description)
    print(f"{'='*60}")

    try:
        # Fresh connection each time
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        print(f"Connecting...")
        sock.connect((HOST, PORT))

        # TLS
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')
        context.options |= 0x4

        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        print(f"TLS connected")

        # Send message
        msg_str = json.dumps(message) + "\n"
        print(f"Sending: {msg_str.strip()}")
        ssl_sock.sendall(msg_str.encode())

        # Wait for potential response
        ssl_sock.settimeout(2)
        try:
            response = ssl_sock.recv(4096)
            if response:
                print(f"Response: {response}")
                try:
                    print(f"Decoded: {response.decode()}")
                except:
                    print(f"Hex: {response.hex()}")
        except socket.timeout:
            print("No response (command may have been accepted)")

        ssl_sock.close()
        print("Connection closed")
        return True

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_sequence():
    """Test a sequence of commands with fresh connections"""

    print("="*60)
    print("SINGLE COMMAND PER CONNECTION TEST")
    print("Testing if motor responds to commands")
    print("="*60)

    # 1. Authenticate
    send_single_command(
        {"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 1},
        "Command 1: Authenticate"
    )
    time.sleep(1)

    # 2. Move up for 2 seconds
    send_single_command(
        {"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 2},
        "Command 2: MOVE UP - Watch the motor!"
    )

    print("\n*** WAITING 3 SECONDS - IS THE MOTOR MOVING UP? ***")
    time.sleep(3)

    # 3. Stop
    send_single_command(
        {"method": "move.stop", "params": {"targetID": TARGET_ID}, "id": 3},
        "Command 3: STOP"
    )
    time.sleep(1)

    # 4. Move down
    send_single_command(
        {"method": "move.down", "params": {"targetID": TARGET_ID}, "id": 4},
        "Command 4: MOVE DOWN - Watch the motor!"
    )

    print("\n*** WAITING 3 SECONDS - IS THE MOTOR MOVING DOWN? ***")
    time.sleep(3)

    # 5. Stop
    send_single_command(
        {"method": "move.stop", "params": {"targetID": TARGET_ID}, "id": 5},
        "Command 5: STOP"
    )

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)
    print("\nDid you see any motor movement?")
    print("If YES: The device accepts commands without sending responses")
    print("If NO: We need to try different command formats")

def test_auth_plus_command():
    """Try sending auth and command together in same connection"""
    print("\n" + "="*60)
    print("Test: Auth + Command in same connection")
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
        print(f"Connected")

        # Send auth
        auth = {"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 1}
        ssl_sock.sendall((json.dumps(auth) + "\n").encode())
        print(f"Sent auth")

        time.sleep(0.5)

        # Send move
        move = {"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 2}
        ssl_sock.sendall((json.dumps(move) + "\n").encode())
        print(f"Sent move up")

        print("\n*** WAITING 5 SECONDS - IS THE MOTOR MOVING? ***")
        time.sleep(5)

        # Send stop
        stop = {"method": "move.stop", "params": {"targetID": TARGET_ID}, "id": 3}
        ssl_sock.sendall((json.dumps(stop) + "\n").encode())
        print(f"Sent stop")

        ssl_sock.close()

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_sequence()
    print("\n\n")
    test_auth_plus_command()
