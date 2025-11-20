#!/usr/bin/env python3
"""
Test 1: UDP Ping (Unencrypted)
According to docs: Ping commands don't require encryption
Port: 55055
"""

import socket
import json
import time

# Device configuration
HOST = "192.168.1.77"
PORT = 55055
TARGET_ID = "160326"

def udp_ping():
    print("=" * 60)
    print("TEST 1: UDP PING (Unencrypted)")
    print("=" * 60)

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        # Prepare ping request
        request = {
            "method": "status.ping",
            "params": {
                "targetID": TARGET_ID
            },
            "id": 1
        }

        request_str = json.dumps(request)
        print(f"\nRequest sent:")
        print(request_str)

        # Send request
        sock.sendto(request_str.encode('utf-8'), (HOST, PORT))
        print(f"\nSent to {HOST}:{PORT}")

        # Wait for response
        print("\nWaiting for response...")
        data, addr = sock.recvfrom(1024)

        print(f"\nResponse received from {addr}:")
        print(data.decode('utf-8'))

        # Parse response
        response = json.loads(data.decode('utf-8'))
        print(f"\nParsed response:")
        print(json.dumps(response, indent=2))

        if response.get("result"):
            print("\n✓ SUCCESS: Motor responded to ping")
            return True
        else:
            print("\n✗ FAILED: Motor returned false")
            return False

    except socket.timeout:
        print("\n✗ TIMEOUT: No response received")
        return False
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    result = udp_ping()
    exit(0 if result else 1)
