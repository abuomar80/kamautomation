"""
KeePass Configuration Page

Configure KeePass password database settings for automatic credential storage.
"""

import streamlit as st
import os
from keepass_helper import test_keepass_connection, get_database_path, get_keepass_master_password
from legacy_session_state import legacy_session_state

legacy_session_state()

# Check if the tenant connection is established
if 'allow_tenant' not in st.session_state:
    st.session_state['allow_tenant'] = False

hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_menu_style, unsafe_allow_html=True)

st.title("KeePass Configuration")

if st.session_state.allow_tenant:
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name", "")
    
    st.markdown("### KeePass Password Management")
    st.info("""
    **KeePass Integration** allows automatic storage of user credentials in encrypted KeePass databases.
    
    - **Per-Tenant Databases**: Each tenant gets its own `.kdbx` file
    - **Automatic Storage**: Credentials are saved when users are created
    - **Secure**: Master password stored in `authentication.yaml` (encrypted)
    """)
    
    # Configuration Status
    st.markdown("---")
    st.subheader("Configuration Status")
    
    master_password = get_keepass_master_password()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if master_password:
            st.success("✓ Master Password Configured")
            st.caption("Source: `authentication.yaml`")
        else:
            st.error("✗ Master Password Not Set")
            st.caption("Add to `authentication.yaml` file")
    
    with col2:
        if tenant:
            db_path = get_database_path(tenant)
            if os.path.exists(db_path):
                st.success(f"✓ Database Exists")
                st.caption(f"Path: `{db_path}`")
            else:
                st.info("✓ Database Will Be Created")
                st.caption(f"Path: `{db_path}`")
        else:
            st.warning("⚠ No Tenant Selected")
    
    # Test Connection
    st.markdown("---")
    st.subheader("Test Connection")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("Test Connection", type="primary"):
            if not master_password:
                st.error("❌ Cannot test: Master password not configured")
                st.info("**To configure:**\n1. Open `authentication.yaml`\n2. Add section:\n   ```yaml\n   keepass:\n     master_password: 'YourPassword'\n   ```\n3. Save and restart the application")
            elif not tenant:
                st.error("❌ Cannot test: No tenant connected")
            else:
                with st.spinner("Testing connection..."):
                    success, message = test_keepass_connection(tenant)
                    if success:
                        st.success(f"✓ {message}")
                    else:
                        st.error(f"❌ {message}")
    
    # Database Information
    if tenant and master_password:
        st.markdown("---")
        st.subheader("Database Information")
        
        db_path = get_database_path(tenant)
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.metric("Tenant", tenant)
            st.metric("Database Path", os.path.basename(db_path))
        
        with info_col2:
            if os.path.exists(db_path):
                file_size = os.path.getsize(db_path)
                st.metric("File Size", f"{file_size:,} bytes")
                st.metric("Status", "Active")
            else:
                st.metric("Status", "Not Created Yet")
                st.caption("Database will be created on first use")
    
    # Setup Instructions
    st.markdown("---")
    st.subheader("Setup Instructions")
    
    with st.expander("How to Configure KeePass Integration"):
        st.markdown("""
        ### Step 1: Add KeePass Section to authentication.yaml
        
        Edit your `authentication.yaml` file and add:
        ```yaml
        keepass:
          master_password: 'YourSecurePassword123!'
        ```
        
        **Important**: 
        - Choose a strong master password
        - Remember this password - it cannot be recovered
        - Keep it secure - it protects all stored credentials
        - The password can be encrypted like other credentials in this file
        
        ### Step 2: Restart Application
        
        After editing the file, restart the Streamlit application:
        ```powershell
        # Stop the current app (Ctrl+C)
        # Then restart:
        streamlit run Homepage.py
        ```
        
        ### Step 3: Test Connection
        
        Click the "Test Connection" button above to verify the setup.
        
        ### Step 4: Create Users
        
        Go to "Default Users" page and create users. Credentials will automatically save to KeePass!
        
        ---
        
        ### Database Location
        
        Databases are stored in:
        ```
        {app_directory}/keepass_databases/{tenant_name}.kdbx
        ```
        
        ### OneDrive Sync (Future)
        
        The database can be moved to the OneDrive shared location:
        ```
        https://naseej.sharepoint.com/:f:/r/sites/KAMSol/Shared%20Documents/KeePassXC_KAM_Password
        ```
        """)
    
    # Troubleshooting
    with st.expander("Troubleshooting"):
        st.markdown("""
        ### Common Issues
        
        **"Master Password Not Set"**
        - Ensure the environment variable is set correctly
        - Restart the application after setting the variable
        - Check variable: `echo $env:KEEPASS_MASTER_PASSWORD` in PowerShell
        
        **"Invalid Master Password"**
        - The password doesn't match the existing database
        - If you forgot the password, you'll need to create a new database
        
        **"Connection Failed"**
        - Check that PyKeePass is installed: `pip install pykeepass`
        - Verify the database directory is writable
        - Check application logs for detailed error messages
        
        **Credentials Not Saving Automatically**
        - Verify KeePass is configured (green checkmarks above)
        - Check for error messages in the user creation page
        - The database will be created automatically on first use
        """)

else:
    st.warning("⚠️ Please Connect to Tenant First.")
    st.info("Go to the 'Tenant' page to establish a connection.")
