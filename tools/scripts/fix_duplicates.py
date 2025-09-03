#!/usr/bin/env python3
"""
Automatic Duplicate Code Fixer

This script automatically identifies and fixes duplicate code issues
in the FOSS Data Platform codebase.
"""

import os
import re
import difflib
from typing import Dict, List, Tuple


class DuplicateCodeFixer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.fixed_functions = []

    def fix_duplicates(self) -> Dict[str, int]:
        """Fix duplicate code issues automatically."""
        stats = {
            'functions_removed': 0,
            'files_modified': 0,
            'lines_saved': 0
        }

        # Fix the specific duplicates we identified
        duplicates_to_fix = [
            '_get_openai_client',
            '_resolve_ckan_parking_json_url',
            'get_pipeline_status',
            'read_recent_events',
            'write_event'
        ]

        for func_name in duplicates_to_fix:
            if self._fix_duplicate_function(func_name):
                stats['functions_removed'] += 1
                print(f"✅ Removed duplicate: {func_name}")

        # Update stats
        stats['files_modified'] = len(set(f[0] for f in self.fixed_functions))

        return stats

    def _fix_duplicate_function(self, func_name: str) -> bool:
        """Fix a specific duplicate function."""
        # Read the file
        filepath = os.path.join(self.root_dir, 'dashboard', 'app.py')

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return False

        lines = content.split('\n')

        # Find all occurrences of the function
        function_starts = []
        for i, line in enumerate(lines):
            if re.match(rf'^\s*def\s+{re.escape(func_name)}\s*\(', line):
                function_starts.append(i)

        if len(function_starts) < 2:
            return False  # Not a duplicate

        # Keep the first occurrence, remove subsequent ones
        functions_to_remove = function_starts[1:]

        # Remove functions in reverse order to maintain line numbers
        lines_to_remove = []
        for start_line in reversed(functions_to_remove):
            end_line = self._find_function_end(lines, start_line)
            if end_line > start_line:
                lines_to_remove.extend(range(start_line, end_line + 1))

        # Remove the lines
        new_lines = [line for i, line in enumerate(lines) if i not in lines_to_remove]

        # Write back the file
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('\n'.join(new_lines))

            lines_removed = len(lines_to_remove)
            self.fixed_functions.append((filepath, func_name, lines_removed))

            return True

        except Exception as e:
            print(f"❌ Error writing file: {e}")
            return False

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

    def create_shared_utilities(self) -> None:
        """Create shared utility modules for common patterns."""
        utils_dir = os.path.join(self.root_dir, 'dashboard', 'utils')
        os.makedirs(utils_dir, exist_ok=True)

        # Create error handling utilities
        error_utils = '''"""Shared error handling utilities."""

from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


def handle_api_error(error: Exception, context: str = "") -> Dict[str, Any]:
    """Standardized API error handling."""
    logger.error(f"API Error in {context}: {error}")
    return {
        "success": False,
        "error": str(error),
        "context": context
    }


def handle_database_error(error: Exception, query: str = "") -> Dict[str, Any]:
    """Standardized database error handling."""
    logger.error(f"Database Error: {error}")
    if query:
        logger.error(f"Query: {query[:100]}...")
    return {
        "success": False,
        "error": "Database operation failed",
        "type": "database_error"
    }


def validate_required_fields(data: Dict, required_fields: List[str]) -> List[str]:
    """Validate that required fields are present and not empty."""
    missing = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing.append(field)
    return missing
'''

        # Create API utilities
        api_utils = '''"""Shared API utilities."""

from typing import Dict, Any, Optional
import requests
import time


def make_api_request(url: str, method: str = 'GET', data: Optional[Dict] = None,
                    timeout: int = 30, retries: int = 3) -> Dict[str, Any]:
    """Make a standardized API request with retry logic."""
    for attempt in range(retries):
        try:
            if method.upper() == 'GET':
                response = requests.get(url, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, timeout=timeout)
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}

            if response.status_code == 200:
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": f"HTTP {response.status_code}"}

        except requests.exceptions.Timeout:
            if attempt == retries - 1:
                return {"success": False, "error": "Request timeout"}
            time.sleep(2 ** attempt)  # Exponential backoff

        except Exception as e:
            return {"success": False, "error": str(e)}

    return {"success": False, "error": "Max retries exceeded"}


def format_api_response(success: bool, data: Any = None, error: str = "") -> Dict[str, Any]:
    """Standardize API response format."""
    if success:
        return {"success": True, "data": data}
    else:
        return {"success": False, "error": error}
'''

        # Write the utility files
        with open(os.path.join(utils_dir, 'error_handlers.py'), 'w') as f:
            f.write(error_utils)

        with open(os.path.join(utils_dir, 'api_utils.py'), 'w') as f:
            f.write(api_utils)

        print("✅ Created shared utility modules")
        print("   - dashboard/utils/error_handlers.py")
        print("   - dashboard/utils/api_utils.py")


def main():
    """Main entry point for the duplicate code fixer."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fix_duplicates.py <directory>")
        print("This will automatically fix duplicate code issues.")
        sys.exit(1)

    root_dir = sys.argv[1]

    print("🔧 Duplicate Code Fixer")
    print("=" * 40)
    print(f"Target directory: {root_dir}")
    print("This will remove duplicate functions and create shared utilities.")
    print()

    # Ask for confirmation
    response = input("Continue? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("Operation cancelled.")
        sys.exit(0)

    fixer = DuplicateCodeFixer(root_dir)

    # Fix duplicates
    stats = fixer.fix_duplicates()

    # Create shared utilities
    fixer.create_shared_utilities()

    print("\n📊 Summary:")
    print(f"   Functions removed: {stats['functions_removed']}")
    print(f"   Files modified: {stats['files_modified']}")
    print(f"   Lines saved: {stats['lines_saved']}")

    if stats['functions_removed'] > 0:
        print("\n✅ Duplicate code cleanup completed!")
        print("   Review the changes and test functionality before committing.")
    else:
        print("\n✅ No duplicate functions found to remove.")


if __name__ == '__main__':
    main()
