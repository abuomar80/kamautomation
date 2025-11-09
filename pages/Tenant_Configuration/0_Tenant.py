import streamlit as st
import json
import requests
from legacy_session_state import legacy_session_state

# Initialize legacy session state for compatibility
legacy_session_state()

# Note: st.set_page_config() is removed as it's already set in Homepage.py
# and causes errors when pages are loaded dynamically

if 'allow_tenant' not in st.session_state:
    st.session_state['allow_tenant'] = False


def tenantlogin(okapi, tenant, username, password):
    myobj = {"username": username, "password": password}
    data = json.dumps(myobj)
    header = {"x-okapi-tenant": tenant}

    x = requests.post(okapi + "/authn/login", data=data, headers=header)
    if "x-okapi-token" in x.headers:
        token = x.headers["x-okapi-token"]
        st.success("Connected! ✅", icon="✅")
        st.session_state.allow_tenant = True
        return token
    else:
        st.error("Please check the Tenant information", icon="🚨")
        return None


def reset():
    st.session_state.allow_tenant = False
    if 'token' in st.session_state:
        del st.session_state['token']
    if 'tenant_name' in st.session_state:
        del st.session_state['tenant_name']
    if 'okapi_url' in st.session_state:
        del st.session_state['okapi_url']
    if 'tenant_username' in st.session_state:
        del st.session_state['tenant_username']


st.title("🔐 Tenant Login")
st.caption('Connect to your tenant to start configuration. This session will be maintained across all Tenant Configuration pages.')

# Use regular inputs instead of form to avoid widget key conflicts when page is loaded dynamically
st.text_input("Enter Tenant Username:", key="username_tenant", placeholder="Please enter your username")
st.text_input("Enter Tenant Password:", key="password", placeholder="Please enter your password", type='password')
st.text_input("Enter Tenant Name:", placeholder="Please enter tenant name", key="tenant")
st.selectbox(
    "Select Okapi URL:",
    ("https://api02-v1.ils.medad.com", "https://api01-v1.ils.medad.com", "https://api01-v1-uae.ils.medad.com"),
    key="okapi",
)

col1, col2 = st.columns(2)
with col1:
    connect_clicked = st.button("Connect", type="primary", use_container_width=True, key="tenant_connect_btn")
with col2:
    reset_clicked = st.button("Reset", use_container_width=True, key="tenant_reset_btn")

if connect_clicked:
    # Validate inputs
    if not st.session_state.get('username_tenant') or not st.session_state.get('password') or not st.session_state.get('tenant') or not st.session_state.get('okapi'):
        st.error("Please fill in all fields")
    else:
        token = tenantlogin(
            st.session_state.okapi,
            st.session_state.tenant,
            st.session_state.username_tenant,
            st.session_state.password
        )
        if token:
            # Store the token in session state for use across Tenant Configuration pages
            st.session_state.token = token
            # Copy form values to separate session state keys for persistence
            st.session_state['tenant_name'] = st.session_state.get('tenant', '')
            st.session_state['okapi_url'] = st.session_state.get('okapi', '')
            st.session_state['tenant_username'] = st.session_state.get('username_tenant', '')
            st.rerun()

if reset_clicked:
    reset()
    st.success("Cleared! ✅", icon="✅")
    st.rerun()

if st.session_state.allow_tenant:
    st.divider()
    st.success(f"✅ Connected to tenant: **{st.session_state.get('tenant_name', st.session_state.get('tenant', ''))}**")
    st.info("💡 You can now navigate to other Tenant Configuration pages. Your session will remain active.")

