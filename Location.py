import streamlit as st
from Service_points import create_sp, create_institutions, create_campuses, create_libraries, create_locations
from Upload import upload
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
from legacy_session_state import legacy_session_state

legacy_session_state()

def loc():

    st.title("Location")
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
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

                    name_result = requests.get(f'{st.session_state.okapi}/service-points?query=(name = {row["ServicePoints name"]})', headers=headers).json()
                    code_result = requests.get(f'{st.session_state.okapi}/service-points?query=(code = {row["ServicePoints Codes"]})', headers=headers).json()
                    empty = []

                    # Create service point and handle response (already exists = success, no message)
                    success, error_msg = create_sp(row["ServicePoints name"], row["ServicePoints Codes"], row["ServicePoints name"],
                              row["ServicePoints name"])
                    if not success and error_msg:
                        error_messages.append(error_msg)
                        st.warning(f"⚠️ Service Point '{row['ServicePoints name']}': {error_msg}")



                    result = requests.get(
                        f'{st.session_state.okapi}/location-units/institutions?query=(name=={row["InstitutionsName"]})',
                        headers=headers).json()

                    if result['locinsts'] == empty:
                        success, error_msg = create_institutions(row["InstitutionsName"], row["InstitutionsCodes"])
                        if not success and error_msg:
                            st.warning(f"⚠️ Institution '{row['InstitutionsName']}': {error_msg}")


                    # GET INSTITUTION ID
                    result = requests.get(
                        f'{st.session_state.okapi}/location-units/institutions?query=(name=={row["InstitutionsName"]})',
                        headers=headers).json()
                    insID = result['locinsts'][0]['id']


                    result2 = requests.get(
                        f'{st.session_state.okapi}/location-units/campuses?query=(name=={row["CampusNames"]})',
                        headers=headers).json()

                    if result2['loccamps'] == empty:
                        success, error_msg = create_campuses(row["CampusNames"], row["CampusCodes"], insID)
                        if not success and error_msg:
                            st.warning(f"⚠️ Campus '{row['CampusNames']}': {error_msg}")


                    # CREATING LIBRARIES
                    result = requests.get(
                        f'{st.session_state.okapi}/location-units/campuses?query=(name=={row["CampusNames"]})',
                        headers=headers).json()

                    campusID = result['loccamps'][0]['id']

                    result2 = requests.get(
                        f'{st.session_state.okapi}/location-units/libraries?query=(name=={row["LibrariesName"]})',
                        headers=headers).json()

                    if result2['loclibs'] == empty:
                        success, error_msg = create_libraries(row['LibrariesName'], row['LibrariesCodes'], campusID)
                        if not success and error_msg:
                            st.warning(f"⚠️ Library '{row['LibrariesName']}': {error_msg}")

                    # else:
                        # st.warning(f'Libary ({row["LibrariesName"]}) already exists.')

                    # FILL LOCATION DICTIONARY
                    result = requests.get(
                        f'{st.session_state.okapi}/service-points?query=(name=={row["ServicePoints name"]})',
                        headers=headers).json()

                    servicepoints = result.get('servicepoints') or []
                    if not servicepoints:
                        warning_msg = (
                            f"❌ No service point found for name '{row['ServicePoints name']}'. "
                            "Skipping this location entry."
                        )
                        st.warning(warning_msg)
                        error_messages.append(warning_msg)
                        continue

                    spid = servicepoints[0].get('id')
                    if not spid:
                        warning_msg = (
                            f"❌ Service point '{row['ServicePoints name']}' is missing an ID. "
                            "Skipping this location entry."
                        )
                        st.warning(warning_msg)
                        error_messages.append(warning_msg)
                        continue
                    if locations.get(row['LocationsName']) is not None:
                        locations_code[row['LocationsName']].append(row['LocationsCodes'])
                        locations_lib[row['LocationsName']].append(row['LibrariesName'])
                        locations_camp[row['LocationsName']].append(campusID)
                        locations_inst[row['LocationsName']].append(insID)

                        if spid not in locations[row['LocationsName']]:
                            locations[row['LocationsName']].append(spid)

                    else:
                        locations[row['LocationsName']] = [spid]
                        locations_code[row['LocationsName']] = [row['LocationsCodes']]
                        locations_lib[row['LocationsName']] = [row['LibrariesName']]
                        locations_camp[row['LocationsName']] = [campusID]
                        locations_inst[row['LocationsName']] = [insID]

                for key in locations:
                    for i in range(0, len(locations_code[key])):
                        code = locations_code[key][i]
                        camp_id = locations_camp[key][i]
                        inst_id = locations_inst[key][i]

                        # GET LIBRARY ID
                        res = requests.get(f'{st.session_state.okapi}/location-units/libraries?query=(name=={locations_lib[key][i]})',
                                           headers=headers).json()
                        lib_ID = res['loclibs'][0]['id']

                        success, error_msg = create_locations(key, code, key, inst_id, camp_id, lib_ID, locations[key][0], locations[key])
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