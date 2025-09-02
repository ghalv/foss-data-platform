#!/usr/bin/env python3
"""
Duplicate Code Analyzer and Remediation Tool

This script identifies duplicate code patterns and suggests refactoring strategies
for the FOSS Data Platform codebase.
"""

import os
import re
import ast
import sys
import difflib
from collections import defaultdict
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass


@dataclass
class DuplicateFunction:
    name: str
    locations: List[str]
    similarity_score: float
    lines_of_code: int


@dataclass
class CodeSimilarity:
    file1: str
    file2: str
    function_name: str
    similarity: float
    duplicate_lines: int


class DuplicateCodeAnalyzer:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.exclude_patterns = ['.venv', '__pycache__', 'node_modules', '.git']

    def analyze_duplicates(self) -> Dict[str, List[DuplicateFunction]]:
        """Analyze duplicate functions and code patterns."""
        function_map = defaultdict(list)
        function_content = {}

        # Collect all functions
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if not any(pat in d for pat in self.exclude_patterns)]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    functions = self._extract_functions(filepath)

                    for func_name, content, line_count in functions:
                        function_map[func_name].append(filepath)
                        key = f"{filepath}:{func_name}"
                        function_content[key] = (content, line_count)

        # Find true duplicates
        duplicates = {}
        for func_name, locations in function_map.items():
            if len(locations) > 1:
                # Check if they're actually duplicates or just same names
                duplicate_locations = []
                base_content = None

                for loc in locations:
                    key = f"{loc}:{func_name}"
                    if key in function_content:
                        content, lines = function_content[key]
                        if base_content is None:
                            base_content = content
                            duplicate_locations.append(loc)
                        elif self._calculate_similarity(base_content, content) > 0.8:
                            duplicate_locations.append(loc)

                if len(duplicate_locations) > 1:
                    duplicates[func_name] = DuplicateFunction(
                        name=func_name,
                        locations=duplicate_locations,
                        similarity_score=1.0,
                        lines_of_code=function_content[f"{duplicate_locations[0]}:{func_name}"][1]
                    )

        return duplicates

    def _extract_functions(self, filepath: str) -> List[Tuple[str, str, int]]:
        """Extract function definitions and their content."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            functions = []
            lines = content.split('\n')

            i = 0
            while i < len(lines):
                line = lines[i]
                # Find function definition
                match = re.match(r'^\s*def\s+(\w+)\s*\(', line)
                if match:
                    func_name = match.group(1)
                    start_line = i

                    # Find function end (next function or end of file)
                    indent_level = len(line) - len(line.lstrip())
                    end_line = start_line

                    j = start_line + 1
                    while j < len(lines):
                        next_line = lines[j]
                        if next_line.strip() == '':
                            j += 1
                            continue

                        current_indent = len(next_line) - len(next_line.lstrip())
                        # Next function at same level
                        if (re.match(r'^\s*def\s+\w+\s*\(', next_line) and
                            current_indent <= indent_level):
                            break
                        # Class or other top-level construct
                        elif (re.match(r'^\s*(class|def|if|for|while)\s+', next_line) and
                              current_indent <= indent_level):
                            break

                        end_line = j
                        j += 1

                    # Extract function content
                    func_content = '\n'.join(lines[start_line:end_line + 1])
                    line_count = end_line - start_line + 1
                    functions.append((func_name, func_content, line_count))

                    i = end_line
                else:
                    i += 1

            return functions

        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            return []

    def _calculate_similarity(self, code1: str, code2: str) -> float:
        """Calculate similarity between two code snippets."""
        # Remove comments and normalize whitespace
        def normalize_code(code: str) -> str:
            # Remove comments
            code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)
            # Normalize whitespace
            code = re.sub(r'\s+', ' ', code)
            return code.strip()

        norm1 = normalize_code(code1)
        norm2 = normalize_code(code2)

        if not norm1 or not norm2:
            return 0.0

        # Use sequence matcher for similarity
        matcher = difflib.SequenceMatcher(None, norm1, norm2)
        return matcher.ratio()

    def analyze_code_patterns(self) -> Dict[str, List[CodeSimilarity]]:
        """Analyze common code patterns that could be extracted."""
        patterns = defaultdict(list)

        # Look for similar error handling patterns
        error_patterns = self._find_error_patterns()

        # Look for similar API endpoint patterns
        api_patterns = self._find_api_patterns()

        # Look for similar database query patterns
        query_patterns = self._find_query_patterns()

        patterns['error_handling'] = error_patterns
        patterns['api_endpoints'] = api_patterns
        patterns['database_queries'] = query_patterns

        return patterns

    def _find_error_patterns(self) -> List[CodeSimilarity]:
        """Find similar error handling patterns."""
        patterns = []

        # Look for try/except blocks with similar structure
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if not any(pat in d for pat in self.exclude_patterns)]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Find try/except blocks
                        try_blocks = re.findall(r'try:\s*\n(.*?)\n\s*except', content, re.DOTALL)
                        for block in try_blocks:
                            if len(block.split('\n')) > 3:  # Substantial error handling
                                patterns.append(CodeSimilarity(
                                    file1=filepath,
                                    file2='',  # Not comparing to another file
                                    function_name='error_handler',
                                    similarity=1.0,
                                    duplicate_lines=len(block.split('\n'))
                                ))

                    except Exception:
                        continue

        return patterns[:10]  # Limit results

    def _find_api_patterns(self) -> List[CodeSimilarity]:
        """Find similar API endpoint patterns."""
        patterns = []

        # Look for Flask route patterns
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if not any(pat in d for pat in self.exclude_patterns)]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Find route patterns
                        routes = re.findall(r'@app\.route\([^)]+\)\s*\n\s*def\s+(\w+)', content)
                        for route_func in routes:
                            patterns.append(CodeSimilarity(
                                file1=filepath,
                                file2='',
                                function_name=route_func,
                                similarity=1.0,
                                duplicate_lines=0  # Will be calculated later
                            ))

                    except Exception:
                        continue

        return patterns[:10]

    def _find_query_patterns(self) -> List[CodeSimilarity]:
        """Find similar database query patterns."""
        patterns = []

        # Look for SQL query patterns
        for root, dirs, files in os.walk(self.root_dir):
            dirs[:] = [d for d in dirs if not any(pat in d for pat in self.exclude_patterns)]

            for file in files:
                if file.endswith('.py'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Find SELECT queries
                        queries = re.findall(r'SELECT\s+.*?\s+FROM', content, re.IGNORECASE | re.DOTALL)
                        for query in queries:
                            if len(query) > 20:  # Substantial query
                                patterns.append(CodeSimilarity(
                                    file1=filepath,
                                    file2='',
                                    function_name='sql_query',
                                    similarity=1.0,
                                    duplicate_lines=len(query.split())
                                ))

                    except Exception:
                        continue

        return patterns[:10]

    def generate_report(self, duplicates: Dict[str, List[DuplicateFunction]],
                       patterns: Dict[str, List[CodeSimilarity]]) -> str:
        """Generate a comprehensive duplicate code report."""

        report_lines = []
        report_lines.append("# Duplicate Code Analysis Report")
        report_lines.append("=" * 50)
        report_lines.append("")

        # Summary
        total_duplicates = len(duplicates)
        total_lines_saved = sum(dup.lines_of_code * (len(dup.locations) - 1)
                              for dup in duplicates.values())

        report_lines.append("## Executive Summary")
        report_lines.append("")
        report_lines.append(f"**Total Duplicate Functions:** {total_duplicates}")
        report_lines.append(f"**Estimated Lines of Code Saved:** {total_lines_saved}")
        report_lines.append(f"**Potential Files to Refactor:** {len(set(loc for dup in duplicates.values() for loc in dup.locations))}")
        report_lines.append("")

        # Duplicate Functions
        report_lines.append("## Duplicate Functions")
        report_lines.append("")

        for func_name, dup_func in sorted(duplicates.items()):
            report_lines.append(f"### `{func_name}`")
            report_lines.append(f"- **Lines of Code:** {dup_func.lines_of_code}")
            report_lines.append(f"- **Occurrences:** {len(dup_func.locations)}")
            report_lines.append("- **Locations:**")
            for loc in dup_func.locations:
                report_lines.append(f"  - `{loc}`")
            report_lines.append("")

        # Code Patterns
        report_lines.append("## Code Pattern Analysis")
        report_lines.append("")

        for pattern_type, similarities in patterns.items():
            if similarities:
                report_lines.append(f"### {pattern_type.replace('_', ' ').title()}")
                report_lines.append("")
                for sim in similarities[:5]:  # Show top 5
                    report_lines.append(f"- **{sim.function_name}** in `{sim.file1}` ({sim.duplicate_lines} lines)")
                report_lines.append("")

        # Recommendations
        report_lines.append("## Recommendations")
        report_lines.append("")

        report_lines.append("### Immediate Actions (High Priority)")
        report_lines.append("- 🔴 Remove true duplicate functions (same implementation)")
        report_lines.append("- 🟡 Consolidate API endpoint duplications")
        report_lines.append("- 🟡 Extract common error handling patterns")
        report_lines.append("")

        report_lines.append("### Refactoring Strategies")
        report_lines.append("")
        report_lines.append("#### 1. Extract Common Functionality")
        report_lines.append("```python")
        report_lines.append("# Instead of duplicating:")
        report_lines.append("# File A: def get_platform_status()")
        report_lines.append("# File B: def get_platform_status()")
        report_lines.append("")
        report_lines.append("# Create shared module:")
        report_lines.append("# platform_utils.py")
        report_lines.append("def get_platform_status():")
        report_lines.append("    # Shared implementation")
        report_lines.append("    pass")
        report_lines.append("```")
        report_lines.append("")

        report_lines.append("#### 2. Use Inheritance for Similar Classes")
        report_lines.append("```python")
        report_lines.append("# Base API class")
        report_lines.append("class BaseAPI:")
        report_lines.append("    def common_method(self):")
        report_lines.append("        # Shared logic")
        report_lines.append("        pass")
        report_lines.append("")
        report_lines.append("# Specific implementations")
        report_lines.append("class StreamingAPI(BaseAPI):")
        report_lines.append("    def stream_specific_method(self):")
        report_lines.append("        self.common_method()  # Reuse")
        report_lines.append("        pass")
        report_lines.append("```")
        report_lines.append("")

        report_lines.append("#### 3. Create Utility Modules")
        report_lines.append("```python")
        report_lines.append("# utils/error_handlers.py")
        report_lines.append("def handle_api_error(error, context):")
        report_lines.append("    # Standardized error handling")
        report_lines.append("    pass")
        report_lines.append("")
        report_lines.append("# Usage across modules:")
        report_lines.append("from utils.error_handlers import handle_api_error")
        report_lines.append("```")
        report_lines.append("")

        report_lines.append("### Implementation Timeline")
        report_lines.append("")
        report_lines.append("#### Week 1: Critical Duplicates")
        report_lines.append("- [ ] Remove exact duplicate functions")
        report_lines.append("- [ ] Consolidate identical API endpoints")
        report_lines.append("- [ ] Create shared utility functions")
        report_lines.append("")
        report_lines.append("#### Week 2: Pattern Extraction")
        report_lines.append("- [ ] Extract common error handling")
        report_lines.append("- [ ] Standardize API response formats")
        report_lines.append("- [ ] Create base classes for similar functionality")
        report_lines.append("")
        report_lines.append("#### Week 3: Testing & Validation")
        report_lines.append("- [ ] Update all import statements")
        report_lines.append("- [ ] Run comprehensive tests")
        report_lines.append("- [ ] Validate all functionality works")
        report_lines.append("")
        report_lines.append("#### Ongoing: Maintenance")
        report_lines.append("- [ ] Regular duplicate code audits")
        report_lines.append("- [ ] Update coding standards")
        report_lines.append("- [ ] Team training on best practices")

        return '\n'.join(report_lines)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python duplicate_code_analyzer.py <directory> [output_file]")
        sys.exit(1)

    root_dir = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print("🔍 Analyzing duplicate code patterns...")
    analyzer = DuplicateCodeAnalyzer(root_dir)

    # Analyze duplicates
    duplicates = analyzer.analyze_duplicates()
    print(f"Found {len(duplicates)} duplicate function groups")

    # Analyze patterns
    patterns = analyzer.analyze_code_patterns()
    print(f"Analyzed {sum(len(p) for p in patterns.values())} code patterns")

    # Generate report
    report = analyzer.generate_report(duplicates, patterns)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"✅ Report saved to: {output_file}")
    else:
        print(report)


if __name__ == '__main__':
    main()
