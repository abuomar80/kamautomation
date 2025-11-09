import streamlit as st
import requests
import json
from typing import Dict, List, Optional, Set, Tuple
from legacy_session_state import legacy_session_state
import string
import secrets
from permissions import apiperm, fullperms, circ, Acquisition, cataloging, admins, search, sip

legacy_session_state()

if 'allow_tenant' not in st.session_state:
    st.session_state['allow_tenant'] = False

# Initialize tenant-related session state variables if not set
# Check both widget-bound keys and copied keys (from form submission)
if 'tenant' not in st.session_state or not st.session_state.get('tenant'):
    st.session_state['tenant'] = st.session_state.get('tenant_name', '')
if 'okapi' not in st.session_state or not st.session_state.get('okapi'):
    st.session_state['okapi'] = st.session_state.get('okapi_url', '')
if 'token' not in st.session_state:
    st.session_state['token'] = st.session_state.get('token')
if 'username_tenant' not in st.session_state or not st.session_state.get('username_tenant'):
    st.session_state['username_tenant'] = st.session_state.get('tenant_username', '')

hide_menu_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_menu_style, unsafe_allow_html=True)


def generate_password(length=12):
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(length))
    return password
def ensure_patron_group(okapi: str, headers: Dict[str, str]) -> str:
    """Ensure Naseej patron group exists and return its id."""
    group_query = {"query": '(group=="Naseej")'}
    response = requests.get(f"{okapi}/groups", headers=headers, params=group_query)
    response.raise_for_status()
    data = response.json()
    if data.get("usergroups"):
        return data["usergroups"][0]["id"]

    payload = {"group": "Naseej"}
    create_resp = requests.post(f"{okapi}/groups", headers=headers, json=payload)
    if create_resp.status_code not in (201, 422):
        raise RuntimeError(f"Failed to create patron group: {create_resp.text}")

    refresh = requests.get(f"{okapi}/groups", headers=headers, params=group_query)
    refresh.raise_for_status()
    groups = refresh.json().get("usergroups", [])
    if not groups:
        raise RuntimeError("Unable to retrieve Naseej patron group after creation.")
    return groups[0]["id"]


def fetch_permission_name(okapi: str, headers: Dict[str, str], display_name: str) -> str:
    """Fetch the permissionName for a display name; raise if missing."""
    params = {"query": f'(displayName=="{display_name}")'}
    response = requests.get(f"{okapi}/perms/permissions", headers=headers, params=params)
    response.raise_for_status()
    payload = response.json()
    permissions = payload.get("permissions") or []
    if not permissions:
        raise RuntimeError(f"Permission set '{display_name}' not found in tenant.")
    record = permissions[0]
    return record.get("permissionName") or record.get("id")


def get_permission_user_record(okapi: str, headers: Dict[str, str], user_id: str) -> Optional[Dict]:
    params = {"query": f'(userId=="{user_id}")'}
    response = requests.get(f"{okapi}/perms/users", headers=headers, params=params)
    response.raise_for_status()
    data = response.json()
    records = data.get("permissionUsers") or []
    return records[0] if records else None


def assign_permission_to_user(okapi: str, headers: Dict[str, str], user_id: str, permission_name: str) -> None:
    existing = get_permission_user_record(okapi, headers, user_id)
    if existing:
        permissions = set(existing.get("permissions") or [])
        if permission_name not in permissions:
            permissions.add(permission_name)
            existing["permissions"] = list(permissions)
            update = requests.put(
                f"{okapi}/perms/users/{existing['id']}",
                headers=headers,
                json=existing,
            )
            update.raise_for_status()
    else:
        payload = {"userId": user_id, "permissions": [permission_name]}
        response = requests.post(f"{okapi}/perms/users", headers=headers, json=payload)
        response.raise_for_status()


def set_preferred_service_point(okapi: str, headers: Dict[str, str], user_id: str) -> None:
    params = {"query": 'name=="Online"'}
    response = requests.get(f"{okapi}/service-points", headers=headers, params=params)
    response.raise_for_status()
    points = response.json().get("servicepoints") or []
    if not points:
        return

    service_point_id = points[0]["id"]
    sp_payload = {
        "userId": user_id,
        "servicePointsIds": [service_point_id],
        "defaultServicePointId": service_point_id,
    }

    params = {"query": f'(userId=="{user_id}")'}
    existing_resp = requests.get(f"{okapi}/service-points-users", headers=headers, params=params)
    existing_resp.raise_for_status()
    records = existing_resp.json().get("servicePointsUsers") or []

    if records:
        record_id = records[0]["id"]
        sp_payload["id"] = record_id
        update = requests.put(
            f"{okapi}/service-points-users/{record_id}", headers=headers, json=sp_payload
        )
        if update.status_code not in (200, 204):
            st.warning(f"Failed to update service point for {user_id}: {update.text}")
    else:
        create = requests.post(f"{okapi}/service-points-users", headers=headers, json=sp_payload)
        if create.status_code not in (201, 204):
            st.warning(f"Failed to assign service point for {user_id}: {create.text}")


def send_user_creation_email(tenant: str, results: List[Dict[str, str]]) -> Tuple[bool, Optional[str]]:
    if not results:
        return False, "No user results to email."

    tenant_upper = tenant.upper() if tenant else "UNKNOWN"
    subject = f"{tenant_upper} - User Creation Summary"
    sender_email = "ilsconfigration@gmail.com"
    sender_password = "pmgargvvawxpltow"
    receiver_email = "ilsconfigration@gmail.com"

    lines = []
    for entry in results:
        password_info = entry.get("password") or "N/A"
        status = entry.get("status", "unknown").upper()
        detail = entry.get("message", "")
        lines.append(f"{entry['username']}: {status} (password: {password_info}) {detail}")

    body = "\n".join(lines) or "No users were processed."

    try:
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import smtplib

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.set_debuglevel(0)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True, None
    except Exception as exc:
        st.warning(f"Unable to send notification email: {exc}")
        return False, str(exc)


def resolve_permission_display_name(username: str, tenant: str) -> str:
    if username.startswith("sip_"):
        return "SIP2 (Service Desk)"
    naseej_users = {"portal_integration", "kam_admin", "helpdesk_admin", "data_migration", "data_migration_user"}
    if username in naseej_users:
        return "Naseej"
    if username == "api_user":
        return "User Management and Circulation"
    return "Naseej"


def create_users(selected_users: List[str]):
    if not selected_users:
        return

    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name", "")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url", "")
    token = st.session_state.get("token")

    if not (tenant and okapi and token):
        st.error("Tenant connection details are missing.")
        return

    base_headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}
    try:
        group_id = ensure_patron_group(okapi, base_headers)
        display_names_needed: Set[str] = {resolve_permission_display_name(u, tenant) for u in selected_users}
        permission_names: Dict[str, str] = {}
        for display_name in display_names_needed:
            permission_names[display_name] = fetch_permission_name(okapi, base_headers, display_name)
    except Exception as exc:
        st.error(f"Failed to prepare prerequisites: {exc}")
        return

    users_url = f"{okapi}/users"
    password_url = f"{okapi}/authn/credentials"
    results: List[Dict[str, str]] = []

    for username in selected_users:
        resolved_permission = resolve_permission_display_name(username, tenant)
        permission_name = permission_names.get(resolved_permission)

        if not permission_name:
            msg = f"Permission set '{resolved_permission}' not found."
            st.error(msg)
            results.append({"username": username, "status": "failed", "message": msg})
            continue

        user_record = {
            "username": username,
            "patronGroup": group_id,
            "active": True,
            "personal": {
                "lastName": username,
                "email": username,
                "addresses": [],
                "preferredContactTypeId": "002",
            },
        }

        try:
            existing = requests.get(
                users_url,
                headers=base_headers,
                params={"query": f'(username=="{username}")'},
            )
            existing.raise_for_status()
            existing_users = existing.json().get("users") or []

            if existing_users:
                user_id = existing_users[0]["id"]
                assign_permission_to_user(okapi, base_headers, user_id, permission_name)
                set_preferred_service_point(okapi, base_headers, user_id)
                message = "User already existed; ensured permission assignment."
                st.info(f"{username}: {message}")
                results.append(
                    {"username": username, "status": "exists", "message": message}
                )
                continue

            create_resp = requests.post(users_url, headers=base_headers, json=user_record)
            if create_resp.status_code not in (201, 200):
                error_text = create_resp.text
                st.error(f"Failed to create {username}: {error_text}")
                results.append(
                    {"username": username, "status": "failed", "message": error_text}
                )
                continue

            fetch = requests.get(
                users_url,
                headers=base_headers,
                params={"query": f'(username=="{username}")'},
            )
            fetch.raise_for_status()
            new_user = fetch.json().get("users")[0]
            user_id = new_user["id"]

            password = generate_password()
            password_payload = {"username": username, "password": password, "userId": user_id}
            password_resp = requests.post(password_url, headers=base_headers, json=password_payload)
            password_resp.raise_for_status()

            assign_permission_to_user(okapi, base_headers, user_id, permission_name)
            set_preferred_service_point(okapi, base_headers, user_id)

            st.success(f"User ({username}) created. Password: {password}")
            results.append(
                {
                    "username": username,
                    "status": "created",
                    "password": password,
                    "message": f"Assigned permission set '{resolved_permission}'.",
                }
            )

        except requests.HTTPError as http_err:
            st.error(f"HTTP error for {username}: {http_err}")
            results.append(
                {"username": username, "status": "failed", "message": str(http_err)}
            )
        except Exception as exc:
            st.error(f"Unexpected error for {username}: {exc}")
            results.append(
                {"username": username, "status": "failed", "message": str(exc)}
            )

    st.session_state["user_creation_results"] = results
    email_sent, email_error = send_user_creation_email(tenant, results)
    if email_sent:
        st.success("Notification email sent.")
    else:
        st.info("Email notification not sent.")

st.title("User Creation")
if st.session_state.allow_tenant:
    # Get tenant name with fallback
    tenant_name = st.session_state.get('tenant') or st.session_state.get('tenant_name', '')
    
    # Build user options list
    user_options = ['portal_integration', 'kam_admin', 'helpdesk_admin', 'data_migration', 'api_user']
    if tenant_name:
        user_options.append(f'sip_{tenant_name}')
    
    options = st.multiselect(
        'Please choose users to create',
        user_options,
        help="Select one or more default accounts to create. The button below stays available even when all accounts are selected.")

    st.write("")
    create_clicked = st.button("Create users", type="primary", use_container_width=False)

    if create_clicked:
        if not options:
            st.warning("Please select at least one user.")
        else:
            create_users(options)
    summary = st.session_state.get("user_creation_results")
    if summary:
        st.subheader("User creation summary")
        st.table(summary)
else:
    st.warning("Please Connect to Tenant First.")
