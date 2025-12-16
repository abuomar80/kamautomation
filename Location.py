import streamlit as st
from Service_points import (
    create_sp, create_institutions, create_campuses, create_libraries, create_locations
)
from Upload import upload
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
from legacy_session_state import legacy_session_state
from connection_manager import get_session, make_request_with_retry, periodic_connection_check, validate_connection, safe_request
from translation_helper import create_translation_for_entity
import time
import json
import datetime

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

        createLoc = st.button("Create locations", type="primary")
        
        if createLoc:
            # CREATE EMPTY DICTIONARIES TO STORE DATA IN
            locations = {}
            locations_code = {}
            locations_lib = {}
            locations_camp = {}
            locations_inst = {}
            
            # Track translation data
            location_translations = {}  # {location_code: arabic_name}
            translation_success_count = 0
            translation_failure_count = 0

            error_messages = []  # Track errors for summary
            total_rows = len(selection)
            
            # Create progress bar and status
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Track newly created items for this session
            session_created_locations = []
            session_created_service_points = []
            
            # Connection keep-alive: Create a session using connection_manager
            session = get_session()
            if not session:
                st.error("⚠️ Failed to create session. Please check your connection details.")
                progress_bar.empty()
                status_text.empty()
                return
            
            # Validate initial connection
            is_valid, current_token = validate_connection(session, okapi, tenant, token)
            if not is_valid:
                st.error("⚠️ Initial connection validation failed. Please check your credentials and reconnect.")
                progress_bar.empty()
                status_text.empty()
                return
            
            token = current_token  # Update token if refreshed
            headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
            
            try:
                for idx, (index, row) in enumerate(selection.iterrows()):
                    # Update progress
                    progress = (idx + 1) / total_rows
                    progress_bar.progress(progress)
                    status_text.text(f"Processing row {idx + 1} of {total_rows}: Creating service points and locations...")
                    
                    # Keep connection alive with periodic validation and refresh
                    if idx > 0 and idx % 25 == 0:  # Check more frequently (every 25 rows)
                        if not periodic_connection_check(session, check_interval=25):
                            st.error(f"⚠️ Connection lost at row {idx + 1}. Please reconnect to tenant.")
                            st.info(f"💡 Processed {idx} rows before connection issue.")
                            break
                        # Update token from session state in case it was refreshed
                        token = st.session_state.get('token')
                        headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
                        session.headers.update(headers)
                    
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
                    
                    # Read Arabic translation columns (optional)
                    institution_name_ar = str(row.get("InstitutionsName_AR", "")).strip() if pd.notna(row.get("InstitutionsName_AR")) else ""
                    campus_name_ar = str(row.get("CampusNames_AR", "")).strip() if pd.notna(row.get("CampusNames_AR")) else ""
                    library_name_ar = str(row.get("LibrariesName_AR", "")).strip() if pd.notna(row.get("LibrariesName_AR")) else ""
                    location_name_ar = str(row.get("LocationsName_AR", "")).strip() if pd.notna(row.get("LocationsName_AR")) else ""
                    
                    # Store location translation for later use
                    if location_name_ar:
                        location_translations[location_code] = location_name_ar

                    # Use retry logic for API calls
                    try:
                        name_response = make_request_with_retry(session, 'GET', f"{okapi}/service-points?query=(name = {sp_name})")
                        if name_response is None:
                            error_messages.append(f"Failed to query service point '{sp_name}' after retries")
                            continue
                        name_result = name_response.json()
                    except Exception as e:
                        error_messages.append(f"Error querying service point '{sp_name}': {str(e)}")
                        continue
                    
                    try:
                        code_response = make_request_with_retry(session, 'GET', f"{okapi}/service-points?query=(code = {sp_code})")
                        if code_response is None:
                            error_messages.append(f"Failed to query service point code '{sp_code}' after retries")
                            continue
                        code_result = code_response.json()
                    except Exception as e:
                        error_messages.append(f"Error querying service point code '{sp_code}': {str(e)}")
                        continue
                    empty = []

                    # Create service point and handle response (already exists = success, no message)
                    success, error_msg, was_created = create_sp(sp_name, sp_code, sp_name, sp_name, okapi, tenant, token)
                    if success and was_created:
                        # Track newly created service point
                        if sp_code not in session_created_service_points and sp_code not in st.session_state.get('created_service_points', []):
                            session_created_service_points.append(sp_code)
                    if not success and error_msg:
                        error_messages.append(error_msg)
                        st.warning(f"⚠️ Service Point '{sp_name}': {error_msg}")



                    try:
                        result_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/institutions?query=(name=={institution_name})")
                        if result_response is None:
                            error_messages.append(f"Failed to query institution '{institution_name}' after retries")
                            continue
                        result = result_response.json()
                    except Exception as e:
                        error_messages.append(f"Error querying institution '{institution_name}': {str(e)}")
                        continue

                    if result.get('locinsts') == empty:
                        success, error_msg = create_institutions(institution_name, institution_code, okapi, tenant, token)
                        if not success and error_msg:
                            st.warning(f"⚠️ Institution '{institution_name}': {error_msg}")

                    # GET INSTITUTION ID AND CREATE TRANSLATION
                    try:
                        result_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/institutions?query=(name=={institution_name})")
                        if result_response is None or not result_response.json().get('locinsts'):
                            error_messages.append(f"Institution '{institution_name}' not found after creation")
                            continue
                        result = result_response.json()
                        insID = result['locinsts'][0]['id']
                        
                        # Create translation if Arabic name provided
                        if institution_name_ar:
                            trans_success, trans_error = create_translation_for_entity(
                                entity_id=insID,
                                english_name=institution_name,
                                arabic_name=institution_name_ar,
                                entity_type='INSTITUTION',
                                okapi=okapi,
                                tenant=tenant,
                                token=token
                            )
                            if trans_success:
                                translation_success_count += 1
                            else:
                                translation_failure_count += 1
                                if trans_error:
                                    error_messages.append(f"Translation for institution '{institution_name}': {trans_error}")
                    except Exception as e:
                        error_messages.append(f"Error getting institution ID for '{institution_name}': {str(e)}")
                        continue

                    try:
                        result2_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/campuses?query=(name=={campus_name})")
                        if result2_response is None:
                            error_messages.append(f"Failed to query campus '{campus_name}' after retries")
                            continue
                        result2 = result2_response.json()
                    except Exception as e:
                        error_messages.append(f"Error querying campus '{campus_name}': {str(e)}")
                        continue

                    if result2.get('loccamps') == empty:
                        success, error_msg = create_campuses(campus_name, campus_code, insID, okapi, tenant, token)
                        if not success and error_msg:
                            st.warning(f"⚠️ Campus '{campus_name}': {error_msg}")

                    # GET CAMPUS ID AND CREATE TRANSLATION
                    try:
                        result_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/campuses?query=(name=={campus_name})")
                        if result_response is None or not result_response.json().get('loccamps'):
                            error_messages.append(f"Campus '{campus_name}' not found after creation")
                            continue
                        result = result_response.json()
                        campusID = result['loccamps'][0]['id']
                        
                        # Create translation if Arabic name provided
                        if campus_name_ar:
                            trans_success, trans_error = create_translation_for_entity(
                                entity_id=campusID,
                                english_name=campus_name,
                                arabic_name=campus_name_ar,
                                entity_type='CAMPUS',
                                okapi=okapi,
                                tenant=tenant,
                                token=token
                            )
                            if trans_success:
                                translation_success_count += 1
                            else:
                                translation_failure_count += 1
                                if trans_error:
                                    error_messages.append(f"Translation for campus '{campus_name}': {trans_error}")
                    except Exception as e:
                        error_messages.append(f"Error getting campus ID for '{campus_name}': {str(e)}")
                        continue

                    try:
                        result2_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/libraries?query=(name=={library_name})")
                        if result2_response is None:
                            error_messages.append(f"Failed to query library '{library_name}' after retries")
                            continue
                        result2 = result2_response.json()
                    except Exception as e:
                        error_messages.append(f"Error querying library '{library_name}': {str(e)}")
                        continue

                    if result2.get('loclibs') == empty:
                        success, error_msg = create_libraries(library_name, library_code, campusID, okapi, tenant, token)
                        if not success and error_msg:
                            st.warning(f"⚠️ Library '{library_name}': {error_msg}")
                        
                        # Create translation if library was just created and Arabic name provided
                        if success and library_name_ar:
                            # Need to get library ID
                            try:
                                lib_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/libraries?query=(name=={library_name})")
                                if lib_response and lib_response.json().get('loclibs'):
                                    lib_data = lib_response.json()
                                    lib_id = lib_data['loclibs'][0]['id']
                                    
                                    trans_success, trans_error = create_translation_for_entity(
                                        entity_id=lib_id,
                                        english_name=library_name,
                                        arabic_name=library_name_ar,
                                        entity_type='LIBRARY',
                                        okapi=okapi,
                                        tenant=tenant,
                                        token=token
                                    )
                                    if trans_success:
                                        translation_success_count += 1
                                    else:
                                        translation_failure_count += 1
                                        if trans_error:
                                            error_messages.append(f"Translation for library '{library_name}': {trans_error}")
                            except Exception as e:
                                error_messages.append(f"Error creating translation for library '{library_name}': {str(e)}")

                    # FILL LOCATION DICTIONARY
                    try:
                        result_response = make_request_with_retry(session, 'GET', f"{okapi}/service-points?query=(name=={sp_name})")
                        if result_response is None:
                            error_messages.append(f"Failed to query service point '{sp_name}' for location creation")
                            continue
                        result = result_response.json()
                    except Exception as e:
                        error_messages.append(f"Error querying service point '{sp_name}' for location: {str(e)}")
                        continue

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

                # Update progress for location creation phase
                status_text.text("Creating locations...")
                location_keys = list(locations.keys())
                total_locations = len(location_keys)
                
                for loc_idx, key in enumerate(location_keys):
                    progress = (total_rows + loc_idx + 1) / (total_rows + total_locations)
                    progress_bar.progress(min(progress, 1.0))
                    status_text.text(f"Creating location {loc_idx + 1} of {total_locations}: {key}...")
                    
                    for i in range(0, len(locations_code[key])):
                        code = locations_code[key][i]
                        camp_id = locations_camp[key][i]
                        inst_id = locations_inst[key][i]

                        # GET LIBRARY ID
                        try:
                            res_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/libraries?query=(name=={locations_lib[key][i]})")
                            if res_response is None:
                                warn = f"Failed to query library '{locations_lib[key][i]}' after retries"
                                st.warning(warn)
                                error_messages.append(warn)
                                continue
                            res = res_response.json()
                        except Exception as e:
                            warn = f"Error querying library '{locations_lib[key][i]}': {str(e)}"
                            st.warning(warn)
                            error_messages.append(warn)
                            continue
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

                        success, error_msg, was_created = create_locations(key, code, key, inst_id, camp_id, lib_ID, locations[key][0], locations[key], okapi, tenant, token)
                        if success and was_created:
                            # Track newly created location
                            if code not in session_created_locations and code not in st.session_state.get('created_locations', []):
                                session_created_locations.append(code)
                            
                            # Create translation for location if Arabic name provided for this specific location code
                            if code in location_translations:
                                location_ar = location_translations[code]
                                try:
                                    # Get location ID
                                    loc_response = make_request_with_retry(session, 'GET', f"{okapi}/locations?query=(code=={code})")
                                    if loc_response and loc_response.json().get('locations'):
                                        loc_data = loc_response.json()
                                        loc_id = loc_data['locations'][0]['id']
                                        
                                        trans_success, trans_error = create_translation_for_entity(
                                            entity_id=loc_id,
                                            english_name=key,
                                            arabic_name=location_ar,
                                            entity_type='LOCATION',
                                            okapi=okapi,
                                            tenant=tenant,
                                            token=token
                                        )
                                        if trans_success:
                                            translation_success_count += 1
                                        else:
                                            translation_failure_count += 1
                                            if trans_error:
                                                error_messages.append(f"Translation for location '{key}': {trans_error}")
                                except Exception as e:
                                    error_messages.append(f"Error creating translation for location '{key}': {str(e)}")
                        if not success and error_msg:
                            error_messages.append(f"Location '{key}': {error_msg}")
                            st.warning(f"⚠️ Location '{key}': {error_msg}")
                    
                    # Small delay to prevent overwhelming the API
                    time.sleep(0.05)
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ An error occurred during creation: {str(e)}")
            finally:
                session.close()

            # Summary message
            if error_messages:
                st.success("✅ Locations and Service Points processed!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
                if session_created_locations or session_created_service_points:
                    st.info(f"📝 Created {len(session_created_locations)} location(s) and {len(session_created_service_points)} service point(s) in this session.")
                if translation_success_count > 0 or translation_failure_count > 0:
                    st.info(f"🌍 Translations: {translation_success_count} successful, {translation_failure_count} failed")
            else:
                st.success("✅ Locations and Service Points have been created successfully!")
                st.info("💡 All items were created or already existed.")
                if session_created_locations or session_created_service_points:
                    st.info(f"📝 Created {len(session_created_locations)} location(s) and {len(session_created_service_points)} service point(s) in this session.")
                if translation_success_count > 0:
                    st.info(f"🌍 Successfully created {translation_success_count} translation(s)")
            st.session_state['allow_calendar'] = True
