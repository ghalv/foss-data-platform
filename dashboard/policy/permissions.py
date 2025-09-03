"""Central policy: allowlists, path ACLs, and guard helpers.

This module does not enforce anything by itself yet; it's a foundation we will
wire into the chat controller when the model tool-calling is added.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set
import os


# Allowlisted high-level actions the chat can request
ALLOWLISTED_ACTIONS: Set[str] = {
    # Pipelines
    "dbt_run",
    "dbt_test",
    "dbt_seed",
    "pipeline_run",
    "pipeline_rerun_last_failed",
    "pipeline_terminate_run",
    "pipeline_pause_schedule",
    # Query
    "execute_query",
    "list_catalogs",
    "list_schemas",
    "list_tables",
    # Storage
    "list_buckets",
    "list_objects",
    "upload_object",
    "delete_object",
    # Ops
    "get_platform_status",
    "get_service_health",
    "restart_service",
}


# Service names that can be controlled (restart/stop/etc.)
SERVICE_ALLOWLIST: Set[str] = {
    "dashboard",
    "dagster",
    "jupyterlab",
    "localhost",
    "trino-worker",
    "grafana",
    "prometheus",
    "minio",
    "postgres",
    "redis",
    "kafka",
    "kafka-ui",
    "zookeeper",
    "flink-jobmanager",
    "flink-taskmanager",
}


@dataclass(frozen=True)
class PathACL:
    read_allow: List[str]
    write_allow: List[str]


# File system ACLs (prefix-based)
PATH_ACL = PathACL(
    read_allow=[
        "docs/",
        "dashboard/templates/",
        "dbt_stavanger_parking/",
    ],
    write_allow=[
        # Limit writes to docs and dbt for now
        "docs/",
        "dbt_stavanger_parking/",
    ],
)


def _is_under(prefixes: List[str], path: str) -> bool:
    norm = path.replace("\\", "/").lstrip("/")
    return any(norm.startswith(p) for p in prefixes)


def is_action_allowed(action: str) -> bool:
    return action in ALLOWLISTED_ACTIONS


def is_service_allowed(service_name: str) -> bool:
    return service_name in SERVICE_ALLOWLIST


def is_path_read_allowed(path: str) -> bool:
    return _is_under(PATH_ACL.read_allow, path)


def is_path_write_allowed(path: str) -> bool:
    return _is_under(PATH_ACL.write_allow, path)


def requires_confirmation(action: str) -> bool:
    """Destructive operations must be explicitly confirmed."""
    return action in {"delete_object", "pipeline_terminate_run", "restart_service"}


def is_safe_path(path: str) -> bool:
    """Basic sanity checks to avoid traversal/symlinks outside repo.

    Note: full symlink escape prevention requires realpath checks when executing.
    """
    if ".." in path.split("/"):
        return False
    if path.startswith(("/", "~")):
        return False
    # Disallow hidden files and dot-directories by default
    parts = path.replace("\\", "/").split("/")
    if any(part.startswith(".") for part in parts):
        return False
    return True


