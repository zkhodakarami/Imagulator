# test_flywheel.py
"""
Test script to debug Flywheel connection issues.
Run this from the command line to verify your credentials work.
"""

import sys
import os
from pathlib import Path

# Try to import flywheel
try:
    import flywheel

    # print(f"✓ flywheel SDK version: {flywheel.__version__}")
except ImportError as e:
    print(f"✗ Cannot import flywheel SDK: {e}")
    print("Install with: pip install flywheel-sdk")
    sys.exit(1)

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

FW_API_KEY = os.getenv("FW_API_KEY")

print("\n=== Configuration Check ===")
print(f"FW_API_KEY set: {'Yes' if FW_API_KEY else 'No'}")

if not FW_API_KEY:
    print("\n✗ FW_API_KEY not found in environment!")
    print("\nCreate a .env file with:")
    print("FW_API_KEY=upenn.flywheel.io:your_api_key_here")
    sys.exit(1)

if ":" not in FW_API_KEY:
    print(f"\n✗ FW_API_KEY format incorrect: '{FW_API_KEY}'")
    print("Expected format: upenn.flywheel.io:your_api_key_here")
    sys.exit(1)

host, key = FW_API_KEY.split(":", 1)
print(f"Host: {host}")
print(f"Key: {key[:10]}...{key[-4:]}")

# Test connection
print("\n=== Testing Connection ===")
try:
    print("Attempting to create Flywheel client...")
    fw = flywheel.Client(FW_API_KEY)
    print("✓ Client created successfully")

    # Test getting user info
    print("\nAttempting to get current user...")
    try:
        user = fw.get_current_user()
        print(f"✓ Connected as: {user.email if hasattr(user, 'email') else user.id}")
        print(f"  User ID: {user.id}")
        if hasattr(user, 'firstname'):
            print(f"  Name: {user.firstname} {user.lastname}")
    except Exception as e:
        print(f"✗ Cannot get user info: {e}")
        print(f"  Error type: {type(e).__name__}")

    # Test listing projects
    print("\n=== Testing Project Access ===")
    try:
        print("Fetching projects...")
        projects = fw.projects()
        print(f"✓ Found {len(projects)} projects")

        if projects:
            print("\nFirst 5 projects:")
            for i, p in enumerate(projects[:5], 1):
                label = getattr(p, 'label', 'N/A')
                pid = getattr(p, 'id', getattr(p, '_id', 'N/A'))
                print(f"  {i}. {label} (ID: {pid})")
        else:
            print("\n⚠ No projects found. This could mean:")
            print("  - Your account has no project access")
            print("  - You need to be added to projects by an admin")
    except Exception as e:
        print(f"✗ Cannot list projects: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback

        traceback.print_exc()

    # Test alternative methods
    print("\n=== Testing Alternative Methods ===")

    # Try projects.find()
    try:
        print("Trying projects.find()...")
        results = fw.projects.find()
        print(f"✓ find() returned {len(list(results))} projects")
    except Exception as e:
        print(f"✗ projects.find() failed: {e}")

    # Try projects.iter()
    try:
        print("Trying projects.iter()...")
        count = 0
        for p in fw.projects.iter():
            count += 1
            if count >= 5:
                break
        print(f"✓ iter() returned at least {count} projects")
    except Exception as e:
        print(f"✗ projects.iter() failed: {e}")

except Exception as e:
    print(f"✗ Failed to create Flywheel client: {e}")
    print(f"  Error type: {type(e).__name__}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("\n=== Summary ===")
print("If you see projects listed above, your connection works!")
print("If not, check:")
print("  1. API key is valid and not expired")
print("  2. You have permission to access projects")
print("  3. Network/firewall allows connection to upenn.flywheel.io")
print("  4. The Flywheel SDK version is compatible (try: pip install --upgrade flywheel-sdk)")