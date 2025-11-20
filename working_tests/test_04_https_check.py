#!/usr/bin/env python3
"""
Test 4: Check HTTPS Web Interface
Port: 443 (standard HTTPS)
"""

import urllib.request
import urllib.error
import ssl

# Device configuration
HOST = "192.168.1.77"

def check_https():
    print("=" * 60)
    print("TEST 4: Check HTTPS Web Interface")
    print("=" * 60)

    # Create SSL context that ignores certificate errors
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    urls_to_try = [
        f"https://{HOST}",
        f"https://{HOST}/",
        f"http://{HOST}",
        f"http://{HOST}:80",
    ]

    for url in urls_to_try:
        try:
            print(f"\nTrying: {url}")
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, context=context, timeout=5) as response:
                status = response.status
                content_type = response.headers.get('Content-Type', 'unknown')
                print(f"✓ SUCCESS: Status {status}, Content-Type: {content_type}")

                # Read first 500 bytes
                data = response.read(500)
                print(f"\nFirst 500 bytes of response:")
                print(data.decode('utf-8', errors='ignore'))
                return True

        except urllib.error.HTTPError as e:
            print(f"  HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            print(f"  URL Error: {e.reason}")
        except Exception as e:
            print(f"  Error: {e}")

    print("\n✗ FAILED: Could not connect to web interface")
    return False

if __name__ == "__main__":
    result = check_https()
    exit(0 if result else 1)
