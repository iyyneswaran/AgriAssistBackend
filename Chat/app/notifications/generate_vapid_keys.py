"""
VAPID Key Generator
====================
Run this script once to generate VAPID key pairs for Web Push notifications.
Add the output to your .env file.

Usage:
    python -m app.notifications.generate_vapid_keys
"""

from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization
import base64


def generate_keys():
    """Generate a new VAPID key pair and print for .env configuration."""
    vapid = Vapid()
    vapid.generate_keys()

    # Extract public key as uncompressed point (required by Web Push)
    raw_pub = vapid.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    # Extract private key (32 bytes)
    raw_priv = vapid.private_key.private_numbers().private_value.to_bytes(32, 'big')

    # Convert to URL-safe Base64 without padding
    pub_b64 = base64.urlsafe_b64encode(raw_pub).decode('utf-8').rstrip('=')
    priv_b64 = base64.urlsafe_b64encode(raw_priv).decode('utf-8').rstrip('=')

    print("\n" + "=" * 60)
    print("  VAPID Keys Generated — Add these to your .env file")
    print("=" * 60)
    print()
    print(f"VAPID_PUBLIC_KEY={pub_b64}")
    print(f"VAPID_PRIVATE_KEY={priv_b64}")
    print(f"VAPID_CONTACT_EMAIL=admin@agriassist.app")
    print()
    print("=" * 60)
    print("  IMPORTANT: Share ONLY the PUBLIC key with the frontend.")
    print("  Keep the PRIVATE key secret.")
    print("=" * 60)
    print()

    return {
        "public_key": pub_b64,
        "private_key": priv_b64,
    }


if __name__ == "__main__":
    generate_keys()
