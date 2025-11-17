import streamlit as st
from Upload import upload
import requests
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import json
import uuid

from legacy_session_state import legacy_session_state

# Get session state of legacy session
legacy_session_state()

# Initialize tenant-related session state variables if not set
if not st.session_state.get('tenant'):
    st.session_state['tenant'] = st.session_state.get('tenant_name', '')
if not st.session_state.get('okapi'):
    st.session_state['okapi'] = st.session_state.get('okapi_url', '')
if not st.session_state.get('token'):
    st.session_state['token'] = st.session_state.get('token', '')

def create_loan_policy(policy_data, okapi, headers):
    """
    Creates or updates a loan policy
    :param policy_data: Dictionary containing loan policy information
    :param okapi: Okapi URL
    :param headers: Request headers
    :return: Tuple (success: bool, error_msg: str or None)
    """
    try:
        # Check if loan policy exists by ID if provided
        policy_id = policy_data.get('id')
        if policy_id:
            get_response = requests.get(f"{okapi}/loan-policy-storage/loan-policies/{policy_id}", headers=headers)
            if get_response.status_code == 200:
                # If it exists, update it
                update_url = f"{okapi}/loan-policy-storage/loan-policies/{policy_id}"
                response = requests.put(update_url, json=policy_data, headers=headers)
                if response.status_code in [200, 204]:
                    return True, None
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('errors', [{}])[0].get('message', f'Error updating loan policy (Status: {response.status_code})')
                    except:
                        error_msg = f'Error updating loan policy (Status: {response.status_code})'
                    return False, error_msg
        
        # If no ID or not found, try to create
        url = f"{okapi}/loan-policy-storage/loan-policies"
        response = requests.post(url, json=policy_data, headers=headers)
        
        if response.status_code in [200, 201]:
            return True, None
        elif response.status_code == 422:
            # Try to update if it already exists (by name)
            try:
                get_response = requests.get(f"{okapi}/loan-policy-storage/loan-policies?limit=1000&query=cql.allRecords%3D1", headers=headers)
                if get_response.status_code == 200:
                    existing_policies = get_response.json().get('loanPolicies', [])
                    policy_name = policy_data.get('name')
                    
                    for policy in existing_policies:
                        if str(policy.get('name', '')) == str(policy_name):
                            policy_data['id'] = policy.get('id')
                            update_url = f"{okapi}/loan-policy-storage/loan-policies/{policy.get('id')}"
                            update_response = requests.put(update_url, json=policy_data, headers=headers)
                            if update_response.status_code in [200, 204]:
                                return True, None
                            break
                
                error_data = response.json()
                error_msg = error_data.get('errors', [{}])[0].get('message', 'Loan policy validation failed')
                return False, error_msg
            except:
                return True, None  # Assume it's a duplicate, which is OK
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('errors', [{}])[0].get('message', f'Error (Status: {response.status_code})')
            except:
                error_msg = f'Error creating loan policy (Status: {response.status_code})'
            return False, error_msg
    except Exception as e:
        return False, f"Error: {str(e)}"

def loan_policies():
    """
    Main function to handle loan policies configuration
    Each row in the Excel sheet will create one loan policy record
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
    df = upload('LoanPolicies')
    
    if df is None or df.empty:
        st.warning("Please upload a file with LoanPolicies sheet.")
        return
    
    # Remove any rows with null values in required columns
    required_columns = ['name']
    for col in required_columns:
        if col not in df.columns:
            st.error(f"⚠️ Required column '{col}' is missing from the uploaded file.")
            return
    
    df = df[df['name'].notna()]
    
    # Strip leading and trailing whitespaces
    if 'name' in df.columns:
        df['name'] = df['name'].astype(str).str.strip()
    if 'description' in df.columns:
        df['description'] = df['description'].astype(str).str.strip()
    
    # Display the data in an editable grid
    display_columns = ['name', 'description', 'loanable', 'renewable', 'profileId', 'periodDuration', 
                       'periodIntervalId', 'closedLibraryDueDateManagementId', 'gracePeriodDuration', 
                       'gracePeriodIntervalId', 'itemLimit', 'numberAllowed', 'renewFromId', 'id']
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
        
        # Process each loan policy (loop through all rows)
        create_button = st.button('Create/Update Loan Policies', type='primary')
        
        if create_button:
            error_messages = []
            success_count = 0
            
            with st.spinner('Creating/updating loan policies...'):
                # Loop through each row and create a loan policy record
                for idx, row in selection.iterrows():
                    # Build the loan policy data structure
                    policy_data = {}
                    
                    # Basic fields
                    policy_data['name'] = str(row['name']).strip()
                    if pd.notna(row.get('description')):
                        policy_data['description'] = str(row['description']).strip()
                    
                    # Boolean fields
                    if pd.notna(row.get('loanable')):
                        policy_data['loanable'] = bool(row['loanable']) if isinstance(row['loanable'], bool) else str(row['loanable']).lower() in ['true', '1', 'yes']
                    else:
                        policy_data['loanable'] = True  # Default
                    if pd.notna(row.get('renewable')):
                        policy_data['renewable'] = bool(row['renewable']) if isinstance(row['renewable'], bool) else str(row['renewable']).lower() in ['true', '1', 'yes']
                    else:
                        policy_data['renewable'] = True  # Default
                    
                    # Build loansPolicy object
                    loans_policy = {}
                    if pd.notna(row.get('profileId')):
                        loans_policy['profileId'] = str(row['profileId']).strip()
                    else:
                        loans_policy['profileId'] = 'Rolling'  # Default
                    
                    # Period
                    if pd.notna(row.get('periodDuration')) or pd.notna(row.get('periodIntervalId')):
                        period = {}
                        if pd.notna(row.get('periodDuration')):
                            period['duration'] = int(float(row['periodDuration']))
                        if pd.notna(row.get('periodIntervalId')):
                            period['intervalId'] = str(row['periodIntervalId']).strip()
                        loans_policy['period'] = period
                    
                    # Closed library due date management
                    if pd.notna(row.get('closedLibraryDueDateManagementId')):
                        loans_policy['closedLibraryDueDateManagementId'] = str(row['closedLibraryDueDateManagementId']).strip()
                    
                    # Grace period
                    if pd.notna(row.get('gracePeriodDuration')) or pd.notna(row.get('gracePeriodIntervalId')):
                        grace_period = {}
                        if pd.notna(row.get('gracePeriodDuration')):
                            grace_period['duration'] = int(float(row['gracePeriodDuration']))
                        if pd.notna(row.get('gracePeriodIntervalId')):
                            grace_period['intervalId'] = str(row['gracePeriodIntervalId']).strip()
                        loans_policy['gracePeriod'] = grace_period
                    
                    # Item limit
                    if pd.notna(row.get('itemLimit')):
                        loans_policy['itemLimit'] = str(int(float(row['itemLimit'])))
                    
                    if loans_policy:
                        policy_data['loansPolicy'] = loans_policy
                    
                    # Build renewalsPolicy object
                    renewals_policy = {}
                    if pd.notna(row.get('numberAllowed')):
                        renewals_policy['numberAllowed'] = str(int(float(row['numberAllowed'])))
                    if pd.notna(row.get('renewFromId')):
                        renewals_policy['renewFromId'] = str(row['renewFromId']).strip()
                    
                    if renewals_policy:
                        policy_data['renewalsPolicy'] = renewals_policy
                    
                    # ID (optional)
                    if 'id' in row and pd.notna(row.get('id')) and str(row['id']).strip():
                        policy_data['id'] = str(row['id']).strip()
                    else:
                        # Generate UUID if not provided
                        policy_data['id'] = str(uuid.uuid4())
                    
                    # Create or update the loan policy (one API call per row)
                    success, error_msg = create_loan_policy(policy_data, okapi, headers)
                    
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"Loan Policy '{row.get('name', 'N/A')}': {error_msg}")
                        st.warning(f"⚠️ Loan Policy '{row.get('name', 'N/A')}': {error_msg}")
                except Exception as e:
                    error_messages.append(f"Loan Policy '{row.get('name', 'N/A')}': {str(e)}")
                    st.warning(f"⚠️ Loan Policy '{row.get('name', 'N/A')}': {str(e)}")
            
            # Summary message
            if error_messages:
                st.success(f"✅ {success_count} loan policy/policies created/updated successfully!")
                st.info(f"💡 {len(error_messages)} error(s) occurred - see warnings above for details.")
            else:
                st.success(f"✅ {success_count} loan policy/policies created/updated successfully!")
                st.info("💡 All loan policies were created/updated successfully.")
    else:
        st.warning('Please Select Required Loan Policies!!')

