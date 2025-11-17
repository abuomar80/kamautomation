import streamlit as st
from Upload import upload
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import json
from legacy_session_state import legacy_session_state

legacy_session_state()

# Initialize tenant-related session state variables if not set
# Check both widget-bound keys and copied keys (from form submission)
# Use .get() to safely check and initialize values
if not st.session_state.get('tenant'):
    st.session_state['tenant'] = st.session_state.get('tenant_name', '')
if not st.session_state.get('okapi'):
    st.session_state['okapi'] = st.session_state.get('okapi_url', '')
if not st.session_state.get('token'):
    st.session_state['token'] = st.session_state.get('token', '')

def post_smtp(df, headers, okapi):
    data = {
        "module": "SMTP_SERVER",
        "configName": "smtp",
        "code": "EMAIL_SMTP_HOST",
        "enabled": "true",
        "value": " smtp.gmail1.com"
    }
    data = json.dumps(data)
    response = requests.post(okapi + "/configurations/entries", data=data, headers=headers)
    return response

def smtp():
    # Get tenant connection details with fallbacks
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name")
    token = st.session_state.get("token")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url")

    if not all([tenant, token, okapi]):
        st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        st.info("Go to the Tenant page, enter connection details, click Connect, then return here.")
        return
    
    df = upload('SMTP')
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    builder = GridOptionsBuilder.from_dataframe(df)
    builder.configure_selection(selection_mode='multiple', use_checkbox=True)
    #builder.set_selected_rows([0])
    go = builder.build()
    grid_return = AgGrid(df, editable=True, theme='balham', gridOptions=go)
    selected_rows = grid_return['selected_rows']
    # st.write(selected_rows)
    if bool(selected_rows):
        selection = pd.DataFrame(selected_rows)
        response = post_smtp(selection, headers, okapi)
        postit = st.button('Create SMTP ', on_click=post_smtp, args=[selection, headers, okapi],)
        if response.status_code == 201 and postit:
            st.success('SMTP Created')
        else:
            st.write(response)
            st.warning('Somthing went wrong !!')