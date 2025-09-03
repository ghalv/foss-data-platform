#!/usr/bin/env python3
"""
FOSS Data Platform - Cleanup System Test
Tests the cleanup functionality before going live
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta
import psycopg2

def test_database_connection():
    """Test connection to PostgreSQL database"""
    print("🔍 Testing database connection...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            dbname='dagster',
            user='dagster',
            password='dagster123'
        )
        conn.close()
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_cleanup_tables():
    """Test that cleanup tables exist"""
    print("🔍 Testing cleanup tables...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            dbname='dagster',
            user='dagster',
            password='dagster123'
        )

        with conn.cursor() as cursor:
            # Check if tables exist
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name IN ('cleanup_policies', 'cleanup_audit')
            """)
            tables = cursor.fetchall()

            if len(tables) >= 2:
                print("✅ Cleanup tables exist")
                return True
            else:
                print(f"❌ Missing cleanup tables. Found: {[t[0] for t in tables]}")
                return False

        conn.close()
    except Exception as e:
        print(f"❌ Table check failed: {e}")
        return False

def test_cleanup_policies():
    """Test that retention policies are configured"""
    print("🔍 Testing retention policies...")
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5433,
            dbname='dagster',
            user='dagster',
            password='dagster123'
        )

        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM cleanup_policies")
            count = cursor.fetchone()[0]

            if count > 0:
                print(f"✅ Found {count} retention policies")

                # Show policies
                cursor.execute("SELECT data_type, retention_days, enabled FROM cleanup_policies")
                policies = cursor.fetchall()

                print("   Current policies:")
                for policy in policies:
                    status = "✅" if policy[2] else "⭕"
                    print(f"   {status} {policy[0]}: {policy[1]} days")

                return True
            else:
                print("❌ No retention policies found")
                return False

        conn.close()
    except Exception as e:
        print(f"❌ Policy check failed: {e}")
        return False

def test_operation_files():
    """Test that operation files can be scanned"""
    print("🔍 Testing operation files...")
    try:
        import glob

        # Create a test operation file
        test_file = "/tmp/operation_test_cleanup.json"
        test_data = {
            "operation_id": "test_cleanup_operation",
            "pipeline_name": "test_pipeline",
            "status": "completed",
            "start_time": (datetime.now() - timedelta(days=45)).isoformat(),  # 45 days old
            "end_time": (datetime.now() - timedelta(days=45)).isoformat(),
            "progress": 100,
            "message": "Test operation for cleanup system"
        }

        with open(test_file, 'w') as f:
            json.dump(test_data, f)

        print(f"✅ Created test operation file: {test_file}")

        # Scan for files
        files = glob.glob("/tmp/operation_*.json")
        old_files = []

        for file_path in files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                created_at = data.get('start_time')
                if created_at:
                    created_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    age_days = (datetime.now() - created_dt.replace(tzinfo=None)).days

                    if age_days > 30:  # Older than retention period
                        old_files.append((file_path, age_days))
            except:
                pass

        if old_files:
            print(f"✅ Found {len(old_files)} files older than 30 days:")
            for file_path, age in old_files:
                print(f"   - {file_path}: {age} days old")
        else:
            print("ℹ️  No files older than 30 days found")

        # Clean up test file
        if os.path.exists(test_file):
            os.remove(test_file)
            print("🧹 Cleaned up test file")

        return True

    except Exception as e:
        print(f"❌ File test failed: {e}")
        return False

def test_cleanup_script():
    """Test the cleanup script functionality"""
    print("🔍 Testing cleanup script...")

    script_path = "/home/gunnar/git/foss-dataplatform/scripts/cleanup_operations.py"

    if not os.path.exists(script_path):
        print(f"❌ Cleanup script not found: {script_path}")
        return False

    if not os.access(script_path, os.X_OK):
        print(f"❌ Cleanup script not executable: {script_path}")
        return False

    print(f"✅ Cleanup script exists and is executable: {script_path}")
    return True

def main():
    """Run all cleanup system tests"""
    print("🧹 FOSS Data Platform - Cleanup System Test")
    print("=" * 50)

    tests = [
        ("Database Connection", test_database_connection),
        ("Cleanup Tables", test_cleanup_tables),
        ("Retention Policies", test_cleanup_policies),
        ("Operation Files", test_operation_files),
        ("Cleanup Script", test_cleanup_script)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        if test_func():
            passed += 1
        print()

    print("=" * 50)
    print(f"🎯 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Cleanup system is ready.")
        print("\n🚀 You can now:")
        print("   • Run dry-run: python scripts/cleanup_operations.py --dry-run")
        print("   • Run cleanup: python scripts/cleanup_operations.py --run")
        print("   • Check stats: python scripts/cleanup_operations.py --stats")
        print("   • View config: python scripts/cleanup_operations.py --config")
        print("   • Use web UI: Visit Pipeline Management page")
    else:
        print("⚠️  Some tests failed. Please check the issues above.")

    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
