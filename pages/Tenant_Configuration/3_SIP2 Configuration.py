import pandas as pd
from datetime import datetime
import streamlit as st
import json
import requests
from legacy_session_state import legacy_session_state
legacy_session_state()



hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_menu_style, unsafe_allow_html=True)
def servicepoint():
    """
    Retrieves service points from the Okapi API and normalizes the data into a pandas dataframe
    :return: pandas dataframe containing the service point information
    """
    # Get tenant and okapi with fallback to copied keys
    tenant = st.session_state.get('tenant') or st.session_state.get('tenant_name', '')
    okapi = st.session_state.get('okapi') or st.session_state.get('okapi_url', '')
    token = st.session_state.get('token')
    header = {"x-okapi-tenant": tenant, "x-okapi-token": token}
    # Endpoint for service points with a limit of 1000
    end_point_service = "service-points?limit=1000"
    url_service = f"{okapi}/{end_point_service}"
    # GET request to retrieve service points
    response = requests.get(url_service, headers=header).json()
    # Normalize the json data into a dataframe
    serivce_point = pd.json_normalize(response, record_path="servicepoints")
    return serivce_point




def sip(okapi, tenant, tokens, spoint1, df):
    now = datetime.now()
    date_time = now.strftime("%d-%m-%Y-%H%M%S")
    end_point_config = "configurations/entries?limit=1000"
    end_point_config_post = "configurations/entries"
    end_point_service = "service-points?limit=1000"

    # Get tenant and okapi with fallback to copied keys
    tenant_val = st.session_state.get('tenant') or st.session_state.get('tenant_name', '')
    okapi_val = st.session_state.get('okapi') or st.session_state.get('okapi_url', '')
    token_val = st.session_state.get('token')

    url_config = f"{okapi_val}/{end_point_config}"
    url_service = f"{okapi_val}/{end_point_service}"
    url_config_post = f"{okapi_val}/{end_point_config_post}"
    headers = {"x-okapi-tenant": f"{tenant_val}", "x-okapi-token": f"{token_val}"}
    response = requests.get(url_config, headers=headers).json()

    acsTenantConfig = pd.json_normalize(response, record_path="configs")
    acsTenantConfig = acsTenantConfig[
        acsTenantConfig["configName"] == "acsTenantConfig"
    ]

    if len(acsTenantConfig) < 1:
        headers = {"x-okapi-tenant": f"{tenant_val}", "x-okapi-token": f"{token_val}"}
        todo = {
            "module": "edge-sip2",
            "configName": "acsTenantConfig",
            "enabled": "true",
            "value": '{"supportedMessages":[{"messageName":"PATRON_STATUS_REQUEST","isSupported":"N"},{"messageName":"CHECKOUT","isSupported":"Y"},{"messageName":"CHECKIN","isSupported":"Y"},{"messageName":"BLOCK_PATRON","isSupported":"N"},{"messageName":"SC_ACS_STATUS","isSupported":"Y"},{"messageName":"LOGIN","isSupported":"Y"},{"messageName":"PATRON_INFORMATION","isSupported":"Y"},{"messageName":"END_PATRON_SESSION","isSupported":"Y"},{"messageName":"FEE_PAID","isSupported":"N"},{"messageName":"ITEM_INFORMATION","isSupported":"N"},{"messageName":"ITEM_STATUS_UPDATE","isSupported":"N"},{"messageName":"PATRON_ENABLE","isSupported":"N"},{"messageName":"HOLD","isSupported":"N"},{"messageName":"RENEW","isSupported":"N"},{"messageName":"RENEW_ALL","isSupported":"N"},{"messageName":"REQUEST_SC_ACS_RESEND","isSupported":"N"}],"statusUpdateOk":true,"offlineOk":false,"patronPasswordVerificationRequired":false}',
        }
        response = requests.post(url_config, data=json.dumps(todo), headers=headers)
    else:
        pass

    response = requests.get(url_service, headers=headers).json()
    serivce_point = pd.json_normalize(response, record_path= "servicepoints")
    serivce_point = serivce_point[["id", "name"]].reset_index()
    id_list = serivce_point.id.tolist()

    response = requests.get(url_config, headers=headers).json()
    selfCheckoutConfig = pd.json_normalize(response, record_path="configs")
    selfCheckoutConfig = selfCheckoutConfig[
        selfCheckoutConfig["configName"].str.contains("selfCheckoutConfig")
    ]
    selfCheckoutConfig["config_name_strip"] = selfCheckoutConfig.configName.str.split(
        "."
    ).str[1]

    for x in selfCheckoutConfig["config_name_strip"]:
        for i in selfCheckoutConfig["id"]:
            if x not in id_list:
                acsTenantConfig.to_csv("selfCheckoutConfig_output_before_delete.csv")
                selfCheckoutConfig = selfCheckoutConfig[
                    selfCheckoutConfig["config_name_strip"] == x
                ]
                for j in selfCheckoutConfig["id"]:
                    print(j)
                    del_url = f"{okapi_val}/{end_point_config_post}"
                    delt = requests.delete(del_url + "/" + j, headers=headers)


    headers = {"x-okapi-tenant": f"{tenant_val}", "x-okapi-token": f"{token_val}"}
    # Get service point ID from dataframe
    spoint2 = df.loc[df["name"] == spoint1, "id"].item()
    todo = {
        "module": "edge-sip2",
        "configName": f"selfCheckoutConfig.{spoint2}",
        "enabled": "true",
        "value": '{"timeoutPeriod": 5,"retriesAllowed": 3,"checkinOk": true,"checkoutOk": true,"acsRenewalPolicy": false,"libraryName":"'
        + spoint1
        + '","terminalLocation":"'
        + spoint2
        + '"}',
    }
    response = requests.post(url_config_post, data=json.dumps(todo), headers=headers)

def checkbox_disabled():
    confirm_disabled = True
    return confirm_disabled

confirm_disabled=False

# Prerequisites section with expandable instructions
with st.expander("⚠️ Prerequisites Checklist - Please Make Sure the Following is Completed Before Proceeding", expanded=False):
    st.markdown("""
    **Please ensure the following prerequisites are completed before configuring SIP2:**
    
    ✅ **Selfcheck has internet access**
    - Self-service checkout stations must have network connectivity
    - Verify internet connection is active and stable
    - Network firewall rules must allow SIP2 communication (port 6443)
    
    ✅ **Service Points already been configured**
    - At least one service point must exist in the tenant
    - Service points are required for SIP2 terminal location configuration
    - Service points can be configured in Advanced Configuration → Location tab
    - Service points will be used to map SIP2 terminals to specific locations
    
    ✅ **Institution, Campuses, Libraries and Locations already been configured**
    - Complete location hierarchy must be set up:
      - **Institution** (top level)
      - **Campus** (under institution)
      - **Library** (under campus)
      - **Location** (under library)
    - Location hierarchy can be configured in Advanced Configuration → Location tab
    - SIP2 terminals need to be associated with specific locations in the hierarchy
    """)
confirm_sip=st.checkbox('Confirm', key='confirm', disabled=confirm_disabled,on_change=checkbox_disabled)


if confirm_sip:
    st.title("Sip Configuration")
    if st.session_state.allow_tenant:
        # Get tenant and okapi with fallback to copied keys
        tenant = st.session_state.get('tenant') or st.session_state.get('tenant_name', '')
        okapi = st.session_state.get('okapi') or st.session_state.get('okapi_url', '')
        
        if not tenant or not okapi:
            st.error("⚠️ Tenant connection information is missing. Please go back to Tenant page and connect again.")
            st.info("💡 **To fix this:**\n1. Go to **Tenant** page (in sidebar)\n2. Enter **Tenant Name**, **Username**, **Password**\n3. Select **Okapi URL** from dropdown\n4. Click **Connect** button\n5. Wait for **'Connected! ✅'** success message\n6. Then return to this page")
            return
        
        if 'sc_ip' not in st.session_state:
            st.session_state.sc_ip=''
        sip2_tenants = {
                "scTenants": [
                    {
                        "scSubnet": "127.0.0.1/24",
                        "tenant": f"{tenant}",
                        "errorDetectionEnabled": True,
                        "fieldDelimiter": "|",
                        "charset": "utf-8",
                    }
                ]
            }
        sip2tenant = json.dumps(sip2_tenants, sort_keys=False, indent=4)

        sip2 = {
                "port": 6443,
                "okapiUrl": f"{okapi}",
                "tenantConfigRetrieverOptions": {
                    "scanPeriod": 300000,
                    "stores": [
                        {
                            "type": "file",
                            "format": "json",
                            "config": {"path": "sip2-tenants.conf"},
                            "optional": False,
                        }
                    ],
                },
            }

        sip2conf=json.dumps(sip2, sort_keys=False, indent=4)

        sipb="""@echo off
            java -jar edge-sip2-fat.jar -conf sip2.conf
            """


        df = servicepoint()
        listspoint = df["name"].tolist()
        st.multiselect("Select Service point", options=listspoint, key="spoint1")
        # spoint2 = df.loc[df["name"] == st.session_state.spoint1, "id"].item()

        bt1, bt2 = st.columns(2)
        with bt1:
            if "sip2click" not in st.session_state:
                st.session_state.sip2click = False
            generatesip = st.button("Generate SIP")
            if generatesip:
                st.session_state.sip2click=True
            if st.session_state.sip2click:
                for i in st.session_state.spoint1:
                    sip(okapi, tenant, st.session_state.get('token'), i, df)
                sipconfig = st.success("Sip Configured!", icon="✅")
                st.link_button('Download Java','https://download.oracle.com/java/21/latest/jdk-21_windows-x64_bin.exe')
                st.link_button('Download Jar File', 'https://github.com/medadadmin/sip2-edge/releases/download/Sip2-Edge-Juniper/edge-sip2-fat.jar')
                st.download_button('Download sip2_tenants.conf', sip2tenant, file_name='sip2-tenants.conf')
                st.download_button('Download sip2.conf', sip2conf, file_name='sip2.conf')
                st.download_button('Download Sip2 Bat File', sipb, file_name='sip2.bat')

    else:
        st.warning("Please Connect to Tenant First.")
