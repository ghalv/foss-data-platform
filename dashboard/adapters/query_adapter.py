"""Typed adapter for query operations against Trino (stub)."""
from __future__ import annotations

from typing import Dict, Any, List


def execute_query(sql: str, catalog: str = "memory", schema: str = "default", row_limit: int = 1000, timeout_s: int = 30) -> Dict[str, Any]:
    return {
        "success": False,
        "error": "not_implemented",
        "sql": sql,
        "catalog": catalog,
        "schema": schema,
        "row_limit": row_limit,
    }


def list_catalogs() -> List[str]:
    return []


def list_schemas(catalog: str) -> List[str]:
    return []


def list_tables(catalog: str, schema: str) -> List[str]:
    return []


