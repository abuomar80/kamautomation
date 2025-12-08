# Connection Management Guide

## Overview

The `connection_manager.py` module provides centralized connection management for all API requests. It includes:
- Automatic token refresh when expired
- Connection validation and keep-alive
- Retry logic with exponential backoff
- Session management

## Key Functions

### `safe_request()`
Make API requests with automatic retry and token refresh:
```python
from connection_manager import safe_request

response = safe_request('GET', f"{okapi}/locations?limit=10")
if response and response.status_code == 200:
    data = response.json()
```

### `get_session()`
Get a managed session for multiple requests:
```python
from connection_manager import get_session, make_request_with_retry, periodic_connection_check

session = get_session()
if session:
    # Make requests using the session
    response = make_request_with_retry(session, 'GET', url)
    
    # Check connection periodically during long operations
    if not periodic_connection_check(session):
        # Handle connection loss
        pass
```

### `validate_connection()`
Validate and refresh connection:
```python
from connection_manager import validate_connection, get_session

session = get_session()
is_valid, token = validate_connection(session, okapi, tenant, token)
```

## Migration Pattern

### Before (Direct requests):
```python
import requests

headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}
response = requests.get(f"{okapi}/locations", headers=headers)
data = response.json()
```

### After (Using connection_manager):
```python
from connection_manager import safe_request

response = safe_request('GET', f"{okapi}/locations")
if response and response.status_code == 200:
    data = response.json()
```

### For POST requests:
```python
# Before
response = requests.post(url, headers=headers, json=data)

# After
response = safe_request('POST', url, json_data=data)
```

## Files Already Updated

- ✅ `connection_manager.py` - Core utility module
- ✅ `Service_points.py` - All functions updated
- ✅ `Location.py` - Main location creation logic updated

## Files That Should Be Updated

The following files make direct API calls and should be migrated to use `connection_manager`:

1. `UserImport.py` - User import operations
2. `pages/Tenant_Configuration/4_Default Users.py` - User creation
3. `pages/Tenant_Configuration/1_Basic Configuration.py` - Configuration operations
4. `pages/Tenant_Configuration/3_SIP2 Configuration.py` - SIP2 configuration
5. `Tenant_Backup.py` - Backup operations
6. `clone_functions.py` - Clone operations
7. `FeeFine.py`, `Waives.py`, `Refunds.py`, `ManualCharges.py` - Financial operations
8. Other configuration files in `pages/Tenant_Configuration/`

## Benefits

1. **Automatic Token Refresh**: Tokens are automatically refreshed when expired
2. **Connection Keep-Alive**: Connections are validated periodically during long operations
3. **Retry Logic**: Failed requests are automatically retried with exponential backoff
4. **Consistent Error Handling**: All API calls use the same error handling pattern
5. **Better Reliability**: Reduces connection-related failures during bulk operations

## Usage in Long-Running Operations

For operations processing many rows (like location creation with 2000+ rows):

```python
from connection_manager import get_session, make_request_with_retry, periodic_connection_check

session = get_session()
for idx, row in enumerate(rows):
    # Check connection every 25 rows
    if idx > 0 and idx % 25 == 0:
        if not periodic_connection_check(session):
            st.error("Connection lost!")
            break
    
    # Make API calls
    response = make_request_with_retry(session, 'POST', url, json_data=data)
    if not response:
        # Handle failure
        continue
```

## Notes

- The connection manager automatically handles token refresh using credentials from session state
- All requests use a 30-second timeout by default
- Retry logic uses exponential backoff (0.5s, 1s, 1.5s delays)
- Connection validation checks every 25 operations by default (configurable)

