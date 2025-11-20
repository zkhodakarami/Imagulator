#!/usr/bin/env python3
"""
Diagnostic and Fix Script for Empty Image URLs
Run this script to check and fix storage_path issues in your database
"""

import sqlite3
import os
from pathlib import Path

# ===== CONFIGURATION =====
DATABASE_PATH = "database/identifier.sqlite"  # Update this to your database path
IMAGE_BASE_DIR = "database/Images/uploaded"  # Update this to your images directory


# =========================

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def diagnose_database():
    """Check the current state of the database"""
    print("=" * 60)
    print("DIAGNOSTIC REPORT")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor()

    # Total images
    cursor.execute("SELECT COUNT(*) as count FROM image")
    total = cursor.fetchone()["count"]
    print(f"\nTotal images in database: {total}")

    # Images with empty paths
    cursor.execute("""
                   SELECT COUNT(*) as count
                   FROM image
                   WHERE storage_path IS NULL OR storage_path = ''
                   """)
    empty = cursor.fetchone()["count"]
    print(f"Images with empty storage_path: {empty}")
    print(f"Images with valid storage_path: {total - empty}")

    if empty > 0:
        print(f"\n⚠️  WARNING: {empty} images have no storage path!")
        print("These images will show as '#' in your HTML links.")
    else:
        print("\n✅ All images have storage paths set.")

    # Show sample of images with paths
    print("\n" + "-" * 60)
    print("SAMPLE IMAGES:")
    print("-" * 60)
    cursor.execute("""
                   SELECT i.id,
                          p.patient_code,
                          i.image_name,
                          i.storage_path,
                          CASE
                              WHEN i.storage_path IS NULL THEN '❌ NULL'
                              WHEN i.storage_path = '' THEN '❌ EMPTY'
                              ELSE '✅ OK'
                              END as status
                   FROM image i
                            LEFT JOIN patient p ON p.id = i.patient_id
                   ORDER BY i.id LIMIT 10
                   """)

    for row in cursor.fetchall():
        print(f"\nImage ID: {row['id']}")
        print(f"  Patient: {row['patient_code']}")
        print(f"  Name: {row['image_name']}")
        print(f"  Path: {row['storage_path']}")
        print(f"  Status: {row['status']}")

    conn.close()
    print("\n" + "=" * 60)


def check_file_system():
    """Check what image files actually exist on disk"""
    print("\n" + "=" * 60)
    print("FILE SYSTEM CHECK")
    print("=" * 60)

    if not os.path.exists(IMAGE_BASE_DIR):
        print(f"\n❌ ERROR: Directory '{IMAGE_BASE_DIR}' does not exist!")
        print("Please update IMAGE_BASE_DIR in this script.")
        return

    print(f"\nScanning directory: {IMAGE_BASE_DIR}")

    # Find all .nii and .nii.gz files
    nifti_files = []
    for ext in ['*.nii', '*.nii.gz']:
        nifti_files.extend(Path(IMAGE_BASE_DIR).rglob(ext))

    print(f"Found {len(nifti_files)} NIfTI files on disk:")
    for f in sorted(nifti_files)[:20]:  # Show first 20
        print(f"  {f}")

    if len(nifti_files) > 20:
        print(f"  ... and {len(nifti_files) - 20} more")

    print("\n" + "=" * 60)


def propose_fix():
    """Analyze the database and file system to propose a fix"""
    print("\n" + "=" * 60)
    print("PROPOSED FIXES")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor()

    # Get images with empty paths
    cursor.execute("""
                   SELECT i.id,
                          i.image_name,
                          p.patient_code,
                          i.patient_id
                   FROM image i
                            JOIN patient p ON p.id = i.patient_id
                   WHERE i.storage_path IS NULL
                      OR i.storage_path = ''
                   """)

    empty_images = cursor.fetchall()

    if not empty_images:
        print("\n✅ No fixes needed - all images have paths!")
        conn.close()
        return

    print(f"\nFound {len(empty_images)} images needing paths.")
    print("\nProposed updates:")

    fixes = []
    for row in empty_images:
        # Try different path patterns
        patterns = [
            f"{IMAGE_BASE_DIR}/{row['patient_code']}/{row['image_name']}",
            f"{IMAGE_BASE_DIR}/{row['image_name']}",
            f"{IMAGE_BASE_DIR}/patient_{row['patient_id']}/{row['image_name']}",
        ]

        # Check which pattern exists
        found_path = None
        for pattern in patterns:
            if os.path.exists(pattern):
                found_path = pattern
                break

        if found_path:
            fixes.append({
                'id': row['id'],
                'patient_code': row['patient_code'],
                'image_name': row['image_name'],
                'new_path': found_path,
                'status': '✅ FILE EXISTS'
            })
        else:
            # Guess the most likely path
            likely_path = patterns[0]
            fixes.append({
                'id': row['id'],
                'patient_code': row['patient_code'],
                'image_name': row['image_name'],
                'new_path': likely_path,
                'status': '⚠️  FILE NOT FOUND'
            })

    for fix in fixes[:10]:  # Show first 10
        print(f"\nImage ID {fix['id']} ({fix['patient_code']})")
        print(f"  Name: {fix['image_name']}")
        print(f"  New path: {fix['new_path']}")
        print(f"  {fix['status']}")

    if len(fixes) > 10:
        print(f"\n... and {len(fixes) - 10} more")

    conn.close()
    return fixes


def apply_fix(fixes, dry_run=True):
    """Apply the fixes to the database"""
    if not fixes:
        print("\n✅ No fixes to apply!")
        return

    conn = get_connection()
    cursor = conn.cursor()

    if dry_run:
        print("\n" + "=" * 60)
        print("DRY RUN - No changes will be made")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("APPLYING FIXES")
        print("=" * 60)

    updated = 0
    not_found = 0

    for fix in fixes:
        if dry_run:
            print(f"Would update image {fix['id']}: {fix['new_path']}")
        else:
            cursor.execute(
                "UPDATE image SET storage_path = ? WHERE id = ?",
                (fix['new_path'], fix['id'])
            )
            updated += 1

        if fix['status'] == '⚠️  FILE NOT FOUND':
            not_found += 1

    if not dry_run:
        conn.commit()
        print(f"\n✅ Updated {updated} images in database")
    else:
        print(f"\n📝 Would update {len(fixes)} images")

    if not_found > 0:
        print(f"⚠️  WARNING: {not_found} files not found on disk")
        print("   These paths were set anyway - check your file system!")

    conn.close()


def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print("IMAGE URL DIAGNOSTIC AND FIX TOOL")
    print("=" * 60)

    if not os.path.exists(DATABASE_PATH):
        print(f"\n❌ ERROR: Database not found at: {DATABASE_PATH}")
        print("Please update DATABASE_PATH in this script.")
        return

    # Step 1: Diagnose
    diagnose_database()

    # Step 2: Check file system
    check_file_system()

    # Step 3: Propose fixes
    fixes = propose_fix()

    if fixes:
        # Step 4: Ask to apply
        print("\n" + "=" * 60)
        response = input("\nApply fixes to database? (yes/no/dry-run): ").lower().strip()

        if response in ['yes', 'y']:
            apply_fix(fixes, dry_run=False)
            print("\n✅ Database updated! Restart your FastAPI server and test.")
        elif response in ['dry-run', 'dry', 'd']:
            apply_fix(fixes, dry_run=True)
        else:
            print("\n❌ No changes made.")

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()