"""Shared error handling utilities."""

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
