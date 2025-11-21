import streamlit as st
from Upload import upload
import requests
from pandas import json_normalize
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import json

from legacy_session_state import legacy_session_state

# Get session state of legacy session
legacy_session_state()

# Initialize tenant-related session state variables if not set
# Check both widget-bound keys and copied keys (from form submission)
if 'tenant' not in st.session_state or not st.session_state.get('tenant'):
    st.session_state['tenant'] = st.session_state.get('tenant_name', '')
if 'okapi' not in st.session_state or not st.session_state.get('okapi'):
    st.session_state['okapi'] = st.session_state.get('okapi_url', '')
if 'token' not in st.session_state:
    st.session_state['token'] = st.session_state.get('token', '')
if 'username_tenant' not in st.session_state or not st.session_state.get('username_tenant'):
    st.session_state['username_tenant'] = st.session_state.get('tenant_username', '')


def post_material(df, headers):
    """
    Posts a new material type to the Okapi API
    :param df: dataframe containing the material types to be posted
    :param headers: headers containing tenant and token information
    """
    for i in df.Medad:
        todo = {
            "name": f"{i}",
            "source":"Automation"

        }
        data = json.dumps(todo)
        # st.write(data)
        okapi_url = st.session_state.get('okapi') or st.session_state.get('okapi_url', '')
        x = requests.post(okapi_url + "/material-types", data=data, headers=headers)

def mtypes():
    """
    Main function to create new material types
    """
    # Check if tenant information is available
    tenant = st.session_state.get('tenant') or st.session_state.get('tenant_name')
    token = st.session_state.get('token')
    okapi = st.session_state.get('okapi') or st.session_state.get('okapi_url')
    
    if not tenant or not token or not okapi:
        st.error("⚠️ Tenant connection information is missing. Please go back to Tenant page and connect again.")
        return
    
    # Upload CSV file and create dataframe
    df = upload('Material_Types')
    # Remove any rows with null values
    df.dropna(inplace=True)
    # Strip leading and trailing whitespaces from "Medad" column
    df['Medad'] = df.Medad.str.strip()
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    # GET request to get current material types
    response = requests.get(f"{okapi}/material-types", headers=headers).json()
    df_material = json_normalize(response['mtypes'])
    # Create an editable grid of the uploaded CSV data
    builder = GridOptionsBuilder.from_dataframe(df)
    builder.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
    builder.configure_pagination(enabled=True)
    builder.configure_column('Medad', editable=True)
    go = builder.build()
    grid_return = AgGrid(df, editable=True, theme='balham', gridOptions=go)

    selected_rows = grid_return['selected_rows']
    # st.write(selected_rows)
    if bool(selected_rows):
        selection = pd.DataFrame(selected_rows)
        AgGrid(selection[['Legacy System', 'Description', 'Medad']], theme='balham')
        medadlist = df_material.name.tolist()
        # Exclude already existing material types from the selection
        selection = selection[~selection['Medad'].isin(medadlist)]
        postit = st.button('Create Material Types', on_click=post_material, args=[selection, headers],)
        if postit:
            st.success('Material Types are Created')

    else:
        st.warning('Please Select Required Material Types!!')
