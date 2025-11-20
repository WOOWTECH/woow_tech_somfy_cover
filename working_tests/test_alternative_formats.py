#!/usr/bin/env python3
"""
Test alternative command formats based on Overkiz API documentation.
"""

import socket
import json
import ssl
import time

HOST = "192.168.1.77"
PORT = 443
TARGET_ID = "160326"
PIN = "9679"
KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"

def send_command(message, description):
    """Send a command and report result"""
    print(f"\n{description}")
    print(f"  Message: {json.dumps(message)}")

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

        msg_str = json.dumps(message) + "\n"
        ssl_sock.sendall(msg_str.encode())

        ssl_sock.settimeout(2)
        try:
            response = ssl_sock.recv(4096)
            if response:
                print(f"  Response: {response}")
                return response
        except socket.timeout:
            print(f"  No response")

        ssl_sock.close()

    except Exception as e:
        print(f"  Error: {e}")

    return None

def test_all_formats():
    """Try all possible command formats"""

    print("="*60)
    print("TESTING ALTERNATIVE COMMAND FORMATS")
    print("="*60)

    # Format 1: Standard JSON-RPC with targetID
    send_command(
        {
            "jsonrpc": "2.0",
            "method": "move.up",
            "params": {"targetID": TARGET_ID},
            "id": 1
        },
        "Format 1: JSON-RPC 2.0 with targetID"
    )
    time.sleep(2)

    # Format 2: Without jsonrpc version
    send_command(
        {
            "method": "move.up",
            "params": {"targetID": TARGET_ID},
            "id": 2
        },
        "Format 2: Simple JSON-RPC (current format)"
    )
    time.sleep(2)

    # Format 3: With deviceURL
    send_command(
        {
            "method": "move.up",
            "params": {
                "deviceURL": f"io://{TARGET_ID}/cover",
                "targetID": TARGET_ID
            },
            "id": 3
        },
        "Format 3: With deviceURL"
    )
    time.sleep(2)

    # Format 4: Execute action format
    send_command(
        {
            "method": "execute",
            "params": {
                "targetID": TARGET_ID,
                "action": "up"
            },
            "id": 4
        },
        "Format 4: Execute action"
    )
    time.sleep(2)

    # Format 5: Apply format (Overkiz style)
    send_command(
        {
            "method": "apply",
            "params": {
                "targetID": TARGET_ID,
                "actions": [
                    {
                        "deviceURL": f"io://{TARGET_ID}",
                        "commands": [
                            {
                                "name": "up"
                            }
                        ]
                    }
                ]
            },
            "id": 5
        },
        "Format 5: Overkiz apply format"
    )
    time.sleep(2)

    # Format 6: Direct action name
    send_command(
        {
            "method": "up",
            "params": {"targetID": TARGET_ID},
            "id": 6
        },
        "Format 6: Direct action as method"
    )
    time.sleep(2)

    # Format 7: setClosure
    send_command(
        {
            "method": "setClosure",
            "params": {
                "targetID": TARGET_ID,
                "closure": 0  # 0 = open, 100 = closed
            },
            "id": 7
        },
        "Format 7: setClosure to 0 (open)"
    )
    time.sleep(2)

    # Format 8: setPosition
    send_command(
        {
            "method": "setPosition",
            "params": {
                "targetID": TARGET_ID,
                "position": 100
            },
            "id": 8
        },
        "Format 8: setPosition to 100"
    )
    time.sleep(2)

    # Format 9: Open command
    send_command(
        {
            "method": "open",
            "params": {"targetID": TARGET_ID},
            "id": 9
        },
        "Format 9: open command"
    )
    time.sleep(2)

    # Format 10: With authentication in params
    send_command(
        {
            "method": "move.up",
            "params": {
                "targetID": TARGET_ID,
                "code": PIN
            },
            "id": 10
        },
        "Format 10: Move with PIN in params"
    )
    time.sleep(2)

    # Format 11: With key
    send_command(
        {
            "method": "move.up",
            "params": {
                "targetID": TARGET_ID,
                "key": KEY
            },
            "id": 11
        },
        "Format 11: Move with KEY in params"
    )
    time.sleep(2)

    # Format 12: Command with parameters array
    send_command(
        {
            "method": "executeCommand",
            "params": {
                "targetID": TARGET_ID,
                "command": "up",
                "parameters": []
            },
            "id": 12
        },
        "Format 12: executeCommand with parameters array"
    )
    time.sleep(2)

    # Format 13: RTS protocol specific
    send_command(
        {
            "method": "sendCommand",
            "params": {
                "targetID": TARGET_ID,
                "command": "my",  # my = stop/favorite position
                "protocol": "rts"
            },
            "id": 13
        },
        "Format 13: RTS protocol command (my)"
    )
    time.sleep(2)

    # Format 14: Auth then move in same message
    auth_and_move = (
        json.dumps({"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 14}) + "\n" +
        json.dumps({"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 15}) + "\n"
    )
    print("\nFormat 14: Auth + Move in single message")
    print(f"  Message: {auth_and_move.strip()}")

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
        ssl_sock.sendall(auth_and_move.encode())

        print("  Sent - waiting for motor...")
        time.sleep(5)

        # Stop
        stop_msg = json.dumps({"method": "move.stop", "params": {"targetID": TARGET_ID}, "id": 16}) + "\n"
        ssl_sock.sendall(stop_msg.encode())
        print("  Stop sent")

        ssl_sock.close()
    except Exception as e:
        print(f"  Error: {e}")

    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    test_all_formats()
    print("\nIf you saw the motor move with any format, that's the one to use!")
