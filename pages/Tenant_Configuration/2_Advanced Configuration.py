from Upload import upload_file
import streamlit as st
from Material_types import mtypes
from Statistical_Codes import stat_types
from user_group import user_groups
from Department import dept
from Location import loc
from Calendar import calendar, exceptions
from Column_Configuration import columns_config
from FeeFineOwner import fee_fine_owner
from FeeFine import fee_fine
from Waives import waives
from ManualCharges import manual_charges
from PaymentMethods import payment_methods
from Refunds import refunds
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
            /* Horizontal scrolling for tabs */
            .stTabs [data-baseweb="tab-list"] {
                gap: 2px;
                overflow-x: auto;
                overflow-y: hidden;
                flex-wrap: nowrap;
                -webkit-overflow-scrolling: touch;
                scrollbar-width: thin;
            }
            .stTabs [data-baseweb="tab"] {
                height: 50px;
                white-space: nowrap;
                padding-left: 20px;
                padding-right: 20px;
                flex-shrink: 0;
            }
            /* Custom scrollbar styling */
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar {
                height: 8px;
            }
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-track {
                background: #f1f1f1;
                border-radius: 10px;
            }
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 10px;
            }
            .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
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
    9. **FeeFineOwner** - Columns: `Service Points` (use service point name/label, or "ALL" for all service points), `Owner` (owner ID/name)
       - ⚠️ **Note:** Fee/fine Owner requires service points to be created first (complete Location tab)
       - Use service point **names** (labels), not UUIDs
       - Use "ALL" to assign an owner to all service points
    10. **FeeFine** - Columns: `feeFineType` (required), `amountWithoutVat` (required, numeric), `vat` (optional, numeric), `owner` (required, references Owner from FeeFineOwner sheet), `automatic` (optional, true/false), `id` (optional, leave empty to auto-generate)
       - ⚠️ **Note:** Fee/fine requires owners to be created first (complete Fee/Fine Owner tab)
       - The `owner` column should match the `Owner` values from the FeeFineOwner sheet
    11. **Waives** - Columns: `nameReason` (required), `id` (optional, leave empty to auto-generate)
       - Each row creates one waive record
       - Loops through all rows to create multiple waives
    12. **ManualCharges** - Columns: `nameReason` (required), `id` (optional, leave empty to auto-generate)
       - Each row creates one manual charge record
       - Loops through all rows to create multiple manual charges
    13. **PaymentMethods** - Columns: `nameMethod` (required), `allowedRefundMethod` (optional, true/false, default: false), `owner` (required, references Owner from FeeFineOwner sheet), `id` (optional, leave empty to auto-generate)
       - ⚠️ **Note:** Payment methods require owners to be created first (complete Fee/Fine Owner tab)
       - The `owner` column should match the `Owner` values from the FeeFineOwner sheet
       - Each row creates one payment method record
       - Loops through all rows to create multiple payment methods
    14. **Refunds** - Columns: `nameReason` (required), `id` (optional, leave empty to auto-generate)
       - Each row creates one refund record
       - Loops through all rows to create multiple refunds
    """)

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15 = st.tabs(["Upload", "Material Types", "Statistical Codes", "User Groups",
                                                          "Location", "Departments", "Calendar", "Exceptions", "Configuration Columns", "Fee/Fine Owner", "Fee/Fine", "Waives", "Manual Charges", "Payment Methods", "Refunds"])

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

with tab10:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            # Check if Location tab has been completed (service points exist)
            fee_fine_owner()
    else:
        st.warning("Please Connect to Tenant First.")

with tab11:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            # Check if Fee/Fine Owner tab has been completed (owners exist)
            fee_fine()
    else:
        st.warning("Please Connect to Tenant First.")

with tab12:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            waives()
    else:
        st.warning("Please Connect to Tenant First.")

with tab13:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            manual_charges()
    else:
        st.warning("Please Connect to Tenant First.")

with tab14:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            # Check if Fee/Fine Owner tab has been completed (owners exist)
            payment_methods()
    else:
        st.warning("Please Connect to Tenant First.")

with tab15:
    if st.session_state.allow_tenant:
        if st.session_state.profiling is not None and st.session_state['key'] is True:
            refunds()
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
            configured_items.append("✅ Fee/Fine Owner configured")
            configured_items.append("✅ Fee/Fine configured")
            configured_items.append("✅ Waives configured")
            configured_items.append("✅ Manual Charges configured")
            configured_items.append("✅ Payment Methods configured")
            configured_items.append("✅ Refunds configured")
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
