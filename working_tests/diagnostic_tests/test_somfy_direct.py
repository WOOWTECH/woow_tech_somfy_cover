#!/usr/bin/env python3
"""
Direct Somfy PoE motor testing script.
Goal: Get ANY response and make the cover move.
"""

import socket
import json
import time
import ssl
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import binascii

# Device configuration
HOST = "192.168.1.77"
TARGET_ID = "160326"
PIN = "9679"
KEY = "FBE90399BA25B4B67DC1B23BE0D9C084"
TCP_PORT = 55056
UDP_PORT = 55055

def test_tcp_plain():
    """Test 1: TCP without TLS - plain JSON-RPC"""
    print("\n" + "="*60)
    print("TEST 1: TCP Plain (No TLS)")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        print(f"Connecting to {HOST}:{TCP_PORT}...")
        sock.connect((HOST, TCP_PORT))
        print("Connected!")

        # Try authentication
        auth_msg = {
            "method": "security.auth",
            "params": {"targetID": TARGET_ID, "code": PIN},
            "id": 1
        }
        msg_str = json.dumps(auth_msg) + "\n"
        print(f"Sending auth: {msg_str.strip()}")
        sock.sendall(msg_str.encode())

        response = sock.recv(4096).decode()
        print(f"Auth response: {response}")

        if response:
            # Try move command
            time.sleep(0.5)
            move_msg = {
                "method": "move.up",
                "params": {"targetID": TARGET_ID},
                "id": 2
            }
            msg_str = json.dumps(move_msg) + "\n"
            print(f"Sending move: {msg_str.strip()}")
            sock.sendall(msg_str.encode())

            response = sock.recv(4096).decode()
            print(f"Move response: {response}")

            return True

        sock.close()
        return False

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_tcp_plain_combined():
    """Test 2: TCP Plain - Auth and Move in one message"""
    print("\n" + "="*60)
    print("TEST 2: TCP Plain - Combined Auth+Move")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        print(f"Connecting to {HOST}:{TCP_PORT}...")
        sock.connect((HOST, TCP_PORT))
        print("Connected!")

        # Send both commands together
        auth_msg = {"method": "security.auth", "params": {"targetID": TARGET_ID, "code": PIN}, "id": 1}
        move_msg = {"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 2}

        combined = json.dumps(auth_msg) + "\n" + json.dumps(move_msg) + "\n"
        print(f"Sending combined: {combined}")
        sock.sendall(combined.encode())

        time.sleep(1)
        response = sock.recv(4096).decode()
        print(f"Response: {response}")

        sock.close()
        return bool(response)

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_udp_plain():
    """Test 3: UDP without encryption"""
    print("\n" + "="*60)
    print("TEST 3: UDP Plain (No Encryption)")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)

        # Try direct move command
        move_msg = {
            "method": "move.up",
            "params": {"targetID": TARGET_ID},
            "id": 1
        }
        msg_str = json.dumps(move_msg)
        print(f"Sending to UDP {HOST}:{UDP_PORT}: {msg_str}")
        sock.sendto(msg_str.encode(), (HOST, UDP_PORT))

        try:
            response, addr = sock.recvfrom(4096)
            print(f"Response from {addr}: {response}")
            return True
        except socket.timeout:
            print("No response (timeout)")
            return False

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_udp_with_auth():
    """Test 4: UDP with authentication message first"""
    print("\n" + "="*60)
    print("TEST 4: UDP with Auth Message First")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)

        # Send auth
        auth_msg = {
            "method": "security.auth",
            "params": {"targetID": TARGET_ID, "code": PIN},
            "id": 1
        }
        msg_str = json.dumps(auth_msg)
        print(f"Sending auth to UDP: {msg_str}")
        sock.sendto(msg_str.encode(), (HOST, UDP_PORT))

        try:
            response, addr = sock.recvfrom(4096)
            print(f"Auth response: {response}")
        except socket.timeout:
            print("No auth response (continuing anyway)")

        time.sleep(0.5)

        # Send move
        move_msg = {
            "method": "move.up",
            "params": {"targetID": TARGET_ID},
            "id": 2
        }
        msg_str = json.dumps(move_msg)
        print(f"Sending move to UDP: {msg_str}")
        sock.sendto(msg_str.encode(), (HOST, UDP_PORT))

        try:
            response, addr = sock.recvfrom(4096)
            print(f"Move response: {response}")
            return True
        except socket.timeout:
            print("No move response (timeout)")
            return False

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_tcp_with_raw_tls():
    """Test 5: TCP with TLS but ignore verification"""
    print("\n" + "="*60)
    print("TEST 5: TCP with TLS (No Verification)")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        print(f"Connecting to {HOST}:{TCP_PORT}...")
        sock.connect((HOST, TCP_PORT))

        # Wrap with TLS, ignore all verification
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.set_ciphers('DEFAULT:@SECLEVEL=0')

        print("Wrapping with TLS...")
        ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
        print(f"TLS established: {ssl_sock.version()}")

        # Try auth
        auth_msg = {
            "method": "security.auth",
            "params": {"targetID": TARGET_ID, "code": PIN},
            "id": 1
        }
        msg_str = json.dumps(auth_msg) + "\n"
        print(f"Sending: {msg_str.strip()}")
        ssl_sock.sendall(msg_str.encode())

        response = ssl_sock.recv(4096).decode()
        print(f"Response: {response}")

        if response:
            time.sleep(0.5)
            move_msg = {
                "method": "move.up",
                "params": {"targetID": TARGET_ID},
                "id": 2
            }
            msg_str = json.dumps(move_msg) + "\n"
            print(f"Sending move: {msg_str.strip()}")
            ssl_sock.sendall(msg_str.encode())

            response = ssl_sock.recv(4096).decode()
            print(f"Move response: {response}")
            return True

        ssl_sock.close()
        return False

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_udp_broadcast():
    """Test 6: UDP broadcast to discover device"""
    print("\n" + "="*60)
    print("TEST 6: UDP Broadcast Discovery")
    print("="*60)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(3)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        # Try discovery message
        discovery_msgs = [
            {"method": "discover", "id": 1},
            {"method": "security.getDeviceInfo", "id": 1},
            {"method": "ping", "id": 1},
        ]

        for msg in discovery_msgs:
            msg_str = json.dumps(msg)
            print(f"Broadcasting: {msg_str}")
            sock.sendto(msg_str.encode(), ("255.255.255.255", UDP_PORT))
            sock.sendto(msg_str.encode(), (HOST, UDP_PORT))

            try:
                response, addr = sock.recvfrom(4096)
                print(f"Response from {addr}: {response}")
                return True
            except socket.timeout:
                pass

        print("No broadcast responses")
        return False

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

def test_alternative_ports():
    """Test 7: Try alternative common ports"""
    print("\n" + "="*60)
    print("TEST 7: Alternative Ports")
    print("="*60)

    common_ports = [80, 443, 8080, 8443, 5000, 5001]

    for port in common_ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            print(f"Trying TCP port {port}...")
            sock.connect((HOST, port))
            print(f"  Connected to port {port}!")

            # Try sending a command
            msg = {"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 1}
            sock.sendall((json.dumps(msg) + "\n").encode())

            try:
                response = sock.recv(4096)
                print(f"  Response: {response}")
                sock.close()
                return True
            except socket.timeout:
                pass

            sock.close()
        except Exception as e:
            pass

    print("No alternative ports responded")
    return False

def test_simple_move_variants():
    """Test 8: Different command formats on UDP"""
    print("\n" + "="*60)
    print("TEST 8: Different Move Command Formats")
    print("="*60)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)

    variants = [
        {"method": "move.up", "params": {"targetID": TARGET_ID}, "id": 1},
        {"method": "moveUp", "params": {"targetID": TARGET_ID}, "id": 1},
        {"method": "up", "params": {"targetID": TARGET_ID}, "id": 1},
        {"method": "move", "params": {"targetID": TARGET_ID, "direction": "up"}, "id": 1},
        {"cmd": "up", "target": TARGET_ID},
        {"command": "up", "targetID": TARGET_ID},
    ]

    for i, msg in enumerate(variants, 1):
        msg_str = json.dumps(msg)
        print(f"\nVariant {i}: {msg_str}")
        sock.sendto(msg_str.encode(), (HOST, UDP_PORT))

        try:
            response, addr = sock.recvfrom(4096)
            print(f"  SUCCESS! Response: {response}")
            return True
        except socket.timeout:
            print("  No response")

    sock.close()
    return False

def main():
    print("="*60)
    print("SOMFY PoE MOTOR DIRECT TESTING")
    print(f"Target: {HOST}")
    print(f"Target ID: {TARGET_ID}")
    print(f"PIN: {PIN}")
    print("="*60)

    tests = [
        ("TCP Plain", test_tcp_plain),
        ("TCP Plain Combined", test_tcp_plain_combined),
        ("UDP Plain", test_udp_plain),
        ("UDP with Auth", test_udp_with_auth),
        ("TCP with TLS", test_tcp_with_raw_tls),
        ("UDP Broadcast", test_udp_broadcast),
        ("Alternative Ports", test_alternative_ports),
        ("Command Variants", test_simple_move_variants),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = "SUCCESS" if result else "FAILED"

            if result:
                print(f"\n{'!'*60}")
                print(f"SUCCESS: {test_name} got a response!")
                print(f"{'!'*60}")
                # Don't stop - keep testing to see what else works

        except Exception as e:
            results[test_name] = f"ERROR: {e}"
            print(f"\nUnexpected error in {test_name}: {e}")

        time.sleep(1)  # Brief pause between tests

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results.items():
        status = result if isinstance(result, str) else ("PASS" if result else "FAIL")
        print(f"{test_name:.<40} {status}")
    print("="*60)

if __name__ == "__main__":
    main()
