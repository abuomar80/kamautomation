import streamlit as st
import json
import requests
from Tenant_Backup import backup

# Note: st.set_page_config() is removed as it's already set in Homepage.py

if 'download' not in st.session_state:
    st.session_state['download'] = False


def tenantlogin(okapi, tenant, username, password):
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


st.title("💾 Backup Tenant")
st.caption('This Section is used to connect to the tenant in order to start the Backup Process')

with st.form("backup_form"):
    st.text_input("Enter Tenant Username:", key="username_tenant_3", placeholder="Please enter your username")
    st.text_input("Enter Tenant Password:", key="password_3", placeholder="Please enter your password", type='password')
    st.text_input("Enter Tenant Name:", placeholder="Please enter tenant name", key="tenant_3")
    st.selectbox(
        "Select Okapi URL:",
        ("https://api02-v1.ils.medad.com", "https://api01-v1.ils.medad.com", "https://api01-v1-uae.ils.medad.com"),
        key="okapi_3",
    )
    submitted_backup = st.form_submit_button("Connect", type="primary")
    if submitted_backup:
        st.session_state['download'] = True
        token = tenantlogin(
            st.session_state.okapi_3,
            st.session_state.tenant_3,
            st.session_state.username_tenant_3,
            st.session_state.password_3,
        )
        if token:
            st.session_state.token_3 = token

if st.session_state.download:
    st.divider()
    with st.spinner(f'Preparing Backup for {st.session_state.tenant_3}...'):
        headers = {
            'x-okapi-tenant': st.session_state.tenant_3,
            'x-okapi-token': st.session_state.token_3
        }
        file = backup(headers, st.session_state.okapi_3)
        st.success("✅ Backup prepared successfully!")
        st.download_button("⬇️ Download Backup", data=file, file_name=f"tenant_backup_{st.session_state.tenant_3}.json", mime='application/json')
