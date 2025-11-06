"""
Utility module for data migration pages that require separate tenant login.
This allows data migration pages to have their own login forms independent of the main session.
"""
import streamlit as st
import json
import requests


def tenantlogin(okapi, tenant, username, password):
    """Login to tenant and return token."""
    myobj = {"username": username, "password": password}
    data = json.dumps(myobj)
    header = {"x-okapi-tenant": tenant}

    x = requests.post(okapi + "/authn/login", data=data, headers=header)
    if "x-okapi-token" in x.headers:
        token = x.headers["x-okapi-token"]
        st.success("Connected! ✅", icon="✅")
        return token
    else:
        st.error("Please check the Tenant information", icon="🚨")
        return None


def render_login_form(page_key_prefix="migration"):
    """
    Render a tenant login form for data migration pages.
    
    Args:
        page_key_prefix: Unique prefix for session state keys to avoid conflicts
        
    Returns:
        tuple: (connected: bool, okapi_url: str, tenant_id: str, token: str, headers: dict)
    """
    # Initialize session state keys with prefix
    connected_key = f"{page_key_prefix}_connected"
    okapi_key = f"{page_key_prefix}_okapi"
    tenant_key = f"{page_key_prefix}_tenant"
    username_key = f"{page_key_prefix}_username"
    token_key = f"{page_key_prefix}_token"
    
    if connected_key not in st.session_state:
        st.session_state[connected_key] = False
    
    st.subheader("🔐 Tenant Login")
    st.caption('Enter tenant credentials to access this data migration tool')
    
    with st.form(f"login_form_{page_key_prefix}"):
        st.text_input("Enter Tenant Username:", key=f"{username_key}_input", placeholder="Please enter your username")
        
        st.text_input("Enter Tenant Password:", key=f"{page_key_prefix}_password_input", 
                     placeholder="Please enter your password", type='password')
        
        st.text_input("Enter Tenant Name:", placeholder="Please enter tenant name", 
                     key=f"{tenant_key}_input")
        
        okapi_options = ("https://api02-v1.ils.medad.com", 
                        "https://api01-v1.ils.medad.com", 
                        "https://api01-v1-uae.ils.medad.com")
        st.selectbox("Select Okapi URL:", okapi_options, key=f"{okapi_key}_input")
        
        col1, col2 = st.columns(2)
        with col1:
            connect_btn = st.form_submit_button("Connect", type="primary")
        with col2:
            reset_btn = st.form_submit_button("Reset")
        
        if connect_btn:
            okapi_val = st.session_state[f"{okapi_key}_input"]
            tenant_val = st.session_state[f"{tenant_key}_input"]
            username_val = st.session_state[f"{username_key}_input"]
            password_val = st.session_state[f"{page_key_prefix}_password_input"]
            
            if not all([okapi_val, tenant_val, username_val, password_val]):
                st.error("⚠️ Please fill in all fields")
            else:
                token = tenantlogin(okapi_val, tenant_val, username_val, password_val)
                if token:
                    st.session_state[connected_key] = True
                    st.session_state[okapi_key] = okapi_val
                    st.session_state[tenant_key] = tenant_val
                    st.session_state[username_key] = username_val
                    st.session_state[token_key] = token
                    # Store password temporarily in session state (cleared on reset or page reload)
                    password_key = f"{page_key_prefix}_password"
                    st.session_state[password_key] = password_val
                    st.rerun()
        
        if reset_btn:
            st.session_state[connected_key] = False
            password_key = f"{page_key_prefix}_password"
            if okapi_key in st.session_state:
                del st.session_state[okapi_key]
            if tenant_key in st.session_state:
                del st.session_state[tenant_key]
            if username_key in st.session_state:
                del st.session_state[username_key]
            if token_key in st.session_state:
                del st.session_state[token_key]
            if password_key in st.session_state:
                del st.session_state[password_key]
            st.success("Cleared! ✅", icon="✅")
            st.rerun()
    
    # Return connection status and credentials
    if st.session_state.get(connected_key, False):
        okapi_url = st.session_state.get(okapi_key, '')
        tenant_id = st.session_state.get(tenant_key, '')
        token = st.session_state.get(token_key, '')
        username = st.session_state.get(username_key, '')
        password_key = f"{page_key_prefix}_password"
        password = st.session_state.get(password_key, '')
        
        if okapi_url and tenant_id and token:
            headers = {
                "x-okapi-tenant": tenant_id,
                "x-okapi-token": token,
                "Content-Type": "application/json"
            }
            return True, okapi_url, tenant_id, token, headers, username, password
    
    return False, '', '', '', {}, '', ''

