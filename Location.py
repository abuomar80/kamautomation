import streamlit as st
from Service_points import (
    create_sp, create_institutions, create_campuses, create_libraries, create_locations,
    delete_location, delete_service_point, get_location_by_code, get_service_point_by_code
)
from Upload import upload
import pandas as pd
import requests
from st_aggrid import AgGrid, GridOptionsBuilder
from legacy_session_state import legacy_session_state
from connection_manager import get_session, make_request_with_retry, periodic_connection_check, validate_connection
import time
import json

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

        col1, col2, col3 = st.columns(3)
        with col1:
            createLoc = st.button("Create locations", type="primary")
        with col2:
            deleteLoc = st.button("🗑️ Delete Created Items", type="secondary")
        with col3:
            scanLoc = st.button("🔍 Scan for Created Items", type="secondary")
        
        # Initialize session state for tracking created items
        if 'created_locations' not in st.session_state:
            st.session_state.created_locations = []
        if 'created_service_points' not in st.session_state:
            st.session_state.created_service_points = []
        
        # Display current tracking status
        if st.session_state.created_locations or st.session_state.created_service_points:
            with st.expander(f"📝 View Tracked Items ({len(st.session_state.created_locations)} locations, {len(st.session_state.created_service_points)} service points)", expanded=False):
                if st.session_state.created_locations:
                    st.write("**Locations to delete:**")
                    for loc_code in st.session_state.created_locations:
                        st.write(f"  - {loc_code}")
                if st.session_state.created_service_points:
                    st.write("**Service Points to delete:**")
                    for sp_code in st.session_state.created_service_points:
                        st.write(f"  - {sp_code}")
                if st.button("Clear Tracking List", key="clear_tracking"):
                    st.session_state.created_locations = []
                    st.session_state.created_service_points = []
                    st.success("Tracking list cleared!")
                    st.rerun()
        else:
            st.info("ℹ️ No items tracked yet. Items will be automatically tracked when created, or use 'Scan for Created Items' to find existing items from selected rows.")
        
        # Handle scan button - find locations and service points from selected rows
        if scanLoc:
            if selection.empty:
                st.warning("⚠️ Please select rows first before scanning.")
            else:
                scan_progress = st.progress(0)
                scan_status = st.empty()
                scanned_locations = []
                scanned_service_points = []
                total_rows = len(selection)
                
                for idx, (index, row) in enumerate(selection.iterrows()):
                    scan_progress.progress((idx + 1) / total_rows)
                    scan_status.text(f"Scanning row {idx + 1} of {total_rows}...")
                    
                    sp_code = str(row["ServicePoints Codes"]).strip()
                    location_code = str(row["LocationsCodes"]).strip()
                    
                    # Check if service point exists
                    if sp_code:
                        sp_id = get_service_point_by_code(sp_code, okapi, tenant, token)
                        if sp_id and sp_code not in st.session_state.created_service_points:
                            scanned_service_points.append(sp_code)
                    
                    # Check if location exists
                    if location_code:
                        loc_id = get_location_by_code(location_code, okapi, tenant, token)
                        if loc_id and location_code not in st.session_state.created_locations:
                            scanned_locations.append(location_code)
                
                scan_progress.empty()
                scan_status.empty()
                
                # Add scanned items to session state
                st.session_state.created_locations.extend(scanned_locations)
                st.session_state.created_service_points.extend(scanned_service_points)
                
                # Remove duplicates
                st.session_state.created_locations = list(set(st.session_state.created_locations))
                st.session_state.created_service_points = list(set(st.session_state.created_service_points))
                
                if scanned_locations or scanned_service_points:
                    st.success(f"✅ Found {len(scanned_locations)} location(s) and {len(scanned_service_points)} service point(s) from selected rows!")
                    st.rerun()
                else:
                    st.info("ℹ️ No new items found in selected rows. Items may already be tracked or don't exist.")
        
        # Handle delete button
        if deleteLoc:
            if not st.session_state.created_locations and not st.session_state.created_service_points:
                st.warning("⚠️ No items to delete. Create locations first or use 'Scan for Created Items' to find existing items.")
            else:
                with st.spinner('Deleting created items...'):
                    delete_progress = st.progress(0)
                    delete_status = st.empty()
                    
                    total_items = len(st.session_state.created_locations) + len(st.session_state.created_service_points)
                    deleted_count = 0
                    delete_errors = []
                    
                    # Delete locations
                    for loc_code in st.session_state.created_locations[:]:
                        delete_status.text(f"Deleting location: {loc_code}...")
                        loc_id = get_location_by_code(loc_code, okapi, tenant, token)
                        if loc_id:
                            success, error_msg = delete_location(loc_id, okapi, tenant, token)
                            if success:
                                st.session_state.created_locations.remove(loc_code)
                                deleted_count += 1
                            else:
                                delete_errors.append(f"Location '{loc_code}': {error_msg}")
                        else:
                            st.session_state.created_locations.remove(loc_code)
                            deleted_count += 1
                        
                        delete_progress.progress(deleted_count / total_items if total_items > 0 else 1.0)
                        time.sleep(0.1)  # Small delay to prevent overwhelming the API
                    
                    # Delete service points
                    for sp_code in st.session_state.created_service_points[:]:
                        delete_status.text(f"Deleting service point: {sp_code}...")
                        sp_id = get_service_point_by_code(sp_code, okapi, tenant, token)
                        if sp_id:
                            success, error_msg = delete_service_point(sp_id, okapi, tenant, token)
                            if success:
                                st.session_state.created_service_points.remove(sp_code)
                                deleted_count += 1
                            else:
                                delete_errors.append(f"Service Point '{sp_code}': {error_msg}")
                        else:
                            st.session_state.created_service_points.remove(sp_code)
                            deleted_count += 1
                        
                        delete_progress.progress(deleted_count / total_items if total_items > 0 else 1.0)
                        time.sleep(0.1)  # Small delay to prevent overwhelming the API
                    
                    delete_progress.empty()
                    delete_status.empty()
                    
                    if delete_errors:
                        st.error(f"❌ Some items could not be deleted:")
                        for err in delete_errors:
                            st.error(f"  - {err}")
                    else:
                        st.success(f"✅ Successfully deleted {deleted_count} item(s)!")
        
        if createLoc:
            # CREATE EMPTY DICTIONARIES TO STORE DATA IN
            locations = {}
            locations_code = {}
            locations_lib = {}
            locations_camp = {}
            locations_inst = {}

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
                            st.info(f"💡 Processed {idx} rows before connection issue. You can use Delete button to clean up created items.")
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
                        if sp_code not in st.session_state.created_service_points:
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

                    # GET INSTITUTION ID
                    try:
                        result_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/institutions?query=(name=={institution_name})")
                        if result_response is None or not result_response.json().get('locinsts'):
                            error_messages.append(f"Institution '{institution_name}' not found after creation")
                            continue
                        result = result_response.json()
                        insID = result['locinsts'][0]['id']
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

                    # CREATING LIBRARIES
                    try:
                        result_response = make_request_with_retry(session, 'GET', f"{okapi}/location-units/campuses?query=(name=={campus_name})")
                        if result_response is None or not result_response.json().get('loccamps'):
                            error_messages.append(f"Campus '{campus_name}' not found after creation")
                            continue
                        result = result_response.json()
                        campusID = result['loccamps'][0]['id']
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
                            if code not in st.session_state.created_locations:
                                session_created_locations.append(code)
                        if not success and error_msg:
                            error_messages.append(f"Location '{key}': {error_msg}")
                            st.warning(f"⚠️ Location '{key}': {error_msg}")
                    
                    # Small delay to prevent overwhelming the API
                    time.sleep(0.05)
                
                # Update session state with newly created items
                st.session_state.created_locations.extend(session_created_locations)
                st.session_state.created_service_points.extend(session_created_service_points)
                
                # Remove duplicates
                st.session_state.created_locations = list(set(st.session_state.created_locations))
                st.session_state.created_service_points = list(set(st.session_state.created_service_points))
                
                # Clear progress indicators
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                progress_bar.empty()
                status_text.empty()
                st.error(f"❌ An error occurred during creation: {str(e)}")
                st.info("💡 You can use the Delete button to remove any items that were created before the error.")
            finally:
                session.close()

            # Summary message
            if error_messages:
                st.success("✅ Locations and Service Points processed!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
                if session_created_locations or session_created_service_points:
                    st.info(f"📝 Created {len(session_created_locations)} location(s) and {len(session_created_service_points)} service point(s) in this session.")
            else:
                st.success("✅ Locations and Service Points have been created successfully!")
                st.info("💡 All items were created or already existed.")
                if session_created_locations or session_created_service_points:
                    st.info(f"📝 Created {len(session_created_locations)} location(s) and {len(session_created_service_points)} service point(s) in this session.")
            st.session_state['allow_calendar'] = True