import streamlit as st
import requests
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

def create_sp(sp_name,sp_code,disp_name,desc,okapi,tenant,token):
    spurl=f'{okapi}/service-points'
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    to_do= {
  "name" : f"{sp_name}",
  "code" : f"{sp_code}",
  "discoveryDisplayName" : f"{disp_name}",
  "description" : f"{desc}"

    }
    response = requests.post(spurl, data=json.dumps(to_do), headers=headers)
    
    # Parse response and show user-friendly message
    if response.status_code == 201:
        return True, None  # Success - created
    elif response.status_code == 422:
        try:
            error_data = response.json()
            if 'errors' in error_data and len(error_data['errors']) > 0:
                error_msg = error_data['errors'][0].get('message', 'Unknown error')
                if 'Service Point Exists' in error_msg or 'already exists' in error_msg.lower():
                    return True, None  # Already exists = success (no error)
                return False, error_msg
        except:
            pass
        # 422 with no parseable error - assume it's a duplicate (exists)
        return True, None
    else:
        try:
            error_data = response.json()
            if 'errors' in error_data:
                return False, error_data['errors'][0].get('message', 'Unknown error')
        except:
            pass
        return False, f"Error creating Service Point '{sp_name}' (Status: {response.status_code})"
def create_institutions(inistname,insticode,okapi,tenant,token):
    insurl=f'{okapi}/location-units/institutions'
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    to_do={
  "name" : f"{inistname}",
  "code" : f"{insticode}"

}
    response = requests.post(insurl, data=json.dumps(to_do), headers=headers)
    if response.status_code not in [201, 422]:  # 422 means already exists, which is OK
        try:
            error_data = response.json()
            if 'errors' in error_data:
                return False, error_data['errors'][0].get('message', 'Unknown error')
        except:
            pass
    return True, None

def create_campuses(campusname, campuscode, instuuid,okapi,tenant,token):
    campusurl=f'{okapi}/location-units/campuses'
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    to_do={
  "name" : f"{campusname}",
  "code" : f"{campuscode}",
  "institutionId" : f"{instuuid}",

}
    response = requests.post(campusurl, data=json.dumps(to_do), headers=headers)
    if response.status_code not in [201, 422]:  # 422 means already exists, which is OK
        try:
            error_data = response.json()
            if 'errors' in error_data:
                return False, error_data['errors'][0].get('message', 'Unknown error')
        except:
            pass
    return True, None


def create_libraries(libraryname, librarycode, campusuuid,okapi,tenant,token):
    liburl=f'{okapi}/location-units/libraries'
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    to_do={
  "name" : f"{libraryname}",
  "code" : f"{librarycode}",
  "campusId" : f"{campusuuid}"
}
    response = requests.post(liburl, data=json.dumps(to_do), headers=headers)
    if response.status_code not in [201, 422]:  # 422 means already exists, which is OK
        try:
            error_data = response.json()
            if 'errors' in error_data:
                return False, error_data['errors'][0].get('message', 'Unknown error')
        except:
            pass
    return True, None

def create_locations(locationname, locationcode, displayname, instuuid, campusuuid, libuuid, spprimaryuuid, splistuuid,okapi,tenant,token):
    locurl=f'{okapi}/locations'
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}


    to_do={

  "name" : f"{locationname}",
  "code" : f"{locationcode}",
  "discoveryDisplayName" : f"{displayname}",
  "isActive" : True,
  "institutionId" : f"{instuuid}",
  "campusId" : f"{campusuuid}",
  "libraryId" : f"{libuuid}",
  # "details" : { },
  "primaryServicePoint" : f"{spprimaryuuid}",
  "servicePointIds" : splistuuid,

}

    response = requests.post(locurl, data=json.dumps(to_do), headers=headers)
    if response.status_code == 201:
        return True, None  # Success - created
    elif response.status_code == 422:
        try:
            error_data = response.json()
            if 'errors' in error_data:
                error_msg = error_data['errors'][0].get('message', 'Location already exists')
                if 'already exists' in error_msg.lower() or 'exists' in error_msg.lower():
                    return True, None  # Already exists = success (no error)
                return False, error_msg
        except:
            pass
        # 422 with no parseable error - assume it's a duplicate (exists)
        return True, None
    else:
        try:
            error_data = response.json()
            if 'errors' in error_data:
                return False, error_data['errors'][0].get('message', 'Unknown error')
        except:
            pass
        return False, f"Error creating location (Status: {response.status_code})"
