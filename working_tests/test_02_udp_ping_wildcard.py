#!/usr/bin/env python3
"""
Test 2: UDP Ping with Wildcard (Unencrypted)
According to docs: Use '*' as a wildcard for targetID
Port: 55055
"""

import socket
import json
import time

# Device configuration
HOST = "192.168.1.77"
PORT = 55055

def udp_ping_wildcard():
    print("=" * 60)
    print("TEST 2: UDP PING WITH WILDCARD (Unencrypted)")
    print("=" * 60)

    # Create UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)

    try:
        # Prepare ping request with wildcard
        request = {
            "method": "status.ping",
            "params": {
                "targetID": "*"
            },
            "id": 0
        }

        request_str = json.dumps(request)
        print(f"\nRequest sent:")
        print(request_str)

        # Send request
        sock.sendto(request_str.encode('utf-8'), (HOST, PORT))
        print(f"\nSent to {HOST}:{PORT}")

        # Wait for response(s)
        print("\nWaiting for response(s)...")

        responses = []
        start_time = time.time()

        while time.time() - start_time < 2:  # Collect responses for 2 seconds
            try:
                sock.settimeout(0.5)
                data, addr = sock.recvfrom(1024)
                print(f"\nResponse received from {addr}:")
                print(data.decode('utf-8'))

                response = json.loads(data.decode('utf-8'))
                responses.append(response)
                print(f"\nParsed response:")
                print(json.dumps(response, indent=2))

            except socket.timeout:
                break

        if responses:
            print(f"\n✓ SUCCESS: Received {len(responses)} response(s)")
            for resp in responses:
                if 'targetID' in resp:
                    print(f"  - Motor found: {resp['targetID']}")
            return True
        else:
            print("\n✗ FAILED: No responses received")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        return False
    finally:
        sock.close()

if __name__ == "__main__":
    result = udp_ping_wildcard()
    exit(0 if result else 1)
