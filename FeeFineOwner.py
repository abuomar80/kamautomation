import streamlit as st
from Upload import upload
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import json

from legacy_session_state import legacy_session_state

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

def get_all_service_points(okapi, headers):
    """
    Fetches all service points from the API
    Returns a dictionary mapping service point names to their UUIDs
    """
    try:
        response = requests.get(f"{okapi}/service-points?limit=1000", headers=headers)
        response.raise_for_status()
        data = response.json()
        service_points = data.get('servicepoints', [])
        
        # Create mapping: name -> {id, name}
        sp_map = {}
        for sp in service_points:
            sp_name = sp.get('name', '')
            sp_id = sp.get('id', '')
            if sp_name and sp_id:
                sp_map[sp_name] = {
                    'value': sp_id,
                    'label': sp_name
                }
        return sp_map
    except Exception as e:
        st.error(f"Error fetching service points: {str(e)}")
        return {}

def create_fee_fine_owner(owner_data, okapi, headers):
    """
    Creates or updates a fee/fine owner
    :param owner_data: Dictionary containing owner information
    :param okapi: Okapi URL
    :param headers: Request headers
    :return: Tuple (success: bool, error_msg: str or None)
    """
    try:
        # First, check if owner already exists
        owner_value = owner_data.get('owner')
        get_response = requests.get(f"{okapi}/owners", headers=headers)
        
        existing_owner_id = None
        if get_response.status_code == 200:
            existing_owners = get_response.json().get('owners', [])
            # Find owner with matching owner value
            for owner in existing_owners:
                if str(owner.get('owner', '')) == str(owner_value):
                    existing_owner_id = owner.get('id')
                    break
        
        # If owner exists, update it; otherwise create new
        if existing_owner_id:
            owner_data['id'] = existing_owner_id
            update_url = f"{okapi}/owners/{existing_owner_id}"
            response = requests.put(update_url, json=owner_data, headers=headers)
            
            if response.status_code in [200, 204]:
                return True, None
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('errors', [{}])[0].get('message', f'Error updating owner (Status: {response.status_code})')
                except:
                    error_msg = f'Error updating fee/fine owner (Status: {response.status_code})'
                return False, error_msg
        else:
            # Create new owner
            url = f"{okapi}/owners"
            response = requests.post(url, json=owner_data, headers=headers)
            
            if response.status_code in [200, 201]:
                return True, None
            elif response.status_code == 422:
                # Validation error - owner might already exist or data is invalid
                try:
                    error_data = response.json()
                    error_msg = error_data.get('errors', [{}])[0].get('message', 'Owner validation failed')
                    # If it's a duplicate, that's OK
                    if 'already exists' in error_msg.lower() or 'duplicate' in error_msg.lower():
                        return True, None
                    return False, error_msg
                except:
                    return True, None  # Assume it's a duplicate, which is OK
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get('errors', [{}])[0].get('message', f'Error (Status: {response.status_code})')
                except:
                    error_msg = f'Error creating fee/fine owner (Status: {response.status_code})'
                return False, error_msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def fee_fine_owner():
    """
    Main function to create fee/fine owners
    """
    # Get tenant connection details with fallbacks
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name")
    token = st.session_state.get("token")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url")

    if not all([tenant, token, okapi]):
        st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        st.info("Go to the Tenant page, enter connection details, click Connect, then return here.")
        return
    
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}", "Content-Type": "application/json"}
    
    # Check if service points have been created (Location tab completed)
    # Fetch service points to check availability
    service_points_map = get_all_service_points(okapi, headers)
    
    if not service_points_map:
        st.warning("⚠️ No service points found. Please complete the **Location** tab first to create service points.")
        st.info("Fee/fine Owner configuration requires service points to be created first.")
        return
    
    # Upload CSV file and create dataframe
    df = upload('FeeFineOwner')
    
    if df is None or df.empty:
        st.warning("Please upload a file with FeeFineOwner sheet.")
        return
    
    # Remove any rows with null values in required columns
    required_columns = ['Service Points', 'Owner']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"⚠️ Required column '{col}' is missing from the uploaded file.")
            return
    
    df = df[df['Owner'].notna()]
    df = df[df['Service Points'].notna()]
    
    # Strip leading and trailing whitespaces
    df['Service Points'] = df['Service Points'].str.strip()
    df['Owner'] = df['Owner'].astype(str).str.strip()
    
    # Display the data in an editable grid
    builder = GridOptionsBuilder.from_dataframe(df)
    builder.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
    builder.configure_pagination(enabled=True)
    builder.configure_column('Service Points', editable=True)
    builder.configure_column('Owner', editable=True)
    go = builder.build()
    grid_return = AgGrid(df, editable=True, theme='balham', gridOptions=go)
    
    selected_rows = grid_return['selected_rows']
    
    if bool(selected_rows):
        selection = pd.DataFrame(selected_rows)
        
        # Display selected rows
        AgGrid(selection[['Service Points', 'Owner']], theme='balham')
        
        # Process each owner
        create_button = st.button('Create Fee/Fine Owners', type='primary')
        
        if create_button:
            error_messages = []
            success_count = 0
            
            with st.spinner('Creating fee/fine owners...'):
                # Group by Owner to create one owner record per unique owner value
                for owner_value in selection['Owner'].unique():
                    owner_rows = selection[selection['Owner'] == owner_value]
                    
                    # Build service point owner list
                    service_point_owners = []
                    
                    for idx, row in owner_rows.iterrows():
                        sp_name = str(row['Service Points']).strip()
                        
                        # Handle "ALL" keyword
                        if sp_name.upper() == 'ALL':
                            # Add all service points
                            for sp_label, sp_info in service_points_map.items():
                                service_point_owners.append({
                                    'value': sp_info['value'],
                                    'label': sp_info['label']
                                })
                        else:
                            # Find service point by name
                            if sp_name in service_points_map:
                                sp_info = service_points_map[sp_name]
                                service_point_owners.append({
                                    'value': sp_info['value'],
                                    'label': sp_info['label']
                                })
                            else:
                                error_msg = f"Service point '{sp_name}' not found for owner '{owner_value}'"
                                error_messages.append(error_msg)
                                st.warning(f"⚠️ {error_msg}")
                                continue
                    
                    if not service_point_owners:
                        error_msg = f"No valid service points found for owner '{owner_value}'"
                        error_messages.append(error_msg)
                        st.warning(f"⚠️ {error_msg}")
                        continue
                    
                    # Create owner data
                    owner_data = {
                        'servicePointOwner': service_point_owners,
                        'owner': str(owner_value),
                        'id': None  # Let the API generate the ID
                    }
                    
                    # Create the fee/fine owner
                    success, error_msg = create_fee_fine_owner(owner_data, okapi, headers)
                    
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"Owner '{owner_value}': {error_msg}")
                        st.warning(f"⚠️ Owner '{owner_value}': {error_msg}")
            
            # Summary message
            if error_messages:
                st.success(f"✅ {success_count} fee/fine owner(s) created successfully!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
            else:
                st.success(f"✅ {success_count} fee/fine owner(s) created successfully!")
                st.info("💡 All owners were created successfully.")
    else:
        st.warning('Please Select Required Fee/Fine Owners!!')

