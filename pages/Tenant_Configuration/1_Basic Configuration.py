import streamlit as st
from legacy_session_state import legacy_session_state
legacy_session_state()
import importlib
import extras
import json
import logging
import requests

extras = importlib.reload(extras)

from extras import (profile_picture,price_note,loan_type,default_job_profile,alt_types,
                    post_locale, addDepartments,circ_other,circ_loanhist,export_profile,configure_tenant,
                    create_instance_for_analytics,verify_instance_exists,verify_instance_by_search,
                    post_holdings,get_holdings_id,post_inventory_item,post_loan_period,post_patron_notice_policy,
                    post_overdue_fines_policy,post_lost_item_fees_policy,
                    configure_portal_medad,configure_portal_marc,configure_portal_item_holding,
                    send_completion_email,add_auc_identifier_type,create_authority_source_file,
                    fetch_help_url_status,fetch_address_types_status,fetch_dummy_location_status)
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

if 'basic_config_summary' not in st.session_state:
    st.session_state['basic_config_summary'] = None

if st.session_state.allow_tenant:
    # Validate that tenant connection info exists
    # Try widget-bound keys first, then fallback to copied keys
    tenant = st.session_state.get('tenant') or st.session_state.get('tenant_name')
    okapi = st.session_state.get('okapi') or st.session_state.get('okapi_url')
    token = st.session_state.get('token')

    # Ensure keys exist for downstream functions that expect them
    if (st.session_state.get('tenant') in [None, '']) and tenant:
        st.session_state['tenant'] = tenant
    if (st.session_state.get('okapi') in [None, '']) and okapi:
        st.session_state['okapi'] = okapi
    if (st.session_state.get('token') in [None, '']) and token:
        st.session_state['token'] = token
    
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
            st.session_state['basic_config_summary'] = None
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
                
                summary_entries = []
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                total_steps = len(config_steps)
                
                def update_progress(step, item_name):
                    """Update progress bar and status"""
                    progress = (step + 1) / total_steps
                    progress_bar.progress(progress)
                    status_text.text(f"Step {step + 1}/{total_steps}: {config_steps[step]}")

                def add_summary(status, message, detail=None):
                    summary_entries.append({
                        "status": status,
                        "message": message,
                        "detail": detail
                    })

                def verify_marc_templates_inline():
                    tenant = st.session_state.get('tenant') or st.session_state.get('tenant_name')
                    okapi = st.session_state.get('okapi') or st.session_state.get('okapi_url')
                    token = st.session_state.get('token')
                    if not all([tenant, okapi, token]):
                        return False, "Missing tenant info"

                    normalized_fn = getattr(extras, "_get_normalized_templates", None)
                    if callable(normalized_fn):
                        definitions = normalized_fn()
                    else:
                        definitions = getattr(extras, "MARC_TEMPLATE_DEFINITIONS", [])
                    module_config = getattr(extras, "MARC_TEMPLATE_MODULE_CONFIG", {})

                    if not definitions:
                        raw_json = getattr(extras, "MARC_TEMPLATES_JSON", None)
                        if raw_json:
                            try:
                                definitions = json.loads(raw_json)
                            except json.JSONDecodeError:
                                logging.error("Failed to parse MARC_TEMPLATES_JSON fallback")
                                definitions = []

                    if not module_config and hasattr(extras, "MARC_TEMPLATE_MODULE_CONFIG"):
                        module_config = getattr(extras, "MARC_TEMPLATE_MODULE_CONFIG")

                    if not definitions or not module_config:
                        return False, "Template metadata unavailable"

                    templates_by_module = {}
                    for template in definitions:
                        module = template.get("module")
                        if not module:
                            continue
                        templates_by_module.setdefault(module, 0)
                        templates_by_module[module] += 1

                    headers = {
                        "x-okapi-tenant": tenant,
                        "x-okapi-token": token,
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }

                    timeout = getattr(extras, "DEFAULT_TIMEOUT", 60)
                    status = {}
                    overall_success = True

                    for module, module_cfg in module_config.items():
                        list_query = (
                            f"{okapi}/configurations/entries?query=(module=={module} and "
                            f"configName=={module_cfg['list_config']})"
                        )

                        try:
                            resp = requests.get(list_query, headers=headers, timeout=timeout)
                        except Exception as exc:
                            logging.error("Failed to fetch %s template list status: %s", module, exc)
                            status[module] = {"error": str(exc)}
                            overall_success = False
                            continue

                        if resp.status_code != 200:
                            logging.error(
                                "Failed to fetch %s template list: %s - %s",
                                module,
                                resp.status_code,
                                resp.text[:200]
                            )
                            status[module] = {"error": f"HTTP {resp.status_code}"}
                            overall_success = False
                            continue

                        data = resp.json()
                        configs = data.get("configs") or []
                        entry_count = len(configs)

                        template_count = 0
                        if configs:
                            raw_value = configs[0].get("value") or "[]"
                            try:
                                parsed_list = json.loads(raw_value)
                            except json.JSONDecodeError:
                                logging.error("Template list JSON malformed for module %s", module)
                                parsed_list = []
                                overall_success = False
                            template_count = len(parsed_list) if isinstance(parsed_list, list) else 0

                        expected_count = templates_by_module.get(module, 0)
                        module_status = {
                            "configs": entry_count,
                            "templates": template_count,
                            "expected": expected_count
                        }

                        if template_count < expected_count:
                            module_status["missing"] = expected_count - template_count
                            overall_success = False

                        status[module] = module_status

                    return overall_success, status
                
                # Steps 1-4: Create suppressed test record structure for Analytics
                # This creates a dummy Instance → Holdings → Inventory Item
                # All marked with discoverySuppress=True to enable analytics functionality
                # This is required for FOLIO Analytics module to work properly
                
                # Step 1: Create Instance directly (suppressed, title "kamautomation")
                update_progress(0, "Creating Instance")
                instance_id = None
                try:
                    instance_id = create_instance_for_analytics()
                except Exception as exc:
                    logging.exception("Instance creation failed")
                    add_summary('error', 'Instance creation', str(exc))

                # Wait a moment for indexing
                time.sleep(2)

                if instance_id:
                    try:
                        if verify_instance_exists(instance_id):
                            add_summary('success', 'Instance created', instance_id)
                        else:
                            found_id = verify_instance_by_search()
                            if found_id:
                                add_summary('success', 'Instance created (via search)', found_id)
                                instance_id = found_id
                            else:
                                add_summary('error', 'Instance creation', 'Instance not found after creation attempt')
                                instance_id = None
                    except Exception as exc:
                        logging.exception("Instance verification failed")
                        add_summary('warning', 'Instance verification', str(exc))
                        instance_id = None
                else:
                    add_summary('error', 'Instance creation', 'No instance ID returned')
                time.sleep(1)
                
                # Step 2: Create Holdings (suppressed, linked to instance, location optional)
                if instance_id:
                    update_progress(1, "Creating Holdings")
                    try:
                        holdings_success = post_holdings(instance_id)
                        if holdings_success:
                            add_summary('success', 'Holdings created')
                        else:
                            add_summary('warning', 'Holdings creation', 'Holdings API call failed')
                    except Exception as exc:
                        logging.exception("Holdings creation failed")
                        add_summary('error', 'Holdings creation', str(exc))
                        holdings_success = False
                    time.sleep(1)

                    # Step 3: Get Holdings ID
                    holding_id = None
                    try:
                        holding_id = get_holdings_id(instance_id)
                    except Exception as exc:
                        logging.exception("Holdings verification failed")
                        add_summary('error', 'Holdings verification', str(exc))

                    if not holding_id:
                        add_summary('warning', 'Holdings verification', 'Holdings record not found after creation')

                    # Step 4: Create Inventory Item (suppressed, location/material type optional)
                    if holding_id:
                        update_progress(2, "Creating Inventory Item")
                        try:
                            item_success = post_inventory_item(holding_id)
                            if item_success:
                                add_summary('success', 'Inventory item created')
                            else:
                                add_summary('warning', 'Inventory item creation', 'Item API call failed')
                        except Exception as exc:
                            logging.exception("Inventory item creation failed")
                            add_summary('error', 'Inventory item creation', str(exc))
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
                    task_defs = [
                        ("Tenant configuration", configure_tenant()),
                        ("Price note type", price_note()),
                        ("Loan type", loan_type()),
                        ("Default job profile", default_job_profile()),
                        ("Alternative title types", alt_types()),
                        ("Departments", addDepartments()),
                        ("AUC identifier type", add_auc_identifier_type()),
                        ("Locale & currency", post_locale(st.session_state.Timezone, st.session_state.currency)),
                        ("Circulation other settings", circ_other()),
                        ("Circulation loan history", circ_loanhist()),
                        ("Export profile", export_profile()),
                        ("Profile picture config", profile_picture()),
                    ]
                    marc_templates_fn = getattr(extras, "ensure_marc_templates", None)
                    if marc_templates_fn:
                        task_defs.append(("MARC templates", marc_templates_fn()))
                    else:
                        add_summary('warning', 'MARC templates', 'Routine not available in this build')
                    ensure_address_types_fn = getattr(extras, "ensure_address_types", None)
                    if ensure_address_types_fn:
                        task_defs.append(("Address types", ensure_address_types_fn()))
                    else:
                        add_summary('warning', 'Address types', 'Routine not available in this build')

                    if not task_defs:
                        return []

                    names, coroutines = zip(*task_defs)
                    results = await asyncio.gather(*coroutines, return_exceptions=True)
                    return list(zip(names, results))
                
                # Running the asyncio event loop
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                # Update progress for async tasks
                async_results = loop.run_until_complete(main())
                for task_name, task_result in async_results:
                    if isinstance(task_result, Exception):
                        add_summary('error', task_name, str(task_result))
                        continue

                    success = True
                    detail = None

                    if isinstance(task_result, tuple) and len(task_result) == 2:
                        success, detail = task_result
                    elif task_result not in (None, True):
                        detail = task_result

                    add_summary('success' if success else 'warning', task_name, detail)
                
                # Step: Create Authority Source File (separate to handle errors)
                update_progress(15, "Creating Authority Source File")
                authority_file_success, authority_file_error = loop.run_until_complete(create_authority_source_file())
                if authority_file_success:
                    add_summary('success', 'Authority source file created')
                else:
                    add_summary('error', 'Authority source file', authority_file_error)
                time.sleep(1)
                
                # Portal Integration Steps
                update_progress(20, "Configuring Profile Pictures")
                # Profile Pictures is already executed in async tasks, just updating progress
                time.sleep(1)
                
                update_progress(21, "Configuring Portal Medad")
                portal_medad_result = loop.run_until_complete(configure_portal_medad())
                if portal_medad_result:
                    add_summary('success', 'Portal Medad configuration applied')
                else:
                    add_summary('warning', 'Portal Medad configuration', 'Skipped or failed')
                time.sleep(1)
                
                update_progress(22, "Configuring Portal MARC")
                portal_marc_result = loop.run_until_complete(configure_portal_marc())
                if portal_marc_result:
                    add_summary('success', 'Portal MARC configuration applied')
                else:
                    add_summary('warning', 'Portal MARC configuration', 'Skipped or failed')
                time.sleep(1)
                
                update_progress(23, "Configuring Portal Item/Holding")
                portal_item_result = loop.run_until_complete(configure_portal_item_holding())
                if portal_item_result:
                    add_summary('success', 'Portal item/holding configuration applied')
                else:
                    add_summary('warning', 'Portal item/holding configuration', 'Skipped or failed')
                time.sleep(1)
                
                # Verification checks
                help_status, help_detail = fetch_help_url_status()
                if help_status:
                    add_summary('success', 'Help URL configured', help_detail)
                else:
                    add_summary('warning', 'Help URL configuration', help_detail)

                addr_status, addr_list = fetch_address_types_status()
                if addr_status:
                    add_summary('success', 'Address types present', addr_list or 'None')
                else:
                    add_summary('warning', 'Address types', 'Unable to verify address types')

                location_status, location_details = fetch_dummy_location_status()
                if location_status:
                    add_summary('success', 'Analytics location tree present')
                else:
                    if isinstance(location_details, dict):
                        detail_text = ", ".join(f"{k}: {'✅' if v else '❌'}" for k, v in location_details.items())
                    else:
                        detail_text = location_details
                    add_summary('warning', 'Analytics location tree incomplete', detail_text)

                templates_status_fn = getattr(extras, "fetch_marc_templates_status", None)
                if templates_status_fn:
                    try:
                        templates_status = templates_status_fn()
                    except Exception as exc:
                        logging.exception("MARC template verification failed")
                        add_summary('warning', 'MARC templates verification', str(exc))
                    else:
                        if templates_status:
                            tpl_ok, tpl_detail = templates_status
                            if tpl_ok:
                                add_summary('success', 'MARC templates verification', tpl_detail)
                            else:
                                add_summary('warning', 'MARC templates verification', tpl_detail)
                else:
                    tpl_ok, tpl_detail = verify_marc_templates_inline()
                    if tpl_ok:
                        add_summary('success', 'MARC templates verification', tpl_detail)
                    else:
                        add_summary('warning', 'MARC templates verification', tpl_detail)

                # Complete progress
                progress_bar.progress(1.0)
                status_text.text("Configuration Complete!")
                
                # Show summary
                st.success("✅ Tenant is now Configured", icon="✅")
                st.session_state['btn2'] = True
                
                icon_map = {
                    'success': '✅',
                    'warning': '⚠️',
                    'error': '❌',
                    'info': 'ℹ️'
                }

                summary_lines = []
                error_lines = []
                for entry in summary_entries:
                    icon = icon_map.get(entry['status'], '•')
                    detail = entry.get('detail')
                    if isinstance(detail, dict):
                        detail_text = json.dumps(detail, indent=2)
                    elif isinstance(detail, list):
                        detail_text = ', '.join(map(str, detail))
                    else:
                        detail_text = str(detail) if detail else ''

                    line = f"{icon} {entry['message']}"
                    if detail_text:
                        line += f" — {detail_text}"
                    summary_lines.append(line)
                    if entry['status'] == 'error':
                        error_lines.append(line)

                output_log = "### Summary\n" + "\n".join(summary_lines)

                if error_lines:
                    output_log += "\n\n### ⚠️ Errors/Warnings\n" + "\n".join(error_lines)
                    output_log += "\n\n**Note:** Please contact the infrastructure team regarding the errors above.**"
                
                st.session_state['basic_config_summary'] = output_log
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

if st.session_state.allow_tenant:
    previous_summary = st.session_state.get('basic_config_summary')
    if previous_summary:
        with st.expander("📋 Last Configuration Summary", expanded=False):
            st.markdown(previous_summary)
