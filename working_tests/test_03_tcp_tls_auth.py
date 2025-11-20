#!/usr/bin/env python3
"""
Test 3: TCP over TLS with PIN Authentication
Port: 55056
"""

import socket
import ssl
import json

# Device configuration
HOST = "192.168.1.77"
PORT = 55056
PIN = "9679"

def tcp_tls_auth():
    print("=" * 60)
    print("TEST 3: TCP over TLS with PIN Authentication")
    print("=" * 60)

    try:
        # Create SSL context (ignore certificate verification for now)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)

        print(f"\nConnecting to {HOST}:{PORT}...")

        # Wrap socket with TLS
        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        ssl_sock.connect((HOST, PORT))

        print("✓ TLS connection established")

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
        print(auth_request)

        ssl_sock.send(request_str.encode('utf-8'))

        # Read response
        print("\nWaiting for response...")
        response_data = ssl_sock.recv(4096)
        print(f"\nResponse received:")
        print(response_data.decode('utf-8'))

        response = json.loads(response_data.decode('utf-8').strip())
        print(f"\nParsed response:")
        print(json.dumps(response, indent=2))

        if response.get("result"):
            print("\n✓ SUCCESS: Authenticated successfully")

            # Try to get motor info
            info_request = {
                "method": "status.info",
                "params": {},
                "id": 2
            }
            request_str = json.dumps(info_request) + "\n"
            print(f"\n\nSending info request:")
            print(info_request)

            ssl_sock.send(request_str.encode('utf-8'))

            response_data = ssl_sock.recv(4096)
            print(f"\nInfo response:")
            print(response_data.decode('utf-8'))

            return True
        else:
            print("\n✗ FAILED: Authentication failed")
            return False

    except socket.timeout:
        print("\n✗ TIMEOUT: Connection timed out")
        return False
    except ConnectionRefusedError:
        print("\n✗ CONNECTION REFUSED: Port may be closed or filtered")
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
    result = tcp_tls_auth()
    exit(0 if result else 1)
