import requests
import json
import streamlit as st
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


def columns_config():
    # Get tenant connection details with fallbacks
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name")
    token = st.session_state.get("token")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url")

    if not all([tenant, token, okapi]):
        st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        st.info("Go to the Tenant page, enter connection details, click Connect, then return here.")
        return

    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}

    entries_endpoint = "/configurations/entries"

    # CHECK IF USER DISPLAY_COL EXISTS
    entries = requests.get(f'{okapi}{entries_endpoint}?query=(name==DISPLAY_COLUMNS)', headers=headers)


    # GET ALL CLASSIFICATION TYPES
    response = requests.get(f'{okapi}/classification-types', headers=headers).json()
    # ?query=cql.allRecords=1%20sortby%20name&limit=2000

    if not response["classificationTypes"]:
        st.warning("No classification types found.")
    else:
        types = []
        for i in response['classificationTypes']:
            types.append(i['name'])

        option = st.selectbox(
        'Classification Types:',
        (types))
        create_column = st.button("Create")

        if create_column:
            if option:
                class_id = ""
                # GET THE ID OF CHOSEN CLASSIFICATION TYPE
                for j in response['classificationTypes']:
                    if j['name'] == option:
                        class_id = j['id']

                config_res = requests.get(f'{okapi}{entries_endpoint}?query=(module== "CONFIGURATION_COLUMNS")', headers=headers).json()
                # st.write(config_res)
                data = {
                    "module": "CONFIGURATION_COLUMNS",
                    "configName": "DISPLAY_COLUMNS",
                    "value": "{\"cover\":true,\"publishers\":true,\"title\":true,\"indexTitle\":false,\"callNumber\":{\"classificationIdentifierType\":\"" + class_id + "\"},\"contributors\":false,\"publicationDate\":true,\"relation\":false}",
                }
                # if exists ,get Id and put, if not post without id
                if not config_res['configs']:
                    # CREATE NEW
                    res = requests.post(f'{okapi}{entries_endpoint}', data=json.dumps(data), headers=headers)
                    # st.write(res.content)
                    st.success('User (DISPLAY_COLUMNS) added successfully.')

                else:
                    config_id = config_res['configs'][0]['id']
                    res = requests.put(f'{okapi}{entries_endpoint}', data=json.dumps(data),
                                        headers=headers)
                    # st.write(res.content)
                    st.success('User (DISPLAY_COLUMNS) Updated successfully.')


