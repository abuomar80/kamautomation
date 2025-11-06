from Upload import upload_file
import streamlit as st
from Material_types import mtypes
from Statistical_Codes import stat_types
from user_group import user_groups
from Department import dept
from Location import loc
from Calendar import calendar, exceptions
from Column_Configuration import columns_config
from legacy_session_state import legacy_session_state
from template_generator import download_template_button
from extras import send_completion_email
legacy_session_state()

if 'allow_tenant' not in st.session_state:
    st.session_state['allow_tenant'] = False

if 'allow_calendar' not in st.session_state:
    st.session_state['allow_calendar'] = False

hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_menu_style, unsafe_allow_html=True)
# st.session_state.update(st.session_state)
st.subheader('Advanced Configuration')
# if st.session_state.allow_tenant:
st.caption('Kindly Upload the Master Profilling document and insure all the sheets are filled properly!')

# Download template section
with st.expander("📥 Download Excel Template", expanded=False):
    st.markdown("""
    **Instructions:**
    1. Download the Excel template using the button below
    2. Fill in all the required sheets with your data
    3. Make sure all sheet names match exactly (case-sensitive)
    4. Upload the completed file in the Upload tab
    """)
    download_template_button()
    st.markdown("""
    **Required Sheets (in exact order):**
    1. **Material_Types** - Columns: `Legacy System`, `Description`, `Medad`
    2. **Statistical_Codes** - Columns: `Medad Statistical Type`, `Medad Statistical Code`
    3. **Item_status** - Columns: `Status`, `Code`
    4. **User_groups** - Columns: `Legacy System` (optional), `Description` (optional, defaults to Medad), `Medad` (required - Patron group name)
       - ⚠️ **Note:** User groups are independent. Departments are loaded separately from the Department sheet.
    5. **Location** - Columns: `ServicePoints name`, `ServicePoints Codes`, `InstitutionsName`, `InstitutionsCodes`, `CampusNames`, `CampusCodes`, `LibrariesName`, `LibrariesCodes`, `LocationsName`, `LocationsCodes`
    6. **Calendar** - Columns: `ServicePoints name`, `start`, `end`
    7. **Calendar Exceptions** - Columns: `ServicePoints name`, `name`, `startDate`, `endDate`, `allDay`
    8. **Department** - Columns: `Name`, `Code` (Optional - can also be defined in User_groups sheet)
    """)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["Upload", "Material Types", "Statistical Codes", "User Groups",
                                                          "Location", "Departments", "Calendar", "Exceptions", "Configuration Columns"])

with tab1:
    if st.session_state.allow_tenant:
        upload_file()
    else:
        st.warning("Please Connect to Tenant First.")


with tab2:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            mtypes()
    else:
        st.warning("Please Connect to Tenant First.")

with tab3:
    if st.session_state.allow_tenant:

        if st.session_state.profiling is not None and st.session_state['key'] is True:
            stat_types()
    else:
        st.warning("Please Connect to Tenant First.")

with tab4:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            if 'Disdur' not in st.session_state:
                st.session_state.Disdur=False

            col1, col2 = st.columns(2)
            with col1:
                st.slider('Expiration Duration Offset', min_value=1, max_value=360, value=None, key='offsetduration',disabled=st.session_state.Disdur)
            with col2:
                st.checkbox('Disable Expiration Duration Offset',value=False, key='Disdur')
            user_groups()
    else:
        st.warning("Please Connect to Tenant First.")


with tab5:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            loc()
    else:
        st.warning("Please Connect to Tenant First.")

with tab6:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            dept()
    else:
        st.warning("Please Connect to Tenant First.")
with tab7:
    if st.session_state.allow_tenant:
    #     if st.session_state.profiling is not None and st.session_state['key'] is True:
        calendar()
    else:
        st.warning("Please Connect to Tenant First.")

with tab8:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            exceptions()
    else:
        st.warning("Please Connect to Tenant First.")
with tab9:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            columns_config()
    else:
        st.warning("Please Connect to Tenant First.")

# Completion Notification Section
st.markdown("---")
if st.session_state.allow_tenant:
    tenant_name = st.session_state.get('tenant', 'Unknown')
    
    st.subheader("📧 Configuration Completion")
    st.caption("Once you have completed all Advanced Configuration steps, click the button below to send a completion notification email.")
    
    if st.button("📬 Send Advanced Configuration Completion Email", type="primary"):
        # Create summary of configured items
        configured_items = []
        
        if st.session_state.profiling is not None and st.session_state.get('key', False):
            configured_items.append("✅ Excel file uploaded and processed")
            configured_items.append("✅ Material Types configured")
            configured_items.append("✅ Statistical Codes configured")
            configured_items.append("✅ User Groups configured")
            configured_items.append("✅ Locations configured")
            configured_items.append("✅ Departments configured")
            configured_items.append("✅ Calendar configured")
            configured_items.append("✅ Calendar Exceptions configured")
            configured_items.append("✅ Column Configuration set up")
        else:
            configured_items.append("⚠️ Please ensure all tabs are completed before sending notification")
        
        output_log = "### Advanced Configuration Summary:\n\n"
        for item in configured_items:
            output_log += f"{item}\n"
        
        # Send email notification
        with st.spinner("Sending email notification..."):
            email_sent = send_completion_email("Advanced", output_log, tenant_name)
        
        if email_sent:
            st.success("✅ Email notification sent successfully!")
        else:
            st.warning("⚠️ Email notification could not be sent. Please check logs.")
else:
    st.warning("Please Connect to Tenant First.")
