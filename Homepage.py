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
    if st.session_state.get('authentication_status') is not True:
        from PIL import Image
        logo = Image.open("medad_logo_eng.png")
        st.image(logo, width=200)
        st.markdown("<h1 style='text-align:center;margin-top:0;'>Medad Automation Tools</h1>", unsafe_allow_html=True)
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
    
    # Use custom navigation that works reliably with forms and dynamic page loading
    # st.navigation has issues with form submit buttons and widget key conflicts
    # when pages are loaded dynamically, so we use custom navigation instead
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
        # Create grouped sections with headers
        st.sidebar.markdown(f"**{group_name}**")
        group_available = {}
        for page_name, page_path in pages.items():
            if os.path.exists(page_path):
                group_available[page_name] = page_path
                # Use a simple, unique button key based on page path
                # Replace special chars to make a valid key
                safe_group = group_name.replace(" ", "_").replace("📁", "").replace("📦", "").replace("⚙️", "")
                safe_page = page_name.replace(" ", "_")
                button_key = f"nav_{safe_group}_{safe_page}"
                button_type = "primary" if st.session_state.get('current_page') == page_path else "secondary"
                # Use smaller buttons without use_container_width
                clicked = st.sidebar.button(page_name, key=button_key, use_container_width=False, type=button_type)
                if clicked:
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
