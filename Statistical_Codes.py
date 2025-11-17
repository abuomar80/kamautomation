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
    st.session_state['token'] = st.session_state.get('token')

if "activatebtn" not in st.session_state:
    st.session_state.activatebtn = True

def post_stat_types(df, headers, okapi):
    """
    Posts a new material type to the Okapi API
    :param df: dataframe containing the material types to be posted
    :param headers: headers containing tenant and token information
    :param okapi: Okapi URL
    """
    for i in df:
        todo = {
            "name": f"{i}",
            "source":"Automation"

        }
        data = json.dumps(todo)
        # st.write(data)
        x = requests.post(okapi + "/statistical-code-types", data=data, headers=headers)

def post_stat_codes(df, headers, okapi):
    """
    Posts a new material type to the Okapi API
    :param df: dataframe containing the material types to be posted
    :param headers: headers containing tenant and token information
    :param okapi: Okapi URL
    """
    for ind in df.index:

        response = requests.get(okapi+f'/statistical-code-types?query=(name=={df["Medad Statistical Type"][ind]})', headers=headers).json()
        typekey=response['statisticalCodeTypes'][0]['id']
        todo = {
            "code": f"{df['Medad Statistical Code'][ind]}",
            "name": f"{df['Medad Statistical Code'][ind]}",
            "statisticalCodeTypeId": f"{typekey}",
            "source": "Automation"
        }
        data = json.dumps(todo)
        requests.post(okapi + "/statistical-codes", data=data, headers=headers)
def stat_types():
    """
    Main function to create new material types
    """
    # Upload CSV file and create dataframe
    df = upload('Statistical_Codes')
    # Remove any rows with null values
    df.dropna(inplace=True)
    # Strip leading and trailing whitespaces from "Medad" column
    df['Medad Statistical Code'] = df['Medad Statistical Code'].str.strip()
    df['Medad Statistical Type'] = df['Medad Statistical Type'].str.strip()
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name")
    token = st.session_state.get("token")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url")

    if not all([tenant, token, okapi]):
        st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        st.info("Go to the Tenant page, enter connection details, click Connect, then return here.")
        return

    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}
    # GET request to get current material types
    response = requests.get(f"{okapi}/statistical-code-types", headers=headers).json()
    df_stypes = json_normalize(response['statisticalCodeTypes'])
    # Create an editable grid of the uploaded CSV data
    builder = GridOptionsBuilder.from_dataframe(df)
    builder.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
    builder.configure_pagination(enabled=True)
    builder.configure_column('Medad Statistical Code', editable=True)
    builder.configure_column('Medad Statistical Type', editable=True)
    go = builder.build()
    grid_return = AgGrid(df, editable=True, theme='balham', gridOptions=go)

    selected_rows = grid_return['selected_rows']
    # st.write(selected_rows)
    if bool(selected_rows):
        selection = pd.DataFrame(selected_rows)
        statcodesdf= pd.DataFrame(selected_rows).reset_index()
        AgGrid(selection[['Medad Statistical Type', 'Medad Statistical Code']], theme='balham')
        stypeslist = df_stypes.name.tolist()
        # Exclude already existing material types from the selection
        selection = selection[~selection['Medad Statistical Type'].isin(stypeslist)]

        df=selection.copy()
        df=df['Medad Statistical Type'].astype('str')
        df.drop_duplicates(inplace=True)



        poststypes = st.button('Create Statistical Types', on_click=post_stat_types, args=[df, headers, okapi])
        if poststypes:
            st.success('Statistical Types are Created')
            st.session_state.activatebtn = False

        postcodes = st.button('Create Statistical Codes', on_click=post_stat_codes, args=[statcodesdf, headers, okapi],disabled=st.session_state.activatebtn)
        if postcodes:
            st.success('Statistical Codes are Created')
            st.session_state.activatebtn = True





    else:
        st.warning('Please Select Required Statistical Types/Codes!!')
