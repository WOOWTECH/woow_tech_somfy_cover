#!/usr/bin/env python3
"""
Test 6: Port Scanner
Check which ports are open on the motor
"""

import socket

HOST = "192.168.1.77"
PORTS_TO_CHECK = [80, 443, 5683, 55055, 55056, 8080, 8443]

def check_port(host, port, timeout=2):
    """Check if a port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def scan_ports():
    print("=" * 60)
    print("TEST 6: Port Scanner")
    print("=" * 60)
    print(f"\nScanning {HOST}...")
    print()

    open_ports = []

    for port in PORTS_TO_CHECK:
        print(f"Port {port:5d}: ", end='', flush=True)
        if check_port(HOST, port):
            print("✓ OPEN")
            open_ports.append(port)
        else:
            print("✗ CLOSED/FILTERED")

    print(f"\n\nSummary: {len(open_ports)} open port(s)")
    for port in open_ports:
        print(f"  - {port}")

    return len(open_ports) > 0

if __name__ == "__main__":
    result = scan_ports()
    exit(0 if result else 1)
