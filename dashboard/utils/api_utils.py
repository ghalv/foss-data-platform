"""Shared API utilities."""

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
