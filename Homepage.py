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
# Try the local version's approach first, then fallback
try:
    authenticator.login(location='main', key='Login')
except (TypeError, AttributeError):
    # Fallback for different API versions
    try:
        authenticator.login()
    except:
        try:
            authenticator.login('Login', 'main')
        except:
            authenticator.login('Login')

# Get authentication status from session_state (stored by authenticator)
name = st.session_state.get('name')
authentication_status = st.session_state.get('authentication_status')
username = st.session_state.get('username')

if authentication_status:
    authenticator.logout(button_name='Logout', location='sidebar')
    
    # Use st.navigation exactly like the local version
    # Define pages with explicit grouping using st.navigation (Streamlit 1.28.0+)
    # This creates collapsible sections in the sidebar
    # Reference: https://docs.streamlit.io/develop/api-reference/navigation/st.navigation
    try:
        # Check if st.navigation and st.Page are available
        if hasattr(st, 'navigation') and hasattr(st, 'Page'):
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
            
            # Create navigation with collapsible groups - exactly like local version
            pg = st.navigation(pages, position="sidebar")
            pg.run()
        else:
            # If st.navigation is not available, show error
            st.error("st.navigation is not available in this Streamlit version. Please upgrade to Streamlit 1.28.0 or later.")
            st.info(f"Current Streamlit version: {st.__version__}")
    except Exception as e:
        # If st.navigation fails, show the error
        st.error(f"Error with st.navigation: {str(e)}")
        st.exception(e)
        st.info("Falling back to custom navigation...")
        
        # Fallback to custom navigation
        import os
        import sys
        
        page_mapping = {
            "📁 Tenant Configuration": {
                "Tenant": "pages/Tenant_Configuration/0_Tenant.py",
                "Basic Configuration": "pages/Tenant_Configuration/1_Basic Configuration.py",
                "Advanced Configuration": "pages/Tenant_Configuration/2_Advanced Configuration.py",
                "SIP2 Configuration": "pages/Tenant_Configuration/3_SIP2 Configuration.py",
                "Default Users": "pages/Tenant_Configuration/4_Default Users.py",
                "Add Permission": "pages/Tenant_Configuration/5_Add Permission.py",
                "Z39.50": "pages/Tenant_Configuration/6_Z39.50.py",
            },
            "📦 Data Migration": {
                "Users Import": "pages/Data_Migration/1_Users Import.py",
                "Circulation Loans": "pages/Data_Migration/2_Circulation Loans.py",
                "Fines": "pages/Data_Migration/3_Fines.py",
                "Marc Splitter": "pages/Data_Migration/4_Marc Splitter.py",
            },
            "⚙️ Other Configuration": {
                "Clone Tenant": "pages/Other_Configuration/1_Clone Tenant.py",
                "Backup Tenant": "pages/Other_Configuration/2_Backup Tenant.py",
            },
        }
        
        st.sidebar.markdown("## 📋 Navigation")
        st.sidebar.markdown("---")
        
        available_pages = {}
        for group_name, pages in page_mapping.items():
            st.sidebar.markdown(f"### {group_name}")
            group_available = {}
            for page_name, page_path in pages.items():
                if os.path.exists(page_path):
                    group_available[page_name] = page_path
                    button_key = f"nav_{group_name}_{page_name}"
                    button_type = "primary" if st.session_state.get('current_page') == page_path else "secondary"
                    if st.sidebar.button(page_name, key=button_key, use_container_width=True, type=button_type):
                        st.session_state['current_page'] = page_path
                        st.rerun()
            if group_available:
                available_pages[group_name] = group_available
            st.sidebar.markdown("---")
        
        current_page = st.session_state.get('current_page')
        if not current_page and available_pages:
            first_group = list(available_pages.keys())[0]
            first_page_path = list(available_pages[first_group].values())[0]
            st.session_state['current_page'] = first_page_path
            current_page = first_page_path
            st.rerun()
        
        if not current_page:
            st.title(f"Welcome, {name}! 👋")
            st.markdown("---")
        else:
            if os.path.exists(current_page):
                try:
                    root_dir = os.path.dirname(os.path.abspath(__file__))
                    if root_dir not in sys.path:
                        sys.path.insert(0, root_dir)
                    
                    with open(current_page, 'r', encoding='utf-8') as f:
                        page_code = f.read()
                    
                    page_namespace = {
                        '__name__': '__main__',
                        '__file__': current_page,
                        'st': st,
                        'sys': sys,
                        'os': os,
                    }
                    
                    try:
                        from legacy_session_state import legacy_session_state
                        page_namespace['legacy_session_state'] = legacy_session_state
                    except ImportError:
                        pass
                    
                    compiled_code = compile(page_code, current_page, 'exec')
                    exec(compiled_code, page_namespace)
                except Exception as e:
                    st.error(f"Error loading page: {str(e)}")
                    st.exception(e)
            else:
                st.error(f"Page not found: {current_page}")
    
elif authentication_status is False:
    st.error('Username/password is incorrect')
elif authentication_status is None:
    st.warning('Please enter your username and password')
