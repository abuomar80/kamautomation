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

def create_refund(refund_data, okapi, headers):
    """
    Creates or updates a refund
    :param refund_data: Dictionary containing refund information
    :param okapi: Okapi URL
    :param headers: Request headers
    :return: Tuple (success: bool, error_msg: str or None)
    """
    try:
        url = f"{okapi}/refunds"
        response = requests.post(url, json=refund_data, headers=headers)
        
        if response.status_code in [200, 201]:
            return True, None
        elif response.status_code == 422:
            # Try to update if it already exists
            try:
                # Check if refund exists by getting existing refunds
                get_response = requests.get(f"{okapi}/refunds", headers=headers)
                if get_response.status_code == 200:
                    existing_refunds = get_response.json().get('refunds', [])
                    # Try to find matching refund by nameReason
                    name_reason = refund_data.get('nameReason')
                    refund_id = refund_data.get('id')
                    
                    if refund_id:
                        # Update existing refund by ID
                        update_url = f"{okapi}/refunds/{refund_id}"
                        update_response = requests.put(update_url, json=refund_data, headers=headers)
                        if update_response.status_code in [200, 204]:
                            return True, None
                    else:
                        # Find by nameReason
                        for refund in existing_refunds:
                            if str(refund.get('nameReason', '')) == str(name_reason):
                                refund_data['id'] = refund.get('id')
                                update_url = f"{okapi}/refunds/{refund.get('id')}"
                                update_response = requests.put(update_url, json=refund_data, headers=headers)
                                if update_response.status_code in [200, 204]:
                                    return True, None
                                break
                # If update fails or refund doesn't exist, return error
                error_data = response.json()
                error_msg = error_data.get('errors', [{}])[0].get('message', 'Refund already exists or validation failed')
                return False, error_msg
            except:
                return True, None  # Assume it's a duplicate, which is OK
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('errors', [{}])[0].get('message', f'Error (Status: {response.status_code})')
            except:
                error_msg = f'Error creating refund (Status: {response.status_code})'
            return False, error_msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def refunds():
    """
    Main function to create refunds
    Each row in the Excel sheet will create one refund record
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
    df = upload('Refunds')
    
    if df is None or df.empty:
        st.warning("Please upload a file with Refunds sheet.")
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
        
        # Process each refund (loop through all rows)
        create_button = st.button('Create Refunds', type='primary')
        
        if create_button:
            error_messages = []
            success_count = 0
            
            with st.spinner('Creating refunds...'):
                # Loop through each row and create a refund record
                for idx, row in selection.iterrows():
                    # Build refund data
                    refund_data = {
                        'nameReason': str(row['nameReason']).strip()
                    }
                    
                    # Add optional id field if provided
                    if 'id' in row and pd.notna(row.get('id')) and str(row['id']).strip():
                        refund_data['id'] = str(row['id']).strip()
                    
                    # Create the refund (one API call per row)
                    success, error_msg = create_refund(refund_data, okapi, headers)
                    
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"Refund '{row.get('nameReason', 'N/A')}': {error_msg}")
                        st.warning(f"⚠️ Refund '{row.get('nameReason', 'N/A')}': {error_msg}")
            
            # Summary message
            if error_messages:
                st.success(f"✅ {success_count} refund(s) created successfully!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
            else:
                st.success(f"✅ {success_count} refund(s) created successfully!")
                st.info("💡 All refunds were created successfully.")
    else:
        st.warning('Please Select Required Refunds!!')

