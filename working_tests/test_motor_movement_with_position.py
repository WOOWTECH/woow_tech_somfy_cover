#!/usr/bin/env python3
"""
Test motor movement and track position updates in real-time.
This test will move the motor and poll position to see live updates.
"""

import socket
import json
import os
import time
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

# Device configuration
HOST = "192.168.1.77"
UDP_PORT = 55055
TARGET_ID = "160326"
KEY_BYTES = bytes.fromhex("FBE90399BA25B4B67DC1B23BE0D9C084")

BLOCK_SIZE = 16


def pad_zero(data: bytes) -> bytes:
    """Zero-padding."""
    padding_needed = -len(data) % BLOCK_SIZE
    return data + b"\0" * padding_needed


def unpad_zero(data: bytes) -> bytes:
    """Remove zero-padding."""
    return data.rstrip(b'\0')


def encrypt_command(method: str, params: dict = None, request_id: int = 1) -> bytes:
    """Encrypt command using zero-padding."""
    # Build JSON-RPC message
    message = {
        "method": method,
        "params": {"targetID": TARGET_ID},
        "id": request_id
    }

    # Add extra params if provided
    if params:
        message["params"].update(params)

    # Compact JSON
    json_str = json.dumps(message, separators=(",", ":"))
    payload = json_str.encode("utf-8")

    # Zero-padding
    payload = pad_zero(payload)

    # Random IV
    iv = os.urandom(BLOCK_SIZE)

    # Encrypt
    cipher = Cipher(algorithms.AES(KEY_BYTES), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(payload) + encryptor.finalize()

    return iv + ciphertext


def send_and_receive(method: str, params: dict = None, request_id: int = 1) -> dict | None:
    """Send command and return decrypted response."""
    try:
        encrypted = encrypt_command(method, params, request_id)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("", UDP_PORT))

        sock.sendto(encrypted, (HOST, UDP_PORT))

        # Receive response
        response, _ = sock.recvfrom(4096)
        sock.close()

        # Decrypt
        iv = response[:BLOCK_SIZE]
        ciphertext = response[BLOCK_SIZE:]

        cipher = Cipher(algorithms.AES(KEY_BYTES), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        padded = decryptor.update(ciphertext) + decryptor.finalize()

        plaintext = unpad_zero(padded)
        return json.loads(plaintext.decode("utf-8"))

    except socket.timeout:
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_position() -> dict | None:
    """Get current position."""
    response = send_and_receive("status.position")
    if response and "position" in response:
        return response["position"]
    return None


def poll_position_during_movement(duration: float, interval: float = 0.5):
    """Poll position repeatedly during movement."""
    print(f"\n  Polling position for {duration} seconds (every {interval}s)...")
    print("  " + "-" * 70)

    start_time = time.time()
    positions = []

    while (time.time() - start_time) < duration:
        pos = get_position()
        if pos:
            value = pos.get("value", "?")
            status = pos.get("status", "?")
            direction = pos.get("direction", "?")

            timestamp = time.time() - start_time
            positions.append((timestamp, value, status, direction))

            print(f"  [{timestamp:5.2f}s] Position: {value:6.3f}% | Status: {status:10s} | Direction: {direction}")
        else:
            print(f"  [{time.time() - start_time:5.2f}s] No response")

        time.sleep(interval)

    print("  " + "-" * 70)
    return positions


def test_movement_sequence():
    """Test motor movement with position tracking."""
    print("=" * 80)
    print("MOTOR MOVEMENT TEST WITH REAL-TIME POSITION TRACKING")
    print("=" * 80)

    # Get initial position
    print("\n[1] Getting initial position...")
    pos = get_position()
    if pos:
        print(f"    Initial position: {pos['value']}%")
        print(f"    Status: {pos['status']}")
        print(f"    Direction: {pos['direction']}")
        initial_pos = pos['value']
    else:
        print("    Failed to get initial position")
        return

    input("\nPress ENTER to move motor UP for 3 seconds...")

    # Move up
    print("\n[2] Sending move.up command...")
    response = send_and_receive("move.up", request_id=1)
    if response:
        print(f"    Response: {response.get('result', 'No result')}")

        # Poll position during movement
        positions = poll_position_during_movement(3.0, 0.3)

        # Stop
        print("\n[3] Sending stop command...")
        response = send_and_receive("move.stop", request_id=2)
        print(f"    Response: {response.get('result', 'No result')}")

        # Get final position
        time.sleep(0.5)
        pos = get_position()
        if pos:
            print(f"\n    Final position after UP: {pos['value']}%")
            print(f"    Change: {pos['value'] - initial_pos:+.3f}%")
    else:
        print("    Failed to send move.up")
        return

    time.sleep(2)

    input("\nPress ENTER to move motor DOWN for 3 seconds...")

    # Move down
    print("\n[4] Sending move.down command...")
    down_start_pos = pos['value']
    response = send_and_receive("move.down", request_id=3)
    if response:
        print(f"    Response: {response.get('result', 'No result')}")

        # Poll position during movement
        positions = poll_position_during_movement(3.0, 0.3)

        # Stop
        print("\n[5] Sending stop command...")
        response = send_and_receive("move.stop", request_id=4)
        print(f"    Response: {response.get('result', 'No result')}")

        # Get final position
        time.sleep(0.5)
        pos = get_position()
        if pos:
            print(f"\n    Final position after DOWN: {pos['value']}%")
            print(f"    Change: {pos['value'] - down_start_pos:+.3f}%")
    else:
        print("    Failed to send move.down")
        return

    # Test move.to position
    input("\nPress ENTER to test move.to command (move to 50%)...")

    print("\n[6] Sending move.to position=50...")
    response = send_and_receive("move.to", {"position": 50.0}, request_id=5)
    if response:
        print(f"    Response: {response.get('result', 'No result')}")

        # Poll position until it reaches 50 or stops
        print("\n  Polling position until motor stops...")
        print("  " + "-" * 70)

        prev_pos = None
        stable_count = 0

        for i in range(40):  # Max 20 seconds (40 * 0.5s)
            pos = get_position()
            if pos:
                value = pos.get("value", 0)
                status = pos.get("status", "?")

                print(f"  [{i*0.5:5.2f}s] Position: {value:6.3f}% | Status: {status:10s}")

                # Check if stopped
                if status == "stopped":
                    if prev_pos is not None and abs(value - prev_pos) < 0.01:
                        stable_count += 1
                        if stable_count >= 2:
                            print(f"\n  Motor stopped at position: {value}%")
                            break
                    else:
                        stable_count = 0
                else:
                    stable_count = 0

                prev_pos = value

            time.sleep(0.5)

        print("  " + "-" * 70)

    print("\n" + "=" * 80)
    print("MOVEMENT TEST COMPLETE")
    print("=" * 80)
    print("\nObservations:")
    print("  1. Did the motor physically move UP?")
    print("  2. Did the motor physically move DOWN?")
    print("  3. Did move.to work to position 50%?")
    print("  4. Did position values update in real-time?")
    print("  5. What was the update frequency?")
    print("=" * 80)


def main():
    """Run the test."""
    try:
        test_movement_sequence()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        # Try to stop motor
        print("Sending emergency stop...")
        try:
            send_and_receive("move.stop")
            print("Stop command sent")
        except:
            pass
    except Exception as e:
        print(f"\n\nFATAL ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
