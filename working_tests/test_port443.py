#!/usr/bin/env python3
"""
Test Somfy on port 443 with various TLS configurations.
"""

import socket
import json
import ssl
import time

HOST = "192.168.1.77"
PORT = 443
TARGET_ID = "160326"
PIN = "9679"

def test_tls_with_legacy():
    """Test port 443 with legacy SSL/TLS support"""
    print("="*60)
    print("Testing Port 443 with Legacy TLS Support")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        print(f"Connecting to {HOST}:{PORT}...")
        sock.connect((HOST, PORT))
        print("Connected!")

        # Create SSL context with legacy support
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')

        # Enable legacy renegotiation
        context.options |= 0x4  # OP_LEGACY_SERVER_CONNECT

        print("Wrapping with TLS (legacy enabled)...")
        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        print(f"TLS established!")
        print(f"  Version: {ssl_sock.version()}")
        print(f"  Cipher: {ssl_sock.cipher()}")

        # Send auth
        auth_msg = {
            "method": "security.auth",
            "params": {"targetID": TARGET_ID, "code": PIN},
            "id": 1
        }
        msg_str = json.dumps(auth_msg) + "\n"
        print(f"\nSending auth: {msg_str.strip()}")
        ssl_sock.sendall(msg_str.encode())

        try:
            response = ssl_sock.recv(4096).decode()
            print(f"Auth response: {response}")

            if response:
                # Try move
                time.sleep(0.5)
                move_msg = {
                    "method": "move.up",
                    "params": {"targetID": TARGET_ID},
                    "id": 2
                }
                msg_str = json.dumps(move_msg) + "\n"
                print(f"\nSending move: {msg_str.strip()}")
                ssl_sock.sendall(msg_str.encode())

                response = ssl_sock.recv(4096).decode()
                print(f"Move response: {response}")

        except socket.timeout:
            print("No response received (timeout)")

        ssl_sock.close()
        return True

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tls_sslv23():
    """Test with SSLv23 protocol"""
    print("\n" + "="*60)
    print("Testing Port 443 with SSLv23")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        print(f"Connecting to {HOST}:{PORT}...")
        sock.connect((HOST, PORT))
        print("Connected!")

        # Try SSLv23
        context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        print("Wrapping with SSLv23...")
        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        print(f"SSL established: {ssl_sock.version()}")

        # Send command
        msg = {"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 1}
        ssl_sock.sendall((json.dumps(msg) + "\n").encode())

        response = ssl_sock.recv(4096).decode()
        print(f"Response: {response}")

        ssl_sock.close()
        return True

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_tls_tlsv1():
    """Test with TLSv1.0"""
    print("\n" + "="*60)
    print("Testing Port 443 with TLSv1.0")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        print(f"Connecting to {HOST}:{PORT}...")
        sock.connect((HOST, PORT))
        print("Connected!")

        # Try TLSv1
        context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        print("Wrapping with TLSv1.0...")
        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        print(f"TLS established: {ssl_sock.version()}")

        # Send command
        msg = {"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 1}
        ssl_sock.sendall((json.dumps(msg) + "\n").encode())

        response = ssl_sock.recv(4096).decode()
        print(f"Response: {response}")

        ssl_sock.close()
        return True

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_openssl_direct():
    """Use OpenSSL command line to test"""
    print("\n" + "="*60)
    print("Testing with OpenSSL Command")
    print("="*60)

    import subprocess

    try:
        # Test what TLS versions are available
        cmd = [
            "openssl", "s_client",
            "-connect", f"{HOST}:{PORT}",
            "-brief",
            "-legacy_renegotiation"
        ]

        print(f"Running: {' '.join(cmd)}")

        # Create message
        msg = {"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 1}
        msg_str = json.dumps(msg) + "\n"

        result = subprocess.run(
            cmd,
            input=msg_str.encode(),
            capture_output=True,
            timeout=5
        )

        print("STDOUT:")
        print(result.stdout.decode())
        print("\nSTDERR:")
        print(result.stderr.decode())

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    print("Testing Somfy Port 443 with various TLS configurations\n")

    # Try OpenSSL first to see what's supported
    test_openssl_direct()

    # Try Python SSL
    test_tls_with_legacy()
    test_tls_sslv23()
    test_tls_tlsv1()
