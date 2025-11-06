import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml import SafeLoader
# Note: legacy_session_state is NOT called here to avoid conflicts with authenticator form
# Other pages that need it will call it themselves

st.set_page_config(
    page_title="KAM TEAM", layout="wide", initial_sidebar_state="expanded"
)

with open('authentication.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
)

# Login form - returns None when location is 'main', authentication info stored in session_state
authenticator.login(location='main', key='Login')

# Get authentication status from session_state (stored by authenticator)
name = st.session_state.get('name')
authentication_status = st.session_state.get('authentication_status')
username = st.session_state.get('username')

if authentication_status:
    authenticator.logout(button_name='Logout', location='sidebar')
    
    # Define pages with explicit grouping using st.navigation (Streamlit 1.46.0+)
    # This creates collapsible sections in the sidebar
    # Reference: https://docs.streamlit.io/develop/api-reference/navigation/st.navigation
    pages = {
        "📁 Tenant Configuration": [
            st.Page("pages/Tenant_Configuration/0_Tenant.py", title="Tenant", default=True),
            st.Page("pages/Tenant_Configuration/1_Basic Configuration.py", title="Basic Configuration"),
            st.Page("pages/Tenant_Configuration/2_Advanced Configuration.py", title="Advanced Configuration"),
            st.Page("pages/Tenant_Configuration/3_SIP2 Configuration.py", title="SIP2 Configuration"),
            st.Page("pages/Tenant_Configuration/4_Default Users.py", title="Default Users"),
            st.Page("pages/Tenant_Configuration/5_Add Permission.py", title="Add Permission"),
            st.Page("pages/Tenant_Configuration/6_Z39.50.py", title="Z39.50"),
        ],
        "📦 Data Migration": [
            st.Page("pages/Data_Migration/1_Users Import.py", title="Users Import"),
            st.Page("pages/Data_Migration/2_Circulation Loans.py", title="Circulation Loans"),
            st.Page("pages/Data_Migration/3_Fines.py", title="Fines"),
            st.Page("pages/Data_Migration/4_Marc Splitter.py", title="Marc Splitter"),
        ],
        "⚙️ Other Configuration": [
            st.Page("pages/Other_Configuration/1_Clone Tenant.py", title="Clone Tenant"),
            st.Page("pages/Other_Configuration/2_Backup Tenant.py", title="Backup Tenant"),
        ],
    }
    
    # Create navigation with collapsible groups
    pg = st.navigation(pages, position="sidebar")
    pg.run()
    
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
