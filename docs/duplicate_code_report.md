# Duplicate Code Analysis Report
==================================================

## Executive Summary

**Total Duplicate Functions:** 5
**Estimated Lines of Code Saved:** 78
**Potential Files to Refactor:** 1

## Duplicate Functions

### `_get_openai_client`
- **Lines of Code:** 3
- **Occurrences:** 2
- **Locations:**
  - `./dashboard/app.py`
  - `./dashboard/app.py`

### `_resolve_ckan_parking_json_url`
- **Lines of Code:** 29
- **Occurrences:** 2
- **Locations:**
  - `./dashboard/app.py`
  - `./dashboard/app.py`

### `get_pipeline_status`
- **Lines of Code:** 19
- **Occurrences:** 2
- **Locations:**
  - `./dashboard/app.py`
  - `./dashboard/app.py`

### `read_recent_events`
- **Lines of Code:** 17
- **Occurrences:** 2
- **Locations:**
  - `./dashboard/app.py`
  - `./dashboard/app.py`

### `write_event`
- **Lines of Code:** 10
- **Occurrences:** 2
- **Locations:**
  - `./dashboard/app.py`
  - `./dashboard/app.py`

## Code Pattern Analysis

### Error Handling

- **error_handler** in `./qa_test_suite.py` (9 lines)
- **error_handler** in `./qa_test_suite.py` (8 lines)
- **error_handler** in `./qa_test_suite.py` (6 lines)
- **error_handler** in `./qa_test_suite.py` (16 lines)
- **error_handler** in `./qa_test_suite.py` (50 lines)

### Api Endpoints

- **dashboard** in `./dashboard/app.py` (0 lines)
- **api_health** in `./dashboard/app.py` (0 lines)
- **health_page** in `./dashboard/app.py` (0 lines)
- **api_metrics** in `./dashboard/app.py` (0 lines)
- **metrics_page** in `./dashboard/app.py` (0 lines)

### Database Queries

- **sql_query** in `./service_validation_suite.py` (228 lines)
- **sql_query** in `./dashboard/app.py` (5 lines)
- **sql_query** in `./dashboard/app.py` (5 lines)
- **sql_query** in `./dashboard/app.py` (6 lines)
- **sql_query** in `./dashboard/app.py` (5 lines)

## Recommendations

### Immediate Actions (High Priority)
- 🔴 Remove true duplicate functions (same implementation)
- 🟡 Consolidate API endpoint duplications
- 🟡 Extract common error handling patterns

### Refactoring Strategies

#### 1. Extract Common Functionality
```python
# Instead of duplicating:
# File A: def get_platform_status()
# File B: def get_platform_status()

# Create shared module:
# platform_utils.py
def get_platform_status():
    # Shared implementation
    pass
```

#### 2. Use Inheritance for Similar Classes
```python
# Base API class
class BaseAPI:
    def common_method(self):
        # Shared logic
        pass

# Specific implementations
class StreamingAPI(BaseAPI):
    def stream_specific_method(self):
        self.common_method()  # Reuse
        pass
```

#### 3. Create Utility Modules
```python
# utils/error_handlers.py
def handle_api_error(error, context):
    # Standardized error handling
    pass

# Usage across modules:
from utils.error_handlers import handle_api_error
```

### Implementation Timeline

#### Week 1: Critical Duplicates
- [ ] Remove exact duplicate functions
- [ ] Consolidate identical API endpoints
- [ ] Create shared utility functions

#### Week 2: Pattern Extraction
- [ ] Extract common error handling
- [ ] Standardize API response formats
- [ ] Create base classes for similar functionality

#### Week 3: Testing & Validation
- [ ] Update all import statements
- [ ] Run comprehensive tests
- [ ] Validate all functionality works

#### Ongoing: Maintenance
- [ ] Regular duplicate code audits
- [ ] Update coding standards
- [ ] Team training on best practices