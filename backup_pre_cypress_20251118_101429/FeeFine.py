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

def get_all_owners(okapi, headers):
    """
    Fetches all fee/fine owners from the API
    Returns a dictionary mapping owner values to their IDs
    """
    try:
        response = requests.get(f"{okapi}/owners?limit=1000", headers=headers)
        response.raise_for_status()
        data = response.json()
        owners = data.get('owners', [])
        
        # Create mapping: owner value -> owner ID
        owner_map = {}
        for owner in owners:
            owner_value = str(owner.get('owner', ''))
            owner_id = owner.get('id', '')
            if owner_value and owner_id:
                owner_map[owner_value] = owner_id
        return owner_map
    except Exception as e:
        st.error(f"Error fetching fee/fine owners: {str(e)}")
        return {}

def create_fee_fine(fee_fine_data, okapi, headers):
    """
    Creates or updates a fee/fine
    :param fee_fine_data: Dictionary containing fee/fine information
    :param okapi: Okapi URL
    :param headers: Request headers
    :return: Tuple (success: bool, error_msg: str or None)
    """
    try:
        url = f"{okapi}/feefines"
        response = requests.post(url, json=fee_fine_data, headers=headers)
        
        if response.status_code in [200, 201]:
            return True, None
        elif response.status_code == 422:
            # Try to update if it already exists
            try:
                # Check if fee/fine exists by getting existing fee/fines
                get_response = requests.get(f"{okapi}/feefines", headers=headers)
                if get_response.status_code == 200:
                    existing_fees = get_response.json().get('feefines', [])
                    # Try to find matching fee/fine by ownerId and feeFineType
                    owner_id = fee_fine_data.get('ownerId')
                    fee_fine_type = fee_fine_data.get('feeFineType')
                    fee_fine_id = fee_fine_data.get('id')
                    
                    if fee_fine_id:
                        # Update existing fee/fine
                        update_url = f"{okapi}/feefines/{fee_fine_id}"
                        update_response = requests.put(update_url, json=fee_fine_data, headers=headers)
                        if update_response.status_code in [200, 204]:
                            return True, None
                    else:
                        # Find by ownerId and feeFineType
                        for fee in existing_fees:
                            if (str(fee.get('ownerId', '')) == str(owner_id) and 
                                str(fee.get('feeFineType', '')) == str(fee_fine_type)):
                                fee_fine_data['id'] = fee.get('id')
                                update_url = f"{okapi}/feefines/{fee.get('id')}"
                                update_response = requests.put(update_url, json=fee_fine_data, headers=headers)
                                if update_response.status_code in [200, 204]:
                                    return True, None
                                break
                # If update fails or fee/fine doesn't exist, return error
                error_data = response.json()
                error_msg = error_data.get('errors', [{}])[0].get('message', 'Fee/fine already exists or validation failed')
                return False, error_msg
            except:
                return True, None  # Assume it's a duplicate, which is OK
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('errors', [{}])[0].get('message', f'Error (Status: {response.status_code})')
            except:
                error_msg = f'Error creating fee/fine (Status: {response.status_code})'
            return False, error_msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def fee_fine():
    """
    Main function to create fee/fines
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
    
    # Check if fee/fine owners have been created (Fee/Fine Owner tab completed)
    owners_map = get_all_owners(okapi, headers)
    
    if not owners_map:
        st.warning("⚠️ No fee/fine owners found. Please complete the **Fee/Fine Owner** tab first to create owners.")
        st.info("Fee/fine configuration requires owners to be created first.")
        return
    
    # Upload CSV file and create dataframe
    df = upload('FeeFine')
    
    if df is None or df.empty:
        st.warning("Please upload a file with FeeFine sheet.")
        return
    
    # Remove any rows with null values in required columns
    required_columns = ['feeFineType', 'amountWithoutVat', 'owner']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"⚠️ Required column '{col}' is missing from the uploaded file.")
            return
    
    df = df[df['feeFineType'].notna()]
    df = df[df['amountWithoutVat'].notna()]
    df = df[df['owner'].notna()]
    
    # Strip leading and trailing whitespaces
    if 'owner' in df.columns:
        df['owner'] = df['owner'].astype(str).str.strip()
    if 'feeFineType' in df.columns:
        df['feeFineType'] = df['feeFineType'].astype(str).str.strip()
    
    # Convert numeric columns
    if 'amountWithoutVat' in df.columns:
        df['amountWithoutVat'] = pd.to_numeric(df['amountWithoutVat'], errors='coerce')
    if 'vat' in df.columns:
        df['vat'] = pd.to_numeric(df['vat'], errors='coerce')
    
    # Handle boolean column
    if 'automatic' in df.columns:
        # Convert various boolean representations
        df['automatic'] = df['automatic'].astype(str).str.lower().map({
            'true': True, '1': True, 'yes': True, 'y': True,
            'false': False, '0': False, 'no': False, 'n': False
        }).fillna(False)
    else:
        df['automatic'] = False
    
    # Display the data in an editable grid
    display_columns = ['feeFineType', 'amountWithoutVat', 'vat', 'owner', 'automatic']
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
        
        # Process each fee/fine
        create_button = st.button('Create Fee/Fines', type='primary')
        
        if create_button:
            error_messages = []
            success_count = 0
            
            with st.spinner('Creating fee/fines...'):
                for idx, row in selection.iterrows():
                    owner_value = str(row['owner']).strip()
                    
                    # Get owner ID from mapping
                    if owner_value not in owners_map:
                        error_msg = f"Owner '{owner_value}' not found for fee/fine type '{row.get('feeFineType', 'N/A')}'"
                        error_messages.append(error_msg)
                        st.warning(f"⚠️ {error_msg}")
                        continue
                    
                    owner_id = owners_map[owner_value]
                    
                    # Build fee/fine data
                    fee_fine_data = {
                        'feeFineType': str(row['feeFineType']),
                        'amountWithoutVat': float(row['amountWithoutVat']) if pd.notna(row['amountWithoutVat']) else 0.0,
                        'ownerId': owner_id,
                        'automatic': bool(row.get('automatic', False))
                    }
                    
                    # Add optional fields
                    if 'vat' in row and pd.notna(row['vat']):
                        fee_fine_data['vat'] = float(row['vat'])
                    
                    # Don't include id if not provided (let API generate it)
                    if 'id' in row and pd.notna(row.get('id')):
                        fee_fine_data['id'] = str(row['id'])
                    
                    # Create the fee/fine
                    success, error_msg = create_fee_fine(fee_fine_data, okapi, headers)
                    
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"Fee/fine type '{row.get('feeFineType', 'N/A')}' for owner '{owner_value}': {error_msg}")
                        st.warning(f"⚠️ Fee/fine type '{row.get('feeFineType', 'N/A')}' for owner '{owner_value}': {error_msg}")
            
            # Summary message
            if error_messages:
                st.success(f"✅ {success_count} fee/fine(s) created successfully!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
            else:
                st.success(f"✅ {success_count} fee/fine(s) created successfully!")
                st.info("💡 All fee/fines were created successfully.")
    else:
        st.warning('Please Select Required Fee/Fines!!')

