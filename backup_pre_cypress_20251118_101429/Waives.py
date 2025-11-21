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

def create_waive(waive_data, okapi, headers):
    """
    Creates or updates a waive
    :param waive_data: Dictionary containing waive information
    :param okapi: Okapi URL
    :param headers: Request headers
    :return: Tuple (success: bool, error_msg: str or None)
    """
    try:
        url = f"{okapi}/waives"
        response = requests.post(url, json=waive_data, headers=headers)
        
        if response.status_code in [200, 201]:
            return True, None
        elif response.status_code == 422:
            # Try to update if it already exists
            try:
                # Check if waive exists by getting existing waives
                get_response = requests.get(f"{okapi}/waives", headers=headers)
                if get_response.status_code == 200:
                    existing_waives = get_response.json().get('waives', [])
                    # Try to find matching waive by nameReason
                    name_reason = waive_data.get('nameReason')
                    waive_id = waive_data.get('id')
                    
                    if waive_id:
                        # Update existing waive by ID
                        update_url = f"{okapi}/waives/{waive_id}"
                        update_response = requests.put(update_url, json=waive_data, headers=headers)
                        if update_response.status_code in [200, 204]:
                            return True, None
                    else:
                        # Find by nameReason
                        for waive in existing_waives:
                            if str(waive.get('nameReason', '')) == str(name_reason):
                                waive_data['id'] = waive.get('id')
                                update_url = f"{okapi}/waives/{waive.get('id')}"
                                update_response = requests.put(update_url, json=waive_data, headers=headers)
                                if update_response.status_code in [200, 204]:
                                    return True, None
                                break
                # If update fails or waive doesn't exist, return error
                error_data = response.json()
                error_msg = error_data.get('errors', [{}])[0].get('message', 'Waive already exists or validation failed')
                return False, error_msg
            except:
                return True, None  # Assume it's a duplicate, which is OK
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('errors', [{}])[0].get('message', f'Error (Status: {response.status_code})')
            except:
                error_msg = f'Error creating waive (Status: {response.status_code})'
            return False, error_msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def waives():
    """
    Main function to create waives
    Each row in the Excel sheet will create one waive record
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
    
    # Upload CSV file and create dataframe
    df = upload('Waives')
    
    if df is None or df.empty:
        st.warning("Please upload a file with Waives sheet.")
        return
    
    # Remove any rows with null values in required columns
    required_columns = ['nameReason']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"⚠️ Required column '{col}' is missing from the uploaded file.")
            return
    
    df = df[df['nameReason'].notna()]
    
    # Strip leading and trailing whitespaces
    if 'nameReason' in df.columns:
        df['nameReason'] = df['nameReason'].astype(str).str.strip()
    
    # Display the data in an editable grid
    display_columns = ['nameReason', 'id']
    display_columns = [col for col in display_columns if col in df.columns]
    
    builder = GridOptionsBuilder.from_dataframe(df[display_columns])
    builder.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
    builder.configure_pagination(enabled=True)
    for col in display_columns:
        builder.configure_column(col, editable=True)
    go = builder.build()
    grid_return = AgGrid(df[display_columns], editable=True, theme='balham', gridOptions=go)
    
    selected_rows = grid_return['selected_rows']
    
    if bool(selected_rows):
        selection = pd.DataFrame(selected_rows)
        
        # Display selected rows
        AgGrid(selection[display_columns], theme='balham')
        
        # Process each waive (loop through all rows)
        create_button = st.button('Create Waives', type='primary')
        
        if create_button:
            error_messages = []
            success_count = 0
            
            with st.spinner('Creating waives...'):
                # Loop through each row and create a waive record
                for idx, row in selection.iterrows():
                    # Build waive data
                    waive_data = {
                        'nameReason': str(row['nameReason']).strip()
                    }
                    
                    # Add optional id field if provided
                    if 'id' in row and pd.notna(row.get('id')) and str(row['id']).strip():
                        waive_data['id'] = str(row['id']).strip()
                    
                    # Create the waive (one API call per row)
                    success, error_msg = create_waive(waive_data, okapi, headers)
                    
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"Waive '{row.get('nameReason', 'N/A')}': {error_msg}")
                        st.warning(f"⚠️ Waive '{row.get('nameReason', 'N/A')}': {error_msg}")
            
            # Summary message
            if error_messages:
                st.success(f"✅ {success_count} waive(s) created successfully!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
            else:
                st.success(f"✅ {success_count} waive(s) created successfully!")
                st.info("💡 All waives were created successfully.")
    else:
        st.warning('Please Select Required Waives!!')

