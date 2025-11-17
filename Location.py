import streamlit as st
from Service_points import create_sp, create_institutions, create_campuses, create_libraries, create_locations
from Upload import upload
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
from legacy_session_state import legacy_session_state

legacy_session_state()

# Initialize tenant-related session state variables if not set
# Check both widget-bound keys and copied keys (from form submission)
if 'tenant' not in st.session_state or not st.session_state.get('tenant'):
    st.session_state['tenant'] = st.session_state.get('tenant_name', '')
if 'okapi' not in st.session_state or not st.session_state.get('okapi'):
    st.session_state['okapi'] = st.session_state.get('okapi_url', '')
if 'token' not in st.session_state:
    st.session_state['token'] = st.session_state.get('token')

def loc():

    st.title("Location")
    
    # Get tenant connection details with fallbacks
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name")
    token = st.session_state.get("token")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url")

    if not all([tenant, token, okapi]):
        st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        st.info("Go to the Tenant page, enter connection details, click Connect, then return here.")
        return
    
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    file = upload('Location')

    builder = GridOptionsBuilder.from_dataframe(file)
    builder.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
    builder.configure_pagination(enabled=True)

    myList = ['ServicePoints name', 'CampusNames', 'LibrariesName', 'LocationsName', 'InstitutionsName']
    for item in myList:
        builder.configure_column(item, editable=True)
    go = builder.build()
    grid_return = AgGrid(file, editable=True, theme='balham', gridOptions=go)

    selected_rows = grid_return['selected_rows']

    if bool(selected_rows):
        selection = pd.DataFrame(selected_rows)

        createLoc = st.button("Create locations")
        if createLoc:
            # CREATE EMPTY DICTIONARIES TO STORE DATA IN
            locations = {}
            locations_code = {}
            locations_lib = {}
            locations_camp = {}
            locations_inst = {}

            error_messages = []  # Track errors for summary
            with st.spinner(f'Creating Selected Locations..'):
                for index, row in selection.iterrows():
                    sp_name = str(row["ServicePoints name"]).strip()
                    sp_code = str(row["ServicePoints Codes"]).strip()
                    institution_name = str(row["InstitutionsName"]).strip()
                    institution_code = str(row["InstitutionsCodes"]).strip()
                    campus_name = str(row["CampusNames"]).strip()
                    campus_code = str(row["CampusCodes"]).strip()
                    library_name = str(row["LibrariesName"]).strip()
                    library_code = str(row["LibrariesCodes"]).strip()
                    location_name = str(row["LocationsName"]).strip()
                    location_code = str(row["LocationsCodes"]).strip()

                    name_result = requests.get(
                        f"{okapi}/service-points?query=(name = {sp_name})",
                        headers=headers,
                    ).json()
                    code_result = requests.get(
                        f"{okapi}/service-points?query=(code = {sp_code})",
                        headers=headers,
                    ).json()
                    empty = []

                    # Create service point and handle response (already exists = success, no message)
                    success, error_msg = create_sp(sp_name, sp_code, sp_name, sp_name, okapi, tenant, token)
                    if not success and error_msg:
                        error_messages.append(error_msg)
                        st.warning(f"⚠️ Service Point '{sp_name}': {error_msg}")



                    result = requests.get(
                        f"{okapi}/location-units/institutions?query=(name=={institution_name})",
                        headers=headers).json()

                    if result['locinsts'] == empty:
                        success, error_msg = create_institutions(institution_name, institution_code, okapi, tenant, token)
                        if not success and error_msg:
                            st.warning(f"⚠️ Institution '{institution_name}': {error_msg}")


                    # GET INSTITUTION ID
                    result = requests.get(
                        f"{okapi}/location-units/institutions?query=(name=={institution_name})",
                        headers=headers).json()
                    insID = result['locinsts'][0]['id']


                    result2 = requests.get(
                        f"{okapi}/location-units/campuses?query=(name=={campus_name})",
                        headers=headers).json()

                    if result2['loccamps'] == empty:
                        success, error_msg = create_campuses(campus_name, campus_code, insID, okapi, tenant, token)
                        if not success and error_msg:
                            st.warning(f"⚠️ Campus '{campus_name}': {error_msg}")


                    # CREATING LIBRARIES
                    result = requests.get(
                        f"{okapi}/location-units/campuses?query=(name=={campus_name})",
                        headers=headers).json()

                    campusID = result['loccamps'][0]['id']

                    result2 = requests.get(
                        f"{okapi}/location-units/libraries?query=(name=={library_name})",
                        headers=headers).json()

                    if result2['loclibs'] == empty:
                        success, error_msg = create_libraries(library_name, library_code, campusID, okapi, tenant, token)
                        if not success and error_msg:
                            st.warning(f"⚠️ Library '{library_name}': {error_msg}")

                    # else:
                        # st.warning(f'Libary ({row["LibrariesName"]}) already exists.')

                    # FILL LOCATION DICTIONARY
                    result = requests.get(
                        f"{okapi}/service-points?query=(name=={sp_name})",
                        headers=headers).json()

                    servicepoints = result.get('servicepoints') or []
                    if not servicepoints:
                        warning_msg = (
                            f"❌ No service point found for name '{sp_name}'. "
                            "Skipping this location entry."
                        )
                        st.warning(warning_msg)
                        error_messages.append(warning_msg)
                        continue

                    spid = servicepoints[0].get('id')
                    if not spid:
                        warning_msg = (
                            f"❌ Service point '{sp_name}' is missing an ID. "
                            "Skipping this location entry."
                        )
                        st.warning(warning_msg)
                        error_messages.append(warning_msg)
                        continue
                    if locations.get(location_name) is not None:
                        locations_code[location_name].append(location_code)
                        locations_lib[location_name].append(library_name)
                        locations_camp[location_name].append(campusID)
                        locations_inst[location_name].append(insID)

                        if spid not in locations[location_name]:
                            locations[location_name].append(spid)

                    else:
                        locations[location_name] = [spid]
                        locations_code[location_name] = [location_code]
                        locations_lib[location_name] = [library_name]
                        locations_camp[location_name] = [campusID]
                        locations_inst[location_name] = [insID]

                for key in locations:
                    for i in range(0, len(locations_code[key])):
                        code = locations_code[key][i]
                        camp_id = locations_camp[key][i]
                        inst_id = locations_inst[key][i]

                        # GET LIBRARY ID
                        res = requests.get(
                            f"{okapi}/location-units/libraries?query=(name=={locations_lib[key][i]})",
                            headers=headers,
                        ).json()
                        libraries = res.get("loclibs") or []
                        if not libraries:
                            warn = (
                                f"❌ No library found for name '{locations_lib[key][i]}'. "
                                "Skipping this location entry."
                            )
                            st.warning(warn)
                            error_messages.append(warn)
                            continue

                        lib_ID = libraries[0].get("id")
                        if not lib_ID:
                            warn = (
                                f"❌ Library record for '{locations_lib[key][i]}' is missing an ID. "
                                "Skipping this location entry."
                            )
                            st.warning(warn)
                            error_messages.append(warn)
                            continue

                        success, error_msg = create_locations(key, code, key, inst_id, camp_id, lib_ID, locations[key][0], locations[key], okapi, tenant, token)
                        if not success and error_msg:
                            error_messages.append(f"Location '{key}': {error_msg}")
                            st.warning(f"⚠️ Location '{key}': {error_msg}")

            # Summary message
            if error_messages:
                st.success("✅ Locations and Service Points processed!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
            else:
                st.success("✅ Locations and Service Points have been created successfully!")
                st.info("💡 All items were created or already existed.")
            st.session_state['allow_calendar'] = True