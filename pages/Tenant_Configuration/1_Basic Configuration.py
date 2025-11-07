import streamlit as st
from legacy_session_state import legacy_session_state
legacy_session_state()
from extras import (profile_picture,price_note,loan_type,default_job_profile,alt_types,
                    post_locale, addDepartments,circ_other,circ_loanhist,export_profile,configure_tenant,ensure_address_types,
                    create_instance_for_analytics,verify_instance_exists,verify_instance_by_search,
                    post_holdings,get_holdings_id,post_inventory_item,post_loan_period,post_patron_notice_policy,
                    post_overdue_fines_policy,post_lost_item_fees_policy,
                    configure_portal_medad,configure_portal_marc,configure_portal_item_holding,
                    send_completion_email,add_auc_identifier_type,create_authority_source_file)
from Notices import send_notice
import time
import asyncio


hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_menu_style, unsafe_allow_html=True)

if 'allow_tenant' not in st.session_state:
    st.session_state['allow_tenant'] = False

# Don't initialize tenant values here - they should come from the Tenant connection form
# Initializing them to empty strings would overwrite existing values or hide connection issues

st.subheader("Basic Tenant Configuration")
st.caption("In order to start tenant configuration, kindly paste Medad ILS URL (ex: https://medad.ils.com) and click on start configuration button.")

if st.session_state.allow_tenant:
    # Validate that tenant connection info exists
    # Try widget-bound keys first, then fallback to copied keys
    tenant = st.session_state.get('tenant') or st.session_state.get('tenant_name')
    okapi = st.session_state.get('okapi') or st.session_state.get('okapi_url')
    token = st.session_state.get('token')
    
    # Check if values are truthy (not None, not empty string)
    if not tenant or not okapi or not token:
        st.error("⚠️ Tenant connection information is missing. Please go back to Tenant page and connect again.")
        with st.expander("🔍 Debug Info (Click to see details)"):
            st.write(f"**allow_tenant:** {st.session_state.get('allow_tenant')}")
            st.write(f"**tenant:** `{st.session_state.get('tenant')}` or `{st.session_state.get('tenant_name')}` (widget: {'tenant' in st.session_state}, copied: {'tenant_name' in st.session_state})")
            st.write(f"**okapi:** `{st.session_state.get('okapi')}` or `{st.session_state.get('okapi_url')}` (widget: {'okapi' in st.session_state}, copied: {'okapi_url' in st.session_state})")
            st.write(f"**token:** {'Present' if token else 'Missing'} (exists in session: {'token' in st.session_state})")
            st.write(f"**username_tenant:** `{st.session_state.get('username_tenant')}` or `{st.session_state.get('tenant_username')}`")
        st.info("💡 **To fix this:**\n1. Go to **Tenant** page (in sidebar)\n2. Enter **Tenant Name**, **Username**, **Password**\n3. Select **Okapi URL** from dropdown\n4. Click **Connect** button\n5. Wait for **'Connected! ✅'** success message\n6. Then return to this page")
    else:
        st.text_input('Client URL',key='clienturl')
        c1, c2 = st.columns(2)
        with c1:
            st.selectbox('TimeZone',
                         options=('Asia/Kuwait', 'Asia/Riyadh', 'Asia/Bahrain', 'Asia/Dubai', 'Asia/Muscat', 'Asia/Qatar'),
                         key='Timezone')


        with c2:



            st.selectbox('Currency',options=('KWD','SAR','BHD','AED','OMR','QAR'),key='currency')


        start = st.button("Start")
        if 'btn2' not in st.session_state:
            st.session_state['btn2'] = False

        if st.session_state.get('start_btn') != True:
            st.session_state.start_btn = start

        if start:
            if st.session_state.start_btn is True:
                tenant_name = st.session_state.get('tenant', 'Unknown')
                
                # List of configuration steps
                config_steps = [
                    "Creating Instance",
                    "Creating Holdings",
                    "Creating Inventory Item",
                    "Configuring Loan Period",
                    "Configuring Overdue Fines Policy",
                    "Configuring Lost Item Fees Policy",
                    "Configuring Patron Notice Policy",
                    "Sending Notices",
                    "Configuring Tenant Settings",
                    "Setting Up Price Notes",
                    "Creating Loan Types",
                    "Configuring Default Job Profile",
                    "Adding Alternative Title Types",
                    "Adding Departments",
                    "Adding AUC ID Identifier Type",
                    "Creating Authority Source File",
                    "Setting Locale & Currency",
                    "Configuring Circulation Other Settings",
                    "Configuring Loan History",
                    "Setting Up Export Profile",
                    "Configuring Profile Pictures",
                    "Configuring Portal Medad",
                    "Configuring Portal MARC",
                    "Configuring Portal Item/Holding"
                ]
                
                configured_items = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_steps = len(config_steps)
                
                def update_progress(step, item_name):
                    """Update progress bar and status"""
                    progress = (step + 1) / total_steps
                    progress_bar.progress(progress)
                    status_text.text(f"Step {step + 1}/{total_steps}: {config_steps[step]}")
                    if item_name:
                        configured_items.append(item_name)
                
                # Steps 1-4: Create suppressed test record structure for Analytics
                # This creates a dummy Instance → Holdings → Inventory Item
                # All marked with discoverySuppress=True to enable analytics functionality
                # This is required for FOLIO Analytics module to work properly
                
                # Step 1: Create Instance directly (suppressed, title "kamautomation")
                update_progress(0, "Creating Instance")
                instance_id = create_instance_for_analytics()
                
                # Wait a moment for indexing
                time.sleep(2)
                
                if instance_id:
                    # Verify instance actually exists by direct GET
                    if verify_instance_exists(instance_id):
                        configured_items.append("Instance")
                    else:
                        # Try to find it via search as fallback
                        found_id = verify_instance_by_search()
                        if found_id:
                            configured_items.append("Instance")
                            instance_id = found_id  # Use the found ID for subsequent operations
                        else:
                            configured_items.append("Instance (not found)")
                            instance_id = None  # Set to None so holdings/item won't be created
                else:
                    pass  # Continue silently
                time.sleep(1)
                
                # Step 2: Create Holdings (suppressed, linked to instance, location optional)
                if instance_id:
                    update_progress(1, "Creating Holdings")
                    holdings_success = post_holdings(instance_id)
                    if holdings_success:
                        configured_items.append("Holdings")
                    time.sleep(1)
                    
                    # Step 3: Get Holdings ID
                    holding_id = get_holdings_id(instance_id)
                    
                    # Step 4: Create Inventory Item (suppressed, location/material type optional)
                    if holding_id:
                        update_progress(2, "Creating Inventory Item")
                        item_success = post_inventory_item(holding_id)
                        if item_success:
                            configured_items.append("Inventory Item")
                    time.sleep(1)
                else:
                    # If instance creation failed, skip holdings and item
                    update_progress(1, "Holdings (skipped)")
                    update_progress(2, "Inventory Item (skipped)")
                time.sleep(1)
                
                # Step 5: Configure Loan Period
                update_progress(3, "Loan Period Policy")
                post_loan_period()
                time.sleep(1)
                
                # Step 6: Configure Overdue Fines Policy
                update_progress(4, "Overdue Fines Policy")
                post_overdue_fines_policy()
                time.sleep(1)
                
                # Step 7: Configure Lost Item Fees Policy
                update_progress(5, "Lost Item Fees Policy")
                post_lost_item_fees_policy()
                time.sleep(1)
                
                # Step 8: Configure Patron Notice Policy
                update_progress(6, "Patron Notice Policy")
                post_patron_notice_policy()
                time.sleep(1)
                
                # Step 9: Send Notices
                update_progress(7, "Notices")
                send_notice()
                time.sleep(1)
                
                # Steps 10-19: Async operations
                update_progress(8, "Tenant Configuration")
                async def main():
                    tasks = [
                        configure_tenant(),
                        ensure_address_types(),
                        price_note(),
                        loan_type(),
                        default_job_profile(),
                        alt_types(),
                        addDepartments(),
                        add_auc_identifier_type(),
                        post_locale(st.session_state.Timezone, st.session_state.currency),
                        circ_other(),
                        circ_loanhist(),
                        export_profile(),
                        profile_picture()
                    ]
                    await asyncio.gather(*tasks)
                
                # Running the asyncio event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Update progress for async tasks
                loop.run_until_complete(main())
                configured_items.extend([
                    "Price Notes", "Loan Types", "Default Job Profile", 
                    "Alternative Title Types", "Departments", "AUC ID Identifier Type",
                    "Locale & Currency", "Circulation Other Settings", "Loan History", 
                    "Export Profile", "Profile Pictures"
                ])
                
                # Step: Create Authority Source File (separate to handle errors)
                update_progress(15, "Creating Authority Source File")
                authority_file_success, authority_file_error = loop.run_until_complete(create_authority_source_file())
                if authority_file_success:
                    configured_items.append("Authority Source File")
                else:
                    # Add error message to configured items and output log
                    configured_items.append(f"Authority Source File (ERROR: {authority_file_error})")
                time.sleep(1)
                
                # Portal Integration Steps
                update_progress(20, "Configuring Profile Pictures")
                # Profile Pictures is already executed in async tasks, just updating progress
                time.sleep(1)
                
                update_progress(21, "Configuring Portal Medad")
                portal_medad_result = loop.run_until_complete(configure_portal_medad())
                if portal_medad_result:
                    configured_items.append("Portal Medad Configuration")
                time.sleep(1)
                
                update_progress(22, "Configuring Portal MARC")
                portal_marc_result = loop.run_until_complete(configure_portal_marc())
                if portal_marc_result:
                    configured_items.append("Portal MARC Configuration")
                time.sleep(1)
                
                update_progress(23, "Configuring Portal Item/Holding")
                portal_item_result = loop.run_until_complete(configure_portal_item_holding())
                if portal_item_result:
                    configured_items.append("Portal Item/Holding Configuration")
                time.sleep(1)
                
                # Complete progress
                progress_bar.progress(1.0)
                status_text.text("Configuration Complete!")
                
                # Show summary
                st.success("✅ Tenant is now Configured", icon="✅")
                st.session_state['btn2'] = True
                
                # Display summary of configured items
                output_log = "### Successfully Configured:\n"
                error_section = ""
                for item in configured_items:
                    if "ERROR:" in item:
                        # Extract error message
                        error_section += f"❌ {item}\n"
                        output_log += f"❌ {item}\n"
                    else:
                        output_log += f"✅ {item}\n"
                
                # Add error section if there are errors
                if error_section:
                    output_log += "\n### ⚠️ Errors/Warnings:\n"
                    output_log += error_section
                    output_log += "\n**Note:** Please contact the infrastructure team regarding the authority source file error.\n"
                
                with st.expander("📋 Configuration Summary", expanded=True):
                    st.markdown(output_log)
                
                # Send email notification
                st.info("📧 Sending email notification...")
                email_sent = send_completion_email("Basic", output_log, tenant_name)
                if email_sent:
                    st.success("✅ Email notification sent successfully!")
                else:
                    st.warning("⚠️ Email notification could not be sent. Please check logs.")

else:
    st.warning("Please Connect to Tenant First.")
