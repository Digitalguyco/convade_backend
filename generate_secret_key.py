#!/usr/bin/env python3
"""
Generate a secure secret key for Django production deployment.
"""
import secrets
import string

def generate_secret_key(length=50):
    """Generate a cryptographically secure secret key."""
    alphabet = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(alphabet) for _ in range(length))

if __name__ == "__main__":
    secret_key = generate_secret_key()
    print("🔐 Generated Secret Key for Django:")
    print(f"SECRET_KEY={secret_key}")
    print("\n💡 Copy this to your environment variables!")
    print("⚠️  Keep this secret and never commit it to version control!") 