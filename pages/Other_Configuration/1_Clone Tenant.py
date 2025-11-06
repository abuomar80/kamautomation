import streamlit as st
import json
import requests
from clone_functions import moveSettings, movelocations, movecircpolicies, movecircrules

# Note: st.set_page_config() is removed as it's already set in Homepage.py

if 'allow_tenant_1' not in st.session_state:
    st.session_state['allow_tenant_1'] = False

if 'allow_tenant_2' not in st.session_state:
    st.session_state['allow_tenant_2'] = False


def tenantlogin(okapi, tenant, username, password):
    myobj = {"username": username, "password": password}
    data = json.dumps(myobj)
    header = {"x-okapi-tenant": tenant}

    x = requests.post(okapi + "/authn/login", data=data, headers=header)
    if "x-okapi-token" in x.headers:
        token = x.headers["x-okapi-token"]
        st.success("Connected! ✅", icon="✅")
        return token
    else:
        st.error("Please check the Tenant information", icon="🚨")
        return None


st.title("🔄 Clone Existing Tenant")
st.caption('Copy settings from a Master Tenant to a Clone Tenant')

# Filters
st.sidebar.write("**ILS Settings Selections:**")
patron_groups = st.sidebar.checkbox("Move Patron Groups")
Service_Points = st.sidebar.checkbox("Move Service Points")
due_dates = st.sidebar.checkbox("Move Fixed Due Dates")
Location_tree = st.sidebar.checkbox("Move Location Hierarchy")
loan_types = st.sidebar.checkbox("Move Loan Types")
loan_policy = st.sidebar.checkbox("Move Loan/Request Policy")
over_policy = st.sidebar.checkbox("Move Overdue/Lost Policy")
Notices = st.sidebar.checkbox("Move Notice Templates")
staff_slips = st.sidebar.checkbox("Move Staff Slips")
Circ_rules = st.sidebar.checkbox("Move Circulation Rules")

dev1, dev2 = st.columns(2)

with dev1:
    st.subheader("📥 Master Tenant (Source)")
    st.caption('This is the Master Tenant where all the settings will be transferred from')

    with st.form("Master"):
        st.text_input("Enter Tenant Username:", key="username_tenant_1", placeholder="Please enter your username")
        st.text_input("Enter Tenant Password:", key="password_1", placeholder="Please enter your password", type='password')
        st.text_input("Enter Tenant Name:", placeholder="Please enter tenant name", key="tenant_1")
        st.selectbox(
            "Select Okapi URL:",
            ("https://api02-v1.ils.medad.com", "https://api01-v1.ils.medad.com", "https://api01-v1-uae.ils.medad.com"),
            key="okapi_1",
        )
        submitted_3 = st.form_submit_button("Connect", type="primary")
        if submitted_3:
            token = tenantlogin(
                st.session_state.okapi_1,
                st.session_state.tenant_1,
                st.session_state.username_tenant_1,
                st.session_state.password_1,
            )
            if token:
                st.session_state.token_1 = token
                st.session_state.allow_tenant_1 = True

with dev2:
    st.subheader("📤 Clone Tenant (Destination)")
    st.caption('This is the Cloned tenant where all the settings will be implemented')

    with st.form("cloned"):
        st.text_input("Enter Tenant Username:", key="username_tenant_2", placeholder="Please enter your username")
        st.text_input("Enter Tenant Password:", key="password_2", placeholder="Please enter your password", type='password')
        st.text_input("Enter Tenant Name:", placeholder="Please enter tenant name", key="tenant_2")
        st.selectbox(
            "Select Okapi URL:",
            ("https://api02-v1.ils.medad.com", "https://api01-v1.ils.medad.com", "https://api01-v1-uae.ils.medad.com"),
            key="okapi_2",
        )
        submitted_1 = st.form_submit_button("Connect", type="primary")
        if submitted_1:
            token = tenantlogin(
                st.session_state.okapi_2,
                st.session_state.tenant_2,
                st.session_state.username_tenant_2,
                st.session_state.password_2,
            )
            if token:
                st.session_state.token_2 = token
                st.session_state.allow_tenant_2 = True

# Clone button
if st.session_state.get('allow_tenant_1') and st.session_state.get('allow_tenant_2'):
    st.divider()
    proceed = st.button("🚀 Clone it", type="primary", use_container_width=True)
    
    if proceed:
        fetchHeaders = {
            'x-okapi-tenant': st.session_state.tenant_1,
            'x-okapi-token': st.session_state.token_1
        }
        postHeaders = {
            'x-okapi-tenant': st.session_state.tenant_2,
            'x-okapi-token': st.session_state.token_2,
            'Content-Type': 'application/json'
        }
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        steps = []
        
        if patron_groups:
            steps.append("Moving Patron Groups")
        if Service_Points:
            steps.append("Moving Service Points")
        if due_dates:
            steps.append("Moving Fixed Due Dates")
        if Location_tree:
            steps.append("Moving Location Hierarchy")
        if loan_types:
            steps.append("Moving Loan Types")
        if loan_policy:
            steps.append("Moving Loan/Request Policies")
        if over_policy:
            steps.append("Moving Overdue/Lost Policies")
        if Notices:
            steps.append("Moving Notice Templates")
        if staff_slips:
            steps.append("Moving Staff Slips")
        if Circ_rules:
            steps.append("Moving Circulation Rules")
        
        total_steps = len(steps)
        
        with st.spinner("Cloning tenant settings..."):
            step_idx = 0
            
            if patron_groups:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Patron Groups...")
                moveSettings("/groups?limit=1000", "/groups/", "usergroups", st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if Service_Points:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Service Points...")
                moveSettings("/service-points?limit=100", "/service-points/", "servicepoints", st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if due_dates:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Fixed Due Dates...")
                moveSettings("/fixed-due-date-schedule-storage/fixed-due-date-schedules?limit=1000",
                             "/fixed-due-date-schedule-storage/fixed-due-date-schedules/", "fixedDueDateSchedules", 
                             st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if Location_tree:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Location Hierarchy...")
                movelocations(st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if loan_types:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Loan Types...")
                moveSettings("/loan-types?limit=500", "/loan-types/", "loantypes", st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if loan_policy:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Loan/Request Policies...")
                movecircpolicies("/loan-policy-storage/loan-policies?limit=100", "/loan-policy-storage/loan-policies/",
                                "loanPolicies", st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                movecircpolicies("/fixed-due-date-schedule-storage/fixed-due-date-schedules?limit=100",
                                "/fixed-due-date-schedule-storage/fixed-due-date-schedules/", "fixedDueDateSchedules",
                                st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                movecircpolicies("/request-policy-storage/request-policies?limit=100",
                                "/request-policy-storage/request-policies/", "requestPolicies", 
                                st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if over_policy:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Overdue/Lost Policies...")
                movecircpolicies("/overdue-fines-policies?limit=100", "/overdue-fines-policies/", "overdueFinePolicies",
                                st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                movecircpolicies("/lost-item-fees-policies?limit=100", "/lost-item-fees-policies/",
                                "lostItemFeePolicies", st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if Notices:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Notice Templates...")
                movecircpolicies("/templates?query=active==true&limit=100", "/templates/", "templates",
                                st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                movecircpolicies("/patron-notice-policy-storage/patron-notice-policies?limit=100",
                                "/patron-notice-policy-storage/patron-notice-policies/", "patronNoticePolicies",
                                st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if staff_slips:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Staff Slips...")
                movecircpolicies("/staff-slips-storage/staff-slips", "/staff-slips-storage/staff-slips/", "staffSlips",
                                st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)

            if Circ_rules:
                status_text.text(f"Step {step_idx + 1}/{total_steps}: Moving Circulation Rules...")
                movecircrules("/circulation/rules", "rulesAsText", st.session_state.okapi_1, st.session_state.okapi_2, fetchHeaders, postHeaders)
                step_idx += 1
                progress_bar.progress(step_idx / total_steps)
        
        progress_bar.progress(1.0)
        status_text.text("✅ Cloning Complete!")
        st.success("🎉 Tenant cloning completed successfully!")
        
elif not st.session_state.get('allow_tenant_1'):
    st.info("👆 Please connect to the Master Tenant first.")
elif not st.session_state.get('allow_tenant_2'):
    st.info("👆 Please connect to the Clone Tenant first.")
