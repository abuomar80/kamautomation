import streamlit as st
from Upload import upload
import pandas as pd
import requests
import json
from st_aggrid import AgGrid, GridOptionsBuilder
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

def dept():
    st.title("Departments")
    
    # Get tenant connection details with fallbacks
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name")
    token = st.session_state.get("token")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url")

    if not all([tenant, token, okapi]):
        st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        st.info("Go to the Tenant page, enter connection details, click Connect, then return here.")
        return
    
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    file = upload('Department')

    builder = GridOptionsBuilder.from_dataframe(file)
    builder.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
    builder.configure_pagination(enabled=True)

    myList = ['Department name', 'Department Code']
    for item in myList:
        builder.configure_column(item, editable=True)

    go = builder.build()
    grid_return = AgGrid(file, editable=True, theme='balham', gridOptions=go)

    selected_rows = grid_return['selected_rows']

    if bool(selected_rows):
        selection = pd.DataFrame(selected_rows)
        createDept = st.button("Create Department")

        if createDept:
            error_messages = []  # Track errors for summary
            with st.spinner(f'Creating Selected Departments..'):
                for index, row in selection.iterrows():
                    data = {
                        "name": row["Name"],
                        "code": row["Code"]
                    }
                    res = requests.post(f'{okapi}/departments', data=json.dumps(data), headers=headers)
                    
                    # Handle response - check for errors
                    if res.status_code not in [201, 422]:  # 422 = already exists (OK)
                        try:
                            error_data = res.json()
                            if 'errors' in error_data:
                                error_msg = error_data['errors'][0].get('message', 'Unknown error')
                                error_messages.append(f"Department '{row['Name']}': {error_msg}")
                                st.warning(f"⚠️ Department '{row['Name']}': {error_msg}")
                        except:
                            error_messages.append(f"Department '{row['Name']}': Error (Status: {res.status_code})")
                            st.warning(f"⚠️ Department '{row['Name']}': Error (Status: {res.status_code})")
            
            # Summary message - shown once after all departments are processed
            if error_messages:
                st.success("✅ Departments processed!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
            else:
                st.success("✅ Departments have been created successfully!")
                st.info("💡 All departments were created or already existed.")