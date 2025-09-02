"""Typed adapter for storage operations (stub)."""
from __future__ import annotations

from typing import Dict, Any, List


def list_buckets() -> List[str]:
    return []


def list_objects(bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
    return []


def upload_object(bucket: str, key: str, local_path: str) -> Dict[str, Any]:
    return {"success": False, "error": "not_implemented"}


def delete_object(bucket: str, key: str) -> Dict[str, Any]:
    return {"success": False, "error": "not_implemented"}


