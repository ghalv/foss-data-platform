#!/usr/bin/env python3
"""
Code Quality and Orphaned Code Detection Script

This script helps identify orphaned code, duplicate functions,
and other code quality issues in the FOSS Data Platform.
"""

import os
import re
import ast
import sys
from collections import defaultdict
from typing import Dict, List, Set, Tuple


class CodeQualityAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.issues = []

    def analyze_file(self, filepath: str) -> List[Dict]:
        """Analyze a single Python file for code quality issues."""
        issues = []

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for orphaned code patterns
            issues.extend(self._check_orphaned_code(content, filepath))
            issues.extend(self._check_duplicate_functions(content, filepath))
            issues.extend(self._check_unused_imports(content, filepath))
            issues.extend(self._check_long_functions(content, filepath))

        except Exception as e:
            issues.append({
                'type': 'error',
                'file': filepath,
                'message': f'Could not analyze file: {e}',
                'severity': 'error'
            })

        return issues

    def _check_orphaned_code(self, content: str, filepath: str) -> List[Dict]:
        """Check for orphaned code patterns."""
        issues = []

        lines = content.split('\n')

        # Check for orphaned try blocks
        try_count = content.count('try:')
        except_count = content.count('except') + content.count('finally:')
        if try_count > except_count:
            issues.append({
                'type': 'orphaned_code',
                'file': filepath,
                'message': f'Potential orphaned try block: {try_count} try, {except_count} except/finally',
                'severity': 'warning'
            })

        # Check for orphaned if blocks (basic heuristic)
        if_lines = [i for i, line in enumerate(lines) if line.strip().startswith('if ') and not line.strip().endswith(':')]
        for line_num in if_lines:
            # Check if next non-empty line is indented (indicating proper block)
            next_line_num = line_num + 1
            while next_line_num < len(lines):
                next_line = lines[next_line_num].strip()
                if next_line:  # Non-empty line
                    if not next_line.startswith(' ') and not next_line.startswith('\t'):
                        # Next line is not indented - potential orphaned if
                        issues.append({
                            'type': 'orphaned_code',
                            'file': filepath,
                            'line': line_num + 1,
                            'message': f'Potential orphaned if statement at line {line_num + 1}',
                            'severity': 'warning'
                        })
                    break
                next_line_num += 1

        # Check for TODO/FIXME comments that might indicate incomplete code
        for i, line in enumerate(lines):
            if 'TODO' in line.upper() or 'FIXME' in line.upper():
                issues.append({
                    'type': 'incomplete_code',
                    'file': filepath,
                    'line': i + 1,
                    'message': f'Incomplete code marker: {line.strip()}',
                    'severity': 'info'
                })

        return issues

    def _check_duplicate_functions(self, content: str, filepath: str) -> List[Dict]:
        """Check for duplicate function definitions."""
        issues = []
        function_names = []

        # Extract function names
        for line in content.split('\n'):
            match = re.match(r'^\s*def\s+(\w+)\s*\(', line)
            if match:
                func_name = match.group(1)
                if func_name in function_names:
                    issues.append({
                        'type': 'duplicate_function',
                        'file': filepath,
                        'message': f'Duplicate function definition: {func_name}',
                        'severity': 'error'
                    })
                function_names.append(func_name)

        return issues

    def _check_unused_imports(self, content: str, filepath: str) -> List[Dict]:
        """Check for potentially unused imports (basic heuristic)."""
        issues = []

        try:
            tree = ast.parse(content)

            # Get all imported names
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.asname or alias.name)
                elif isinstance(node, ast.ImportFrom):
                    for alias in node.names:
                        imports.add(alias.asname or alias.name)

            # Check if imports are used (basic check)
            content_no_comments = re.sub(r'#.*$', '', content, flags=re.MULTILINE)
            unused_imports = []

            for imp in imports:
                if imp and not re.search(r'\b' + re.escape(imp) + r'\b', content_no_comments):
                    unused_imports.append(imp)

            if unused_imports:
                issues.append({
                    'type': 'unused_imports',
                    'file': filepath,
                    'message': f'Potentially unused imports: {", ".join(unused_imports[:5])}',
                    'severity': 'info'
                })

        except SyntaxError:
            pass  # Skip files with syntax errors

        return issues

    def _check_long_functions(self, content: str, filepath: str) -> List[Dict]:
        """Check for functions that are too long (maintainability issue)."""
        issues = []

        lines = content.split('\n')
        current_function = None
        function_start = 0

        for i, line in enumerate(lines):
            # Check for function definition
            match = re.match(r'^\s*def\s+(\w+)\s*\(', line)
            if match:
                if current_function and (i - function_start) > 50:  # More than 50 lines
                    issues.append({
                        'type': 'long_function',
                        'file': filepath,
                        'line': function_start + 1,
                        'message': f'Function {current_function} is too long ({i - function_start} lines). Consider breaking it down.',
                        'severity': 'warning'
                    })

                current_function = match.group(1)
                function_start = i

        return issues

    def scan_directory(self, exclude_patterns: List[str] = None) -> List[Dict]:
        """Scan entire directory for code quality issues."""
        if exclude_patterns is None:
            exclude_patterns = ['__pycache__', '.git', 'node_modules', '.venv', 'env']

        all_issues = []

        for root, dirs, files in os.walk(self.root_dir):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    issues = self.analyze_file(filepath)
                    all_issues.extend(issues)

        return all_issues

    def generate_report(self, issues: List[Dict], output_file: str = None):
        """Generate a comprehensive report of code quality issues."""
        # Group issues by type and severity
        issue_counts = defaultdict(lambda: defaultdict(int))
        issues_by_file = defaultdict(list)

        for issue in issues:
            issue_type = issue['type']
            severity = issue.get('severity', 'info')
            issue_counts[issue_type][severity] += 1
            issues_by_file[issue['file']].append(issue)

        report = []
        report.append("# Code Quality Report")
        report.append("=" * 50)
        report.append("")

        # Summary
        report.append("## Summary")
        total_issues = len(issues)
        report.append(f"Total issues found: {total_issues}")
        report.append("")

        for issue_type, severities in issue_counts.items():
            report.append(f"### {issue_type.replace('_', ' ').title()}")
            for severity, count in severities.items():
                severity_emoji = {'error': '🔴', 'warning': '🟡', 'info': 'ℹ️'}.get(severity, '❓')
                report.append(f"  {severity_emoji} {severity.capitalize()}: {count}")
            report.append("")

        # Detailed issues by file
        report.append("## Detailed Issues by File")
        report.append("")

        for filepath, file_issues in sorted(issues_by_file.items()):
            report.append(f"### {filepath}")
            for issue in file_issues:
                severity_emoji = {'error': '🔴', 'warning': '🟡', 'info': 'ℹ️'}.get(issue.get('severity', 'info'), '❓')
                line_info = f" (line {issue.get('line')})" if 'line' in issue else ""
                report.append(f"  {severity_emoji} {issue['message']}{line_info}")
            report.append("")

        # Recommendations
        report.append("## Recommendations")
        report.append("")
        report.append("### Immediate Actions (High Priority)")
        report.append("- 🔴 Fix all syntax errors and duplicate functions")
        report.append("- 🟡 Review and clean orphaned code blocks")
        report.append("- 🟡 Break down functions longer than 50 lines")
        report.append("")
        report.append("### Maintenance Actions (Medium Priority)")
        report.append("- ℹ️ Remove unused imports")
        report.append("- ℹ️ Address TODO/FIXME comments")
        report.append("")
        report.append("### Prevention Actions (Low Priority)")
        report.append("- Set up pre-commit hooks for code quality")
        report.append("- Implement automated testing for syntax validation")
        report.append("- Add code review guidelines for orphaned code detection")

        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report))
            print(f"Report saved to: {output_file}")
        else:
            print('\n'.join(report))


def main():
    """Main entry point for the code quality analyzer."""
    if len(sys.argv) < 2:
        print("Usage: python code_quality_check.py <directory> [output_file]")
        sys.exit(1)

    root_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    analyzer = CodeQualityAnalyzer(root_dir)
    print(f"Analyzing codebase in: {root_dir}")
    print("This may take a few minutes for large codebases...")

    issues = analyzer.scan_directory()

    print(f"\nFound {len(issues)} issues")
    analyzer.generate_report(issues, output_file)


if __name__ == '__main__':
    main()
