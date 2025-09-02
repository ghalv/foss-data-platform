"""Typed adapter for dbt operations.

This is a stub; wire real subprocess calls behind validation later.
"""
from __future__ import annotations

from typing import Dict, Any


def run(pipeline_id: str, target: str = "dev") -> Dict[str, Any]:
    return {"success": False, "error": "not_implemented", "pipeline_id": pipeline_id, "target": target}


def test(pipeline_id: str, target: str = "dev") -> Dict[str, Any]:
    return {"success": False, "error": "not_implemented", "pipeline_id": pipeline_id, "target": target}


def seed(pipeline_id: str, target: str = "dev") -> Dict[str, Any]:
    return {"success": False, "error": "not_implemented", "pipeline_id": pipeline_id, "target": target}


