#!/usr/bin/env python3
"""
FOSS Data Platform - Pipeline Operations Cleanup Script

This script manages garbage collection for old pipeline operations, including:
- Cleaning up old operation JSON files from /tmp
- Removing old database records based on retention policies
- Providing configurable retention periods
- Safety features like dry-run mode and backups

Usage:
    python cleanup_operations.py --dry-run          # Show what would be cleaned
    python cleanup_operations.py --run              # Actually perform cleanup
    python cleanup_operations.py --type manual      # Manual cleanup with audit
    python cleanup_operations.py --stats            # Show cleanup statistics
    python cleanup_operations.py --config           # Show current retention policies
"""

import os
import sys
import json
import time
import psycopg2
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import glob
import shutil
from typing import Dict, List, Tuple, Optional

class PipelineCleanupManager:
    def __init__(self, db_config: Dict, dry_run: bool = True):
        self.db_config = db_config
        self.dry_run = dry_run
        self.backup_dir = Path("/tmp/cleanup_backups")
        self.operations_dir = Path("/tmp")
        self.stats = {
            'files_scanned': 0,
            'files_deleted': 0,
            'space_freed': 0,
            'errors': []
        }

        # Create backup directory if it doesn't exist
        if not self.dry_run:
            self.backup_dir.mkdir(exist_ok=True)

    def get_db_connection(self):
        """Establish database connection"""
        try:
            return psycopg2.connect(**self.db_config)
        except Exception as e:
            print(f"Database connection failed: {e}")
            return None

    def get_retention_policies(self) -> Dict[str, Dict]:
        """Get retention policies from database"""
        policies = {}
        conn = self.get_db_connection()
        if not conn:
            return policies

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT data_type, retention_days, enabled, description
                    FROM cleanup_policies
                    WHERE enabled = true
                """)
                for row in cursor.fetchall():
                    policies[row[0]] = {
                        'retention_days': row[1],
                        'enabled': row[2],
                        'description': row[3]
                    }
        except Exception as e:
            print(f"Error fetching retention policies: {e}")
        finally:
            conn.close()

        return policies

    def scan_operation_files(self) -> List[Dict]:
        """Scan for operation files in /tmp"""
        operations = []
        pattern = "/tmp/operation_*.json"

        for file_path in glob.glob(pattern):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)

                # Extract operation metadata
                operation = {
                    'file_path': file_path,
                    'file_size': os.path.getsize(file_path),
                    'created_at': data.get('start_time'),
                    'status': data.get('status', 'unknown'),
                    'pipeline_name': data.get('pipeline_name', 'unknown'),
                    'age_days': None
                }

                # Calculate age if we have creation time
                if operation['created_at']:
                    try:
                        created_dt = datetime.fromisoformat(operation['created_at'].replace('Z', '+00:00'))
                        operation['age_days'] = (datetime.now() - created_dt.replace(tzinfo=None)).days
                    except:
                        operation['age_days'] = 999  # Very old if can't parse

                operations.append(operation)
                self.stats['files_scanned'] += 1

            except Exception as e:
                self.stats['errors'].append(f"Error reading {file_path}: {e}")

        return operations

    def should_cleanup_file(self, operation: Dict, policies: Dict) -> Tuple[bool, str]:
        """Determine if a file should be cleaned up based on policies"""
        if not operation['age_days']:
            return False, "Unable to determine age"

        # Check pipeline operations policy
        if 'pipeline_operations' in policies:
            retention_days = policies['pipeline_operations']['retention_days']
            if operation['age_days'] > retention_days:
                return True, f"Older than {retention_days} days"

        # Special handling for failed operations (keep longer)
        if operation['status'] == 'failed' and 'failed_operations' in policies:
            retention_days = policies['failed_operations']['retention_days']
            if operation['age_days'] <= retention_days:
                return False, f"Failed operation within {retention_days} day retention"

        return False, "Within retention period"

    def create_backup(self, file_path: str) -> str:
        """Create backup of file before deletion"""
        if self.dry_run:
            return "DRY_RUN"

        backup_path = self.backup_dir / f"{Path(file_path).name}.backup"
        try:
            shutil.copy2(file_path, backup_path)
            return str(backup_path)
        except Exception as e:
            self.stats['errors'].append(f"Backup failed for {file_path}: {e}")
            return "BACKUP_FAILED"

    def cleanup_file(self, operation: Dict) -> bool:
        """Clean up a single operation file"""
        file_path = operation['file_path']

        if self.dry_run:
            print(f"WOULD DELETE: {file_path} ({operation['age_days']} days old)")
            return True

        # Create backup first
        backup_path = self.create_backup(file_path)
        if backup_path == "BACKUP_FAILED":
            return False

        try:
            # Delete the file
            os.remove(file_path)
            self.stats['files_deleted'] += 1
            self.stats['space_freed'] += operation['file_size']

            # Log to database
            self.log_cleanup_action(
                data_type='pipeline_operations',
                cleanup_type='automatic',
                records_deleted=1,
                space_freed=operation['file_size'],
                details=f"Cleaned {file_path}, backup: {backup_path}"
            )

            print(f"DELETED: {file_path} (backup: {backup_path})")
            return True

        except Exception as e:
            self.stats['errors'].append(f"Delete failed for {file_path}: {e}")
            return False

    def log_cleanup_action(self, data_type: str, cleanup_type: str, records_deleted: int,
                          space_freed: int, details: str = ""):
        """Log cleanup action to database"""
        if self.dry_run:
            return

        conn = self.get_db_connection()
        if not conn:
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO cleanup_audit
                    (data_type, cleanup_type, records_deleted, space_freed_bytes, executed_by)
                    VALUES (%s, %s, %s, %s, %s)
                """, (data_type, cleanup_type, records_deleted, space_freed, f"cleanup_script:{details}"))
                conn.commit()
        except Exception as e:
            print(f"Error logging cleanup action: {e}")
        finally:
            conn.close()

    def perform_cleanup(self, cleanup_type: str = 'automatic') -> Dict:
        """Main cleanup function"""
        print(f"Starting cleanup (type: {cleanup_type}, dry_run: {self.dry_run})")
        print("=" * 60)

        # Get retention policies
        policies = self.get_retention_policies()
        if not policies:
            print("No retention policies found. Using defaults.")
            policies = {
                'pipeline_operations': {'retention_days': 30, 'enabled': True, 'description': 'Default'}
            }

        print(f"Retention policies: {json.dumps(policies, indent=2)}")
        print()

        # Scan for operations
        operations = self.scan_operation_files()
        print(f"Found {len(operations)} operation files")

        # Analyze and cleanup
        for operation in operations:
            should_cleanup, reason = self.should_cleanup_file(operation, policies)

            if should_cleanup:
                success = self.cleanup_file(operation)
                if not success:
                    print(f"FAILED: {operation['file_path']} - {reason}")
            else:
                print(f"KEEP: {operation['file_path']} - {reason}")

        # Final stats
        print("\n" + "=" * 60)
        print("CLEANUP SUMMARY:")
        print(f"Files scanned: {self.stats['files_scanned']}")
        print(f"Files deleted: {self.stats['files_deleted']}")
        print(f"Space freed: {self.stats['space_freed']:,} bytes")
        if self.stats['errors']:
            print(f"Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors'][:5]:  # Show first 5 errors
                print(f"  - {error}")

        return self.stats

    def show_stats(self):
        """Show cleanup statistics"""
        conn = self.get_db_connection()
        if not conn:
            print("Cannot connect to database")
            return

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM get_cleanup_stats()")
                rows = cursor.fetchall()

                if not rows:
                    print("No cleanup statistics available")
                    return

                print("CLEANUP STATISTICS:")
                print("-" * 80)
                print("<10")
                for row in rows:
                    print("<10")
                print("-" * 80)

        except Exception as e:
            print(f"Error fetching stats: {e}")
        finally:
            conn.close()

    def show_config(self):
        """Show current retention policies"""
        policies = self.get_retention_policies()
        print("CURRENT RETENTION POLICIES:")
        print("=" * 40)
        for data_type, policy in policies.items():
            status = "ENABLED" if policy['enabled'] else "DISABLED"
            print(f"{data_type}:")
            print(f"  Retention: {policy['retention_days']} days")
            print(f"  Status: {status}")
            print(f"  Description: {policy.get('description', 'N/A')}")
            print()


def main():
    parser = argparse.ArgumentParser(description='Pipeline Operations Cleanup')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned without actually deleting')
    parser.add_argument('--run', action='store_true', help='Actually perform cleanup')
    parser.add_argument('--type', default='automatic', choices=['automatic', 'manual', 'emergency'],
                       help='Type of cleanup for audit logging')
    parser.add_argument('--stats', action='store_true', help='Show cleanup statistics')
    parser.add_argument('--config', action='store_true', help='Show current retention policies')
    parser.add_argument('--db-host', default='localhost', help='Database host')
    parser.add_argument('--db-port', type=int, default=5433, help='Database port')
    parser.add_argument('--db-name', default='dagster', help='Database name')
    parser.add_argument('--db-user', default='dagster', help='Database user')
    parser.add_argument('--db-password', default='dagster123', help='Database password')

    args = parser.parse_args()

    # Database configuration
    db_config = {
        'host': args.db_host,
        'port': args.db_port,
        'dbname': args.db_name,
        'user': args.db_user,
        'password': args.db_password
    }

    # Determine if this is a dry run
    dry_run = args.dry_run or not args.run

    # Create cleanup manager
    cleanup_manager = PipelineCleanupManager(db_config, dry_run)

    if args.stats:
        cleanup_manager.show_stats()
    elif args.config:
        cleanup_manager.show_config()
    else:
        # Perform cleanup
        stats = cleanup_manager.perform_cleanup(args.type)

        if dry_run:
            print("\nThis was a DRY RUN. Use --run to actually perform cleanup.")
        else:
            print("\nCleanup completed successfully!")


if __name__ == '__main__':
    main()
