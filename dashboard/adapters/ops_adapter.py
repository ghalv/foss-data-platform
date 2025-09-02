"""Typed adapter for ops (restart/health) (stub)."""
from __future__ import annotations

from typing import Dict, Any


def get_platform_status() -> Dict[str, Any]:
    return {"success": True, "status": "unknown"}


def restart_service(service_name: str) -> Dict[str, Any]:
    return {"success": False, "error": "not_implemented", "service": service_name}


