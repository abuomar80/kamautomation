"""
Centralized connection management utility for API requests.
Provides token refresh, connection validation, retry logic, and session management.
"""
import streamlit as st
import requests
import json
import time
from typing import Optional, Tuple, Dict, Any
from legacy_session_state import legacy_session_state

# Initialize legacy session state
legacy_session_state()


def get_connection_details() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Get tenant connection details from session state with fallbacks."""
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url")
    token = st.session_state.get("token")
    return tenant, okapi, token


def refresh_token(okapi: str, tenant: str, username: str, password: str) -> Optional[str]:
    """Refresh the authentication token."""
    try:
        myobj = {"username": username, "password": password}
        data = json.dumps(myobj)
        header = {"x-okapi-tenant": tenant}
        response = requests.post(okapi + "/authn/login", data=data, headers=header, timeout=30)
        if "x-okapi-token" in response.headers:
            new_token = response.headers["x-okapi-token"]
            st.session_state['token'] = new_token
            return new_token
    except Exception as e:
        if hasattr(st, 'warning'):
            st.warning(f"⚠️ Token refresh failed: {str(e)}")
    return None


def validate_connection(session: requests.Session, okapi: str, tenant: str, token: str, max_retries: int = 3) -> Tuple[bool, str]:
    """Validate connection and refresh token if needed."""
    for attempt in range(max_retries):
        try:
            test_response = session.get(f"{okapi}/locations?limit=1", timeout=10)
            if test_response.status_code == 200:
                return True, token  # Connection is valid
            elif test_response.status_code == 401:
                # Token expired, try to refresh
                username = st.session_state.get('username_tenant') or st.session_state.get('tenant_username')
                password = st.session_state.get('password')
                if username and password:
                    new_token = refresh_token(okapi, tenant, username, password)
                    if new_token:
                        # Update session headers
                        session.headers.update({"x-okapi-tenant": tenant, "x-okapi-token": new_token})
                        return True, new_token
                return False, token  # Cannot refresh
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
    return False, token


def get_session() -> Optional[requests.Session]:
    """Get or create a requests session with proper headers."""
    tenant, okapi, token = get_connection_details()
    
    if not all([tenant, okapi, token]):
        return None
    
    session = requests.Session()
    session.headers.update({
        "x-okapi-tenant": tenant,
        "x-okapi-token": token,
        "Content-Type": "application/json"
    })
    return session


def make_request_with_retry(
    session: requests.Session,
    method: str,
    url: str,
    max_retries: int = 3,
    validate_before: bool = False,
    **kwargs
) -> Optional[requests.Response]:
    """
    Make HTTP request with retry logic, connection validation, and automatic token refresh.
    
    Args:
        session: Requests session object
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: Request URL
        max_retries: Maximum number of retry attempts
        validate_before: Whether to validate connection before making request
        **kwargs: Additional arguments to pass to requests method
    
    Returns:
        Response object or None if all retries failed
    """
    tenant, okapi, token = get_connection_details()
    
    # Validate connection before request if requested
    if validate_before and tenant and okapi and token:
        is_valid, current_token = validate_connection(session, okapi, tenant, token)
        if not is_valid:
            return None
        token = current_token
        session.headers.update({"x-okapi-tenant": tenant, "x-okapi-token": token})
    
    # Set default timeout if not provided
    if 'timeout' not in kwargs:
        kwargs['timeout'] = 30
    
    for attempt in range(max_retries):
        try:
            if method.upper() == 'GET':
                response = session.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = session.post(url, **kwargs)
            elif method.upper() == 'PUT':
                response = session.put(url, **kwargs)
            elif method.upper() == 'DELETE':
                response = session.delete(url, **kwargs)
            elif method.upper() == 'PATCH':
                response = session.patch(url, **kwargs)
            else:
                response = session.request(method, url, **kwargs)
            
            # If unauthorized, try to refresh token once
            if response.status_code == 401 and attempt == 0 and tenant and okapi:
                username = st.session_state.get('username_tenant') or st.session_state.get('tenant_username')
                password = st.session_state.get('password')
                
                if username and password:
                    new_token = refresh_token(okapi, tenant, username, password)
                    if new_token:
                        st.session_state['token'] = new_token
                        session.headers.update({"x-okapi-tenant": tenant, "x-okapi-token": new_token})
                        # Retry the request with new token
                        continue
            
            return response
            
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            return None
        except requests.exceptions.RequestException:
            if attempt < max_retries - 1:
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                continue
            return None
    
    return None


def safe_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    data: Optional[Any] = None,
    json_data: Optional[Dict] = None,
    max_retries: int = 3,
    validate_before: bool = False
) -> Optional[requests.Response]:
    """
    Make a safe API request with automatic session management, token refresh, and retry logic.
    This is a convenience function that doesn't require a pre-created session.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: Request URL
        headers: Optional headers (will be merged with session headers)
        data: Optional request data
        json_data: Optional JSON data (will be converted to JSON string)
        max_retries: Maximum number of retry attempts
        validate_before: Whether to validate connection before making request
    
    Returns:
        Response object or None if all retries failed
    """
    session = get_session()
    if not session:
        return None
    
    # Merge custom headers if provided
    if headers:
        session.headers.update(headers)
    
    # Prepare request kwargs
    kwargs = {}
    if data:
        kwargs['data'] = data
    if json_data:
        kwargs['data'] = json.dumps(json_data)
    
    response = make_request_with_retry(
        session,
        method,
        url,
        max_retries=max_retries,
        validate_before=validate_before,
        **kwargs
    )
    
    return response


def periodic_connection_check(session: requests.Session, check_interval: int = 25) -> bool:
    """
    Check if periodic connection validation is needed and perform it.
    Call this periodically during long-running operations.
    
    Args:
        session: Requests session object
        check_interval: How often to check (in number of operations)
    
    Returns:
        True if connection is valid, False otherwise
    """
    tenant, okapi, token = get_connection_details()
    if not all([tenant, okapi, token]):
        return False
    
    is_valid, current_token = validate_connection(session, okapi, tenant, token)
    if is_valid and current_token != token:
        # Token was refreshed, update session
        session.headers.update({"x-okapi-tenant": tenant, "x-okapi-token": current_token})
        st.session_state['token'] = current_token
    
    return is_valid

