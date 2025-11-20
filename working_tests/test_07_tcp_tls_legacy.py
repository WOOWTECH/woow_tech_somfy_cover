#!/usr/bin/env python3
"""
Test 7: TCP over TLS with Legacy SSL Support
Port: 55056
Uses TLSv1.2 as discovered from curl
"""

import socket
import ssl
import json

# Device configuration
HOST = "192.168.1.77"
PORT = 55056
PIN = "9679"

def tcp_tls_legacy():
    print("=" * 60)
    print("TEST 7: TCP over TLS with Legacy SSL (TLSv1.2)")
    print("=" * 60)

    try:
        # Create SSL context with TLSv1.2
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Enable legacy renegotiation
        context.options |= 0x4  # SSL_OP_LEGACY_SERVER_CONNECT

        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        print(f"\nConnecting to {HOST}:{PORT}...")

        # Wrap socket with TLS
        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        ssl_sock.connect((HOST, PORT))

        print(f"✓ TLS connection established")
        print(f"  Protocol: {ssl_sock.version()}")
        print(f"  Cipher: {ssl_sock.cipher()}")

        # Try authentication
        auth_request = {
            "method": "security.auth",
            "params": {
                "code": PIN
            },
            "id": 1
        }

        request_str = json.dumps(auth_request) + "\n"
        print(f"\nSending authentication request:")
        print(json.dumps(auth_request, indent=2))

        ssl_sock.sendall(request_str.encode('utf-8'))

        # Read response
        print("\nWaiting for response...")
        response_data = b""
        while True:
            chunk = ssl_sock.recv(1024)
            if not chunk:
                break
            response_data += chunk
            if b'\n' in chunk or b'}' in chunk:
                break

        print(f"\nRaw response received ({len(response_data)} bytes):")
        print(response_data[:200])

        response_str = response_data.decode('utf-8').strip()
        print(f"\nResponse string:")
        print(response_str)

        response = json.loads(response_str)
        print(f"\nParsed response:")
        print(json.dumps(response, indent=2))

        if response.get("result"):
            print("\n✓ SUCCESS: Authenticated successfully!")

            # Try to move the motor
            move_request = {
                "method": "move.wink",
                "params": {},
                "id": 2
            }

            request_str = json.dumps(move_request) + "\n"
            print(f"\n\n{'='*60}")
            print("Sending WINK command to identify motor...")
            print(json.dumps(move_request, indent=2))

            ssl_sock.sendall(request_str.encode('utf-8'))

            response_data = b""
            while True:
                chunk = ssl_sock.recv(1024)
                if not chunk:
                    break
                response_data += chunk
                if b'\n' in chunk or b'}' in chunk:
                    break

            print(f"\nWink response:")
            print(response_data.decode('utf-8'))

            return True
        else:
            print("\n✗ FAILED: Authentication failed")
            if 'error' in response:
                print(f"Error: {response['error']}")
            return False

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            ssl_sock.close()
        except:
            pass

if __name__ == "__main__":
    result = tcp_tls_legacy()
    exit(0 if result else 1)
