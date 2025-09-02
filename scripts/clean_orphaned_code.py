#!/usr/bin/env python3
"""
Automated Orphaned Code Cleaner

This script automatically identifies and removes orphaned code blocks
from Python files in the FOSS Data Platform.
"""

import os
import re
import ast
import sys
from typing import List, Dict, Tuple


class OrphanedCodeCleaner:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.fixed_files = []

    def clean_file(self, filepath: str) -> bool:
        """Clean orphaned code from a single file. Returns True if file was modified."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                original_content = f.read()

            cleaned_content = self._clean_content(original_content, filepath)

            if cleaned_content != original_content:
                # Create backup
                backup_path = f"{filepath}.backup"
                with open(backup_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)

                # Write cleaned content
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(cleaned_content)

                self.fixed_files.append(filepath)
                print(f"✅ Cleaned: {filepath} (backup: {backup_path})")
                return True

        except Exception as e:
            print(f"❌ Error cleaning {filepath}: {e}")

        return False

    def _clean_content(self, content: str, filepath: str) -> str:
        """Clean orphaned code from content."""
        lines = content.split('\n')
        cleaned_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]
            cleaned_lines.append(line)

            # Look for function definitions
            if re.match(r'^\s*def\s+\w+\s*\(', line):
                func_name = re.match(r'^\s*def\s+(\w+)\s*\(', line).group(1)

                # Check if this function is a duplicate
                duplicate_found = False
                for j in range(len(cleaned_lines) - 1):
                    if re.match(rf'^\s*def\s+{re.escape(func_name)}\s*\(', cleaned_lines[j]):
                        duplicate_found = True
                        break

                if duplicate_found:
                    # Find the end of this duplicate function
                    func_end = self._find_function_end(lines, i)
                    if func_end > i:
                        print(f"  🗑️  Removed duplicate function '{func_name}' (lines {i+1}-{func_end+1})")
                        i = func_end + 1
                        continue

            i += 1

        return '\n'.join(cleaned_lines)

    def _find_function_end(self, lines: List[str], start_idx: int) -> int:
        """Find the end of a function definition."""
        indent_level = len(lines[start_idx]) - len(lines[start_idx].lstrip())

        for i in range(start_idx + 1, len(lines)):
            line = lines[i]
            if line.strip() == '':
                continue

            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent_level and line.strip() and not line.startswith(' ' * (indent_level + 1)):
                return i - 1

        return len(lines) - 1

    def scan_and_clean(self, exclude_patterns: List[str] = None) -> Dict:
        """Scan directory and clean orphaned code."""
        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', '.git', 'node_modules', '.venv', 'env']

        stats = {
            'scanned_files': 0,
            'cleaned_files': 0,
            'errors': 0
        }

        print("🔍 Scanning for orphaned code...")

        for root, dirs, files in os.walk(self.root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    stats['scanned_files'] += 1

                    try:
                        if self.clean_file(filepath):
                            stats['cleaned_files'] += 1
                    except Exception as e:
                        print(f"❌ Error processing {filepath}: {e}")
                        stats['errors'] += 1

        return stats


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python clean_orphaned_code.py <directory>")
        print("This will scan and clean orphaned code from Python files.")
        print("Backups will be created with .backup extension.")
        sys.exit(1)

    root_dir = sys.argv[1]

    print("🧹 Orphaned Code Cleaner")
    print("=" * 40)
    print(f"Target directory: {root_dir}")
    print("This will create backups and remove orphaned code.")
    print()

    # Ask for confirmation
    response = input("Continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)

    cleaner = OrphanedCodeCleaner(root_dir)
    stats = cleaner.scan_and_clean()

    print("\n📊 Summary:")
    print(f"   Files scanned: {stats['scanned_files']}")
    print(f"   Files cleaned: {stats['cleaned_files']}")
    print(f"   Errors: {stats['errors']}")

    if stats['cleaned_files'] > 0:
        print("
✅ Cleanup complete! Review the .backup files before committing."
    else:
        print("\n✅ No orphaned code found.")


if __name__ == '__main__':
    main()
