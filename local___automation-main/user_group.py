import streamlit as st
from Upload import upload
import requests
from pandas import json_normalize
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder
import json

from legacy_session_state import legacy_session_state

# Get session state of legacy session
legacy_session_state()

if "department_activate" not in st.session_state:
    st.session_state.department_activate = True

def create_ugroup(df, expirationOffsetInDays):

    ugroupurl=f'{st.session_state.okapi}/groups'
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}

    if st.session_state.Disdur is False:
        for index, row in df.iterrows():
            # Use Description column if available, otherwise use Medad (group name) as description
            description = row.get('Description', row.get('Medad', ''))
            if pd.isna(description):
                description = row['Medad']
            
            to_do={
                "group" : f"{row['Medad']}",
                "desc" : f"{description}",
                "expirationOffsetInDays" : expirationOffsetInDays}

            requests.post(ugroupurl, data=json.dumps(to_do), headers=headers)
    elif st.session_state.Disdur is True:
        for index, row in df.iterrows():
            # Use Description column if available, otherwise use Medad (group name) as description
            description = row.get('Description', row.get('Medad', ''))
            if pd.isna(description):
                description = row['Medad']
            
            to_do = {
                "group": f"{row['Medad']}",
                "desc": f"{description}"}

            requests.post(ugroupurl, data=json.dumps(to_do), headers=headers)

def departments(df):
    department = f'{st.session_state.okapi}/departments'
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    for index, row in df.iterrows():
        if row['Department'] is None:
            pass
        else:
            to_do = {
                "name": f"{row['Department']}",
                "code": f"{row['Department_code']}"}

            requests.post(department, data=json.dumps(to_do), headers=headers)

def user_groups():
    df = upload('User_groups')
    # Remove any rows with null values in Medad (required column - this is the Patron group name)
    df = df[df['Medad'].notna()]
    # Strip leading and trailing whitespaces from "Medad" column
    df['Medad'] = df.Medad.str.strip()
    
    # Ensure Description column exists, fill with Medad if missing
    if 'Description' not in df.columns:
        df['Description'] = df['Medad']
    else:
        # Fill empty descriptions with Medad value
        df['Description'] = df['Description'].fillna(df['Medad'])
        df['Description'] = df['Description'].str.strip()
    
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    
    # GET request to get current user groups
    response = requests.get(f"{st.session_state.okapi}/groups", headers=headers).json()
    df_group = json_normalize(response['usergroups'])
    
    # Create an editable grid of the uploaded CSV data
    # Only show columns that are relevant for user groups: Legacy System, Description, Medad
    display_columns = ['Legacy System', 'Description', 'Medad']
    # Filter to only include columns that exist in the dataframe
    display_columns = [col for col in display_columns if col in df.columns]
    
    builder = GridOptionsBuilder.from_dataframe(df[display_columns] if display_columns else df)
    builder.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
    builder.configure_pagination(enabled=True)
    builder.configure_column('Medad', editable=True)
    if 'Description' in display_columns:
        builder.configure_column('Description', editable=True)
    go = builder.build()
    grid_return = AgGrid(df[display_columns] if display_columns else df, editable=True, theme='balham', gridOptions=go)

    selected_rows = grid_return['selected_rows']
    if bool(selected_rows):
        selection = pd.DataFrame(selected_rows)
        # Display only relevant columns
        AgGrid(selection[display_columns], theme='balham')
        
        # Exclude already existing user groups from the selection
        medadlist = df_group.group.tolist()
        selection = selection[~selection['Medad'].isin(medadlist)]
        
        # Track the last created selection to detect when a new selection is made
        if 'last_user_groups_selection_hash' not in st.session_state:
            st.session_state.last_user_groups_selection_hash = None
        
        # Create hash of current selection to detect changes
        current_selection_hash = hash(tuple(sorted(selection['Medad'].tolist()))) if not selection.empty else None
        
        # Show summary BEFORE button click (preview of what will be created)
        # Only show if this is a new selection (not after creation)
        if not selection.empty and current_selection_hash != st.session_state.last_user_groups_selection_hash:
            st.info(f"📋 **Preview:** {len(selection)} new user group(s) will be created")
        
        # Create user groups button
        create_button = st.button('Create User Groups')
        if create_button:
            if not selection.empty:
                with st.spinner('Creating user groups...'):
                    create_ugroup(selection, st.session_state.offsetduration)
                    # Mark this selection as created to prevent showing summary again
                    st.session_state.last_user_groups_selection_hash = current_selection_hash
                    st.success(f'✅ {len(selection)} User Group(s) Created Successfully')
            else:
                st.info('No new user groups to create (all selected groups already exist)')

    else:
        st.warning('Please Select Required User Groups!!')

