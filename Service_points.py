import streamlit as st
import requests
import json
import time

from legacy_session_state import legacy_session_state
from connection_manager import safe_request, get_connection_details

# Get session state of legacy session
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

def create_sp(sp_name,sp_code,disp_name,desc,okapi,tenant,token, max_retries=3):
    spurl=f'{okapi}/service-points'
    to_do= {
  "name" : f"{sp_name}",
  "code" : f"{sp_code}",
  "discoveryDisplayName" : f"{disp_name}",
  "description" : f"{desc}"

    }
    
    # Use connection_manager for automatic retry and token refresh
    response = safe_request('POST', spurl, json_data=to_do, max_retries=max_retries)
    
    if response is None:
        return False, f"Failed to create Service Point '{sp_name}' after {max_retries} attempts", False
    
    # Parse response and show user-friendly message
    if response.status_code == 201:
        return True, None, True  # Success - created (newly created)
    elif response.status_code == 422:
        try:
            error_data = response.json()
            if 'errors' in error_data and len(error_data['errors']) > 0:
                error_msg = error_data['errors'][0].get('message', 'Unknown error')
                if 'Service Point Exists' in error_msg or 'already exists' in error_msg.lower():
                    return True, None, False  # Already exists = success (no error, not newly created)
                return False, error_msg, False
        except:
            pass
        # 422 with no parseable error - assume it's a duplicate (exists)
        return True, None, False
    else:
        try:
            error_data = response.json()
            if 'errors' in error_data:
                return False, error_data['errors'][0].get('message', 'Unknown error'), False
        except:
            pass
        return False, f"Error creating Service Point '{sp_name}' (Status: {response.status_code})", False
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

def create_locations(locationname, locationcode, displayname, instuuid, campusuuid, libuuid, spprimaryuuid, splistuuid,okapi,tenant,token, max_retries=3):
    locurl=f'{okapi}/locations'

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

    # Use connection_manager for automatic retry and token refresh
    response = safe_request('POST', locurl, json_data=to_do, max_retries=max_retries)
    
    if response is None:
        return False, f"Failed to create location '{locationname}' after {max_retries} attempts", False
    if response.status_code == 201:
        return True, None, True  # Success - created (newly created)
    elif response.status_code == 422:
        try:
            error_data = response.json()
            if 'errors' in error_data:
                error_msg = error_data['errors'][0].get('message', 'Location already exists')
                if 'already exists' in error_msg.lower() or 'exists' in error_msg.lower():
                    return True, None, False  # Already exists = success (no error, not newly created)
                return False, error_msg, False
        except:
            pass
        # 422 with no parseable error - assume it's a duplicate (exists)
        return True, None, False
    else:
        try:
            error_data = response.json()
            if 'errors' in error_data:
                return False, error_data['errors'][0].get('message', 'Unknown error'), False
        except:
            pass
        return False, f"Error creating location (Status: {response.status_code})", False

def delete_location(location_id, okapi, tenant, token):
    """Delete a location by ID"""
    locurl = f'{okapi}/locations/{location_id}'
    
    try:
        response = safe_request('DELETE', locurl, max_retries=3)
        if response is None:
            return False, "Failed to delete location after retries"
        
        if response.status_code == 204:
            return True, None  # Success - deleted
        elif response.status_code == 404:
            return True, None  # Already deleted or doesn't exist
        else:
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    return False, error_data['errors'][0].get('message', 'Unknown error')
            except:
                pass
            return False, f"Error deleting location (Status: {response.status_code})"
    except Exception as e:
        return False, f"Exception deleting location: {str(e)}"

def delete_service_point(sp_id, okapi, tenant, token):
    """Delete a service point by ID"""
    spurl = f'{okapi}/service-points/{sp_id}'
    
    try:
        response = safe_request('DELETE', spurl, max_retries=3)
        if response is None:
            return False, "Failed to delete service point after retries"
        
        if response.status_code == 204:
            return True, None  # Success - deleted
        elif response.status_code == 404:
            return True, None  # Already deleted or doesn't exist
        else:
            try:
                error_data = response.json()
                if 'errors' in error_data:
                    return False, error_data['errors'][0].get('message', 'Unknown error')
            except:
                pass
            return False, f"Error deleting service point (Status: {response.status_code})"
    except Exception as e:
        return False, f"Exception deleting service point: {str(e)}"

def get_location_by_code(location_code, okapi, tenant, token):
    """Get location ID by code"""
    locurl = f'{okapi}/locations?query=(code=={location_code})'
    
    try:
        response = safe_request('GET', locurl, max_retries=3)
        if response and response.status_code == 200:
            data = response.json()
            locations = data.get('locations', [])
            if locations:
                return locations[0].get('id')
        return None
    except:
        return None

def get_location_details_by_code(location_code, okapi, tenant, token):
    """Get full location details by code (ID, name, creation date)"""
    locurl = f'{okapi}/locations?query=(code=={location_code})'
    
    try:
        response = safe_request('GET', locurl, max_retries=3)
        if response and response.status_code == 200:
            data = response.json()
            locations = data.get('locations', [])
            if locations:
                loc = locations[0]
                return {
                    'id': loc.get('id'),
                    'name': loc.get('name'),
                    'code': loc.get('code'),
                    'metadata': loc.get('metadata', {})
                }
        return None
    except:
        return None

def get_service_point_by_code(sp_code, okapi, tenant, token):
    """Get service point ID by code"""
    spurl = f'{okapi}/service-points?query=(code=={sp_code})'
    
    try:
        response = safe_request('GET', spurl, max_retries=3)
        if response and response.status_code == 200:
            data = response.json()
            service_points = data.get('servicepoints', [])
            if service_points:
                return service_points[0].get('id')
        return None
    except:
        return None

def get_service_point_details_by_code(sp_code, okapi, tenant, token):
    """Get full service point details by code (ID, name, creation date)"""
    spurl = f'{okapi}/service-points?query=(code=={sp_code})'
    
    try:
        response = safe_request('GET', spurl, max_retries=3)
        if response and response.status_code == 200:
            data = response.json()
            service_points = data.get('servicepoints', [])
            if service_points:
                sp = service_points[0]
                return {
                    'id': sp.get('id'),
                    'name': sp.get('name'),
                    'code': sp.get('code'),
                    'metadata': sp.get('metadata', {})
                }
        return None
    except:
        return None