import aiohttp
import asyncio
import json
import re
import uuid
import streamlit as st
from legacy_session_state import legacy_session_state
import requests
import logging
legacy_session_state()

if 'Allow_rest' not in st.session_state:
    st.session_state['Allow_rest'] = False


def _get_connection_details(require_token: bool = True):
    tenant = st.session_state.get('tenant') or st.session_state.get('tenant_name') or ''
    okapi = st.session_state.get('okapi') or st.session_state.get('okapi_url') or ''
    token = st.session_state.get('token') if require_token else (st.session_state.get('token') or '')

    if require_token and not all([tenant, okapi, token]):
        logging.error("Missing tenant connection details (tenant/okapi/token)")
        if hasattr(st, 'error'):
            st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        return None, None, None

    return tenant, okapi, token


def _build_dummy_location_identifiers(tenant_raw: str):
    base_name = re.sub(r'[^A-Za-z0-9]+', '_', tenant_raw or '').strip('_') or 'tenant'
    base_name_lower = base_name.lower()
    base_name_upper = base_name.upper()

    def name_with_suffix(suffix: str) -> str:
        return f"{base_name_lower}__{suffix}"

    def code_with_suffix(suffix: str) -> str:
        code_value = f"{base_name_upper}__{suffix}"
        return code_value[:50]

    return {
        "institution_name": name_with_suffix("institution"),
        "institution_code": code_with_suffix("INSTITUTION"),
        "campus_name": name_with_suffix("campus"),
        "campus_code": code_with_suffix("CAMPUS"),
        "library_name": name_with_suffix("library"),
        "library_code": code_with_suffix("LIBRARY"),
        "location_name": name_with_suffix("location"),
        "location_code": code_with_suffix("LOCATION"),
        "service_point_name": name_with_suffix("service_point"),
        "service_point_code": code_with_suffix("SP")
    }


MARC_TEMPLATE_DEFINITIONS = [
    {
        "id": "cf747c1c-7f40-4056-b063-723ed8289ed8",
        "name": "Default Bibliographic Template",
        "description": "Automation - default bibliographic template",
        "content": {
            "leader": "00000nam a2200000 i 4500",
            "fields": [
                {"tag": "001", "value": ""},
                {"tag": "005", "value": ""},
                {"tag": "008", "value": ""},
                {
                    "tag": "100",
                    "indicator1": "1",
                    "indicator2": " ",
                    "subfields": [{"code": "a", "value": ""}]
                },
                {
                    "tag": "245",
                    "indicator1": "1",
                    "indicator2": "0",
                    "subfields": [{"code": "a", "value": ""}]
                },
                {
                    "tag": "264",
                    "indicator1": " ",
                    "indicator2": "1",
                    "subfields": [
                        {"code": "a", "value": ""},
                        {"code": "b", "value": ""},
                        {"code": "c", "value": ""}
                    ]
                }
            ]
        }
    }
]


# Set logging to WARNING level to suppress debug output
logging.basicConfig(level=logging.WARNING)

async def async_request(method, url, headers=None, data=None):
    if headers is None:
        headers = {}
    headers['Content-Type'] = 'application/json'

    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, data=data) as response:
            # Suppress debug logging - only log errors
            if response.status != 200:
                logging.error(f"API Error: {response.status} - {await response.text()}")
            response.raise_for_status()
            return await response.json() if method == "GET" else await response.text()


async def configure_tenant():
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, "Missing tenant info"

    Config_url = f"{okapi}/configurations/entries?limit=1000"
    post_url = f"{okapi}/configurations/entries"
    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}
    response = await async_request("GET", Config_url, headers=headers)
    # Configuration response - no debug output needed

    reset = {
        "module": "USERSBL",
        "configName": "smtp",
        "code": "FOLIO_HOST",
        "description": "email reset host",
        "default": "true",
        "enabled": "true",
        "value": f"{st.session_state.clienturl}",
    }

    marc = {
        "module": "MARCEDITOR",
        "configName": "default_job_profile_id",
        "enabled": "true",
        "value": "e34d7b92-9b83-11eb-a8b3-0242ac130003"
    }

    tasks = []
    smtp_exists = False
    marc_exists = False
    help_exists = False
    help_url = "https://docs.medad.com/"
    help_payload = {
        "module": "MISCELLANEOUS",
        "configName": "HELP_URL",
        "enabled": "true",
        "value": json.dumps({"ar": help_url, "en": help_url, "fr": help_url})
    }

    for config in response["configs"]:
        if config["module"] == "USERSBL" and config["configName"] == "smtp" and config["code"] == "FOLIO_HOST":
            smtp_exists = True
            tasks.append(async_request("PUT", f"{post_url}/{config['id']}", headers=headers, data=json.dumps(reset)))
        elif config["module"] == "MARCEDITOR" and config["configName"] == "default_job_profile_id":
            marc_exists = True
            if config["value"] != "e34d7b92-9b83-11eb-a8b3-0242ac130003":
                st.warning('Please Check Your Job Load Profile Manually!')
            # Update existing marc configuration
            tasks.append(async_request("PUT", f"{post_url}/{config['id']}", headers=headers, data=json.dumps(marc)))
        elif config["module"] == "MISCELLANEOUS" and config["configName"] == "HELP_URL":
            help_exists = True
            # Update if value is missing or different from desired URL
            try:
                existing_value = json.loads(config.get("value") or "{}")
            except json.JSONDecodeError:
                existing_value = {}

            should_update = any(existing_value.get(lang) != help_url for lang in ["ar", "en", "fr"]) or not existing_value

            if should_update:
                tasks.append(async_request(
                    "PUT",
                    f"{post_url}/{config['id']}",
                    headers=headers,
                    data=json.dumps(help_payload)
                ))

    if not smtp_exists:
        tasks.append(async_request("POST", post_url, headers=headers, data=json.dumps(reset)))

    if not marc_exists:
        tasks.append(async_request("POST", post_url, headers=headers, data=json.dumps(marc)))

    if not help_exists:
        tasks.append(async_request("POST", post_url, headers=headers, data=json.dumps(help_payload)))

    if tasks:
        await asyncio.gather(*tasks)

    return True, "Tenant configuration updated"

async def price_note():
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, "Missing tenant info"

    item_note_types_url = f"{okapi}/item-note-types"
    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}

    # Fetch existing item note types
    existing_item_note_types_response = await async_request("GET", item_note_types_url, headers=headers)
    # Existing item note types - no debug output needed

    if isinstance(existing_item_note_types_response, dict) and 'itemNoteTypes' in existing_item_note_types_response:
        existing_item_note_types = {note_type["name"].lower() for note_type in
                                    existing_item_note_types_response['itemNoteTypes']}
    else:
        existing_item_note_types = set()

    item_note_name = "price"
    if item_note_name.lower() not in existing_item_note_types:
        data = {"source": "automation", "name": item_note_name}
        await async_request("POST", item_note_types_url, headers=headers, data=json.dumps(data))

    return True, "Price note type ensured"


async def ensure_address_types():
    """Ensure required patron address types are present (Home, Work)."""
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, "Missing tenant info"

    url = f"{okapi}/addresstypes"
    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}

    try:
        existing_response = await async_request("GET", url, headers=headers)
    except Exception as exc:
        logging.error(f"Failed to fetch address types: {exc}")
        return False, f"Error fetching address types: {exc}"

    existing_types = set()
    if isinstance(existing_response, dict):
        raw_types = existing_response.get("addressTypes") or existing_response.get("addresstypes") or []
        for entry in raw_types:
            name = entry.get("addressType") or entry.get("name")
            if name:
                existing_types.add(name.lower())
    elif isinstance(existing_response, list):
        for entry in existing_response:
            name = entry.get("addressType") or entry.get("name")
            if name:
                existing_types.add(name.lower())

    desired_types = ["Home", "Work"]
    create_tasks = []

    for address_type in desired_types:
        if address_type.lower() in existing_types:
            continue
        payload = {
            "addressType": address_type,
            "id": str(uuid.uuid4())
        }
        create_tasks.append(async_request("POST", url, headers=headers, data=json.dumps(payload)))

    if create_tasks:
        try:
            await asyncio.gather(*create_tasks)
        except Exception as exc:
            logging.error(f"Failed to create address types: {exc}")
            return False, f"Failed creating address types: {exc}"

    return True, "Address types ensured"

async def loan_type():
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, "Missing tenant info"

    loan_types_url = f"{okapi}/loan-types"
    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}

    # Fetch existing loan types
    existing_loan_types_response = await async_request("GET", loan_types_url, headers=headers)
    # Existing loan types - no debug output needed

    if isinstance(existing_loan_types_response, dict) and 'loantypes' in existing_loan_types_response:
        existing_loan_types = {loan_type["name"].lower() for loan_type in existing_loan_types_response['loantypes']}
    else:
        existing_loan_types = set()

    loan_type_name = "Non circulating"
    if loan_type_name.lower() not in existing_loan_types:
        data = {"name": loan_type_name}
        await async_request("POST", loan_types_url, headers=headers, data=json.dumps(data))
        return True, f"Created {loan_type_name}"

    return True, f"Existing {loan_type_name}"


async def ensure_marc_templates():
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, "Missing tenant info"

    headers = {
        "x-okapi-tenant": tenant,
        "x-okapi-token": token,
        "Content-Type": "application/json"
    }

    created_templates = []

    # Fetch existing recordTemplates entry
    templates_query = f"{okapi}/configurations/entries?query=(module==MARC_EDITOR and configName==recordTemplates)"
    try:
        resp = requests.get(templates_query, headers=headers)
    except Exception as exc:
        logging.error(f"Failed to fetch existing MARC templates: {exc}")
        return False, f"Fetch failed: {exc}"

    if resp.status_code != 200:
        logging.error(f"Cannot fetch MARC templates: {resp.status_code} - {resp.text[:200]}")
        return False, f"HTTP {resp.status_code}"

    data = resp.json()
    existing_entry = data.get('configs', [])
    existing_templates = []
    entry_id = None
    if existing_entry:
        entry = existing_entry[0]
        entry_id = entry.get('id')
        try:
            existing_templates = json.loads(entry.get('value') or '[]')
        except json.JSONDecodeError:
            existing_templates = []

    existing_ids = {template.get('id') for template in existing_templates}

    updated_templates = existing_templates[:]

    for template_def in MARC_TEMPLATE_DEFINITIONS:
        template_id = template_def['id']
        if template_id not in existing_ids:
            updated_templates.append({
                "id": template_id,
                "name": template_def.get('name', template_id),
                "description": template_def.get('description', '')
            })
            created_templates.append(template_def['name'])

        # Ensure template content exists
        content_query = (
            f"{okapi}/configurations/entries?query=(module==MARC_EDITOR and "
            f"configName==recordTemplatesContent and code=={template_id})"
        )
        try:
            content_resp = requests.get(content_query, headers=headers)
        except Exception as exc:
            logging.error(f"Failed to check template content for {template_id}: {exc}")
            return False, f"Template content fetch failed: {exc}"

        payload = {
            "module": "MARC_EDITOR",
            "configName": "recordTemplatesContent",
            "code": template_id,
            "enabled": True,
            "value": json.dumps(template_def['content'])
        }

        if content_resp.status_code == 200 and content_resp.json().get('configs'):
            config_id = content_resp.json()['configs'][0]['id']
            await async_request(
                "PUT",
                f"{okapi}/configurations/entries/{config_id}",
                headers=headers,
                data=json.dumps(payload)
            )
        else:
            await async_request(
                "POST",
                f"{okapi}/configurations/entries",
                headers=headers,
                data=json.dumps(payload)
            )

    # Update recordTemplates entry
    templates_payload = {
        "module": "MARC_EDITOR",
        "configName": "recordTemplates",
        "enabled": True,
        "value": json.dumps(updated_templates)
    }

    if entry_id:
        await async_request(
            "PUT",
            f"{okapi}/configurations/entries/{entry_id}",
            headers=headers,
            data=json.dumps(templates_payload)
        )
    else:
        await async_request(
            "POST",
            f"{okapi}/configurations/entries",
            headers=headers,
            data=json.dumps(templates_payload)
        )

    if created_templates:
        return True, f"Templates added: {', '.join(created_templates)}"
    return True, "Templates already present"


async def default_job_profile():
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    config_url = f"{st.session_state.okapi}/configurations/entries?query=(module==MARCEDITOR and configName==default_job_profile_id)"

    # Fetch existing configuration entries
    response = await async_request("GET", config_url, headers=headers)
    # Existing default job profile - no debug output needed

    default_job = {
        "module": "MARCEDITOR",
        "configName": "default_job_profile_id",
        "enabled": "true",
        "value": "e34d7b92-9b83-11eb-a8b3-0242ac130003"
    }

    if response and 'configs' in response and len(response['configs']) > 0:
        config_id = response['configs'][0]['id']
        # Updating existing configuration - no output needed
        update_url = f"{st.session_state.okapi}/configurations/entries/{config_id}"
        await async_request("PUT", update_url, headers=headers, data=json.dumps(default_job))
    else:
        # Creating new configuration entry - no output needed
        await async_request("POST", f"{st.session_state.okapi}/configurations/entries", headers=headers,
                            data=json.dumps(default_job))
async def alt_types():
    alt_typesurl = f"{st.session_state.okapi}/alternative-title-types"
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    altlist = ['Uniform title', 'Variant title', 'General topology', 'Former title']

    # Fetch existing alternative title types
    existing_types_response = await async_request("GET", alt_typesurl, headers=headers)
    # Existing types - no debug output needed

    existing_types = set()
    if isinstance(existing_types_response, dict) and 'alternativeTitleTypes' in existing_types_response:
        for alt_type in existing_types_response['alternativeTitleTypes']:
            # Alternative title type found - no output needed
            if isinstance(alt_type, dict) and 'name' in alt_type:
                existing_types.add(alt_type["name"].strip().lower())

    # Existing types set - no debug output needed

    tasks = []
    for alt in altlist:
        alt_lower = alt.strip().lower()
        if alt_lower not in existing_types:
            data = json.dumps({"name": alt, "source": "Automation"})
            # Adding new alternative title type - no output needed
            tasks.append(async_request("POST", alt_typesurl, headers=headers, data=data))
        else:
            # Alternative title type already exists - no output needed
            pass

    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                # Error during task execution - logged at warning level if needed
                pass

async def addDepartments():
    departments_url = f"{st.session_state.okapi}/departments"
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}

    # Fetch existing departments
    existing_departments_response = await async_request("GET", departments_url, headers=headers)
    # Existing departments - no debug output needed

    if isinstance(existing_departments_response, dict) and 'departments' in existing_departments_response:
        existing_departments = {dept["name"].lower() for dept in existing_departments_response['departments']}
    else:
        existing_departments = set()

    department_name = "Main"
    if department_name.lower() not in existing_departments:
        data = {"name": department_name, "code": "main"}
        await async_request("POST", departments_url, headers=headers, data=json.dumps(data))
    else:
        # Department already exists - no output needed
        pass


async def add_auc_identifier_type():
    """Add AUC ID identifier type to the tenant"""
    identifier_types_url = f"{st.session_state.okapi}/identifier-types"
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}

    # Fetch existing identifier types
    existing_identifier_types_response = await async_request("GET", identifier_types_url, headers=headers)

    if isinstance(existing_identifier_types_response, dict) and 'identifierTypes' in existing_identifier_types_response:
        existing_identifier_types = {identifier_type["name"].lower() for identifier_type in existing_identifier_types_response['identifierTypes']}
    else:
        existing_identifier_types = set()

    identifier_type_name = "AUC ID"
    if identifier_type_name.lower() not in existing_identifier_types:
        # Create AUC ID identifier type with specific structure
        data = {
            "source": "local",
            "name": identifier_type_name,
            "id": "4570f599-3f9b-4a59-8b5c-5f89015f6634"
        }
        await async_request("POST", identifier_types_url, headers=headers, data=json.dumps(data))
    else:
        # Identifier type already exists - no output needed
        pass


async def create_authority_source_file():
    """
    Create local authority source file with tenant name prefix and HRID starting at 1.
    Returns (success: bool, error_message: str or None)
    """
    try:
        authority_source_url = f"{st.session_state.okapi}/authority-source-files"
        headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
        
        # Create file name with tenant name + "1" (e.g., "KAM1")
        tenant_name = st.session_state.get('tenant', 'TENANT')
        file_name = f"{tenant_name.upper()}1"
        
        # Check if file already exists
        try:
            existing_files_response = await async_request("GET", authority_source_url, headers=headers)
            if isinstance(existing_files_response, dict) and 'authoritySourceFiles' in existing_files_response:
                existing_files = {file["name"].upper() for file in existing_files_response['authoritySourceFiles']}
                if file_name.upper() in existing_files:
                    # File already exists
                    return True, None
        except Exception as e:
            logging.warning(f"Could not check existing authority source files: {str(e)}")
        
        # Create authority source file
        data = {
            "name": file_name,
            "hridManagement": {
                "startNumber": "1"
            },
            "baseUrl": "",
            "source": "local",
            "selectable": True,
            "code": "TEST"
        }
        
        try:
            await async_request("POST", authority_source_url, headers=headers, data=json.dumps(data))
            return True, None  # Success
        except Exception as e:
            error_message = f"Failed to create authority source file '{file_name}': {str(e)}"
            logging.error(error_message)
            return False, error_message
            
    except Exception as e:
        error_message = f"Error creating authority source file: {str(e)}"
        logging.error(error_message)
        return False, error_message


async def post_locale(timezone, currency):
    get_config = f"{st.session_state.okapi}/configurations/entries?query=(module==ORG and configName==localeSettings)"
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    response = await async_request("GET", get_config, headers=headers)

    to_do = {
        "module": "ORG",
        "configName": "localeSettings",
        "enabled": True,
        "value": f'{{"locale":"en-US","timezone":"{timezone}","currency":"{currency}"}}'
    }

    if not response['configs']:
        await async_request("POST", f"{st.session_state.okapi}/configurations/entries", headers=headers,
                            data=json.dumps(to_do))
    else:
        config_id = response['configs'][0]['id']
        await async_request("PUT", f"{st.session_state.okapi}/configurations/entries/{config_id}", headers=headers,
                            data=json.dumps(to_do))


async def circ_other():
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    value = {
        "audioAlertsEnabled": False,
        "audioTheme": "classic",
        "checkoutTimeout": True,
        "checkoutTimeoutDuration": 3,
        "prefPatronIdentifier": "barcode,username",
        "useCustomFieldsAsIdentifiers": False,
        "wildcardLookupEnabled": False
    }
    body = {
        "module": "CHECKOUT",
        "configName": "other_settings",
        "enabled": True,
        "value": json.dumps(value)}  # Convert the value object to a JSON string

    response = await async_request("GET",
                                   f"{st.session_state.okapi}/configurations/entries?query=(module=CHECKOUT and configName=other_settings)",
                                   headers=headers)
    if response['configs']:
        config_id = response['configs'][0]['id']
        await async_request("PUT", f"{st.session_state.okapi}/configurations/entries/{config_id}", headers=headers,
                            data=json.dumps(body))
    else:
        await async_request("POST", f"{st.session_state.okapi}/configurations/entries", headers=headers,
                            data=json.dumps(body))


async def circ_loanhist():
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    body = {
        "module": "LOAN_HISTORY",
        "configName": "loan_history",
        "enabled": True,
        "value": "{\"closingType\":{\"loan\":\"never\",\"feeFine\":null,\"loanExceptions\":[]},\"loan\":{},\"feeFine\":{},\"loanExceptions\":[],\"treatEnabled\":false}"
    }

    response = await async_request("GET",
                                   f"{st.session_state.okapi}/configurations/entries?query=(module=LOAN_HISTORY and configName=loan_history)",
                                   headers=headers)
    if response['configs']:
        config_id = response['configs'][0]['id']
        await async_request("PUT", f"{st.session_state.okapi}/configurations/entries/{config_id}", headers=headers,
                            data=json.dumps(body))
    else:
        await async_request("POST", f"{st.session_state.okapi}/configurations/entries", headers=headers,
                            data=json.dumps(body))


async def export_profile():
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    profile_url = f"{st.session_state.okapi}/data-export/mapping-profiles"

    # Fetch existing mapping profiles
    existing_profiles_response = await async_request("GET", profile_url, headers=headers)
    # Existing profiles - no debug output needed

    existing_profiles = set()
    if isinstance(existing_profiles_response, dict) and 'mappingProfiles' in existing_profiles_response:
        for profile in existing_profiles_response['mappingProfiles']:
            # Mapping profile found - no output needed
            if isinstance(profile, dict) and 'name' in profile:
                existing_profiles.add(profile["name"].lower())

    # Existing profiles set - no debug output needed

    profile_name = "Medad Export"
    if profile_name.lower() not in existing_profiles:
        data = json.dumps({
            "transformations": [
                {"fieldId": "holdings.callnumber", "path": "$.holdings[*].callNumber", "recordType": "HOLDINGS",
                 "transformation": "99900$a", "enabled": True},
                {"fieldId": "holdings.callnumbertype", "path": "$.holdings[*].callNumberTypeId",
                 "recordType": "HOLDINGS", "transformation": "99900$w", "enabled": True},
                {"fieldId": "item.barcode", "path": "$.holdings[*].items[*].barcode", "recordType": "ITEM",
                 "transformation": "99900$i", "enabled": True},
                {"fieldId": "item.copynumber", "path": "$.holdings[*].items[*].copyNumber", "recordType": "ITEM",
                 "transformation": "99900$c", "enabled": True},
                {"fieldId": "item.effectivelocation.name", "path": "$.holdings[*].items[*].effectiveLocationId",
                 "recordType": "ITEM", "transformation": "99900$l", "enabled": True},
                {"fieldId": "item.materialtypeid", "path": "$.holdings[*].items[*].materialTypeId",
                 "recordType": "ITEM", "transformation": "99900$t", "enabled": True},
                {"fieldId": "item.itemnotetypeid.price",
                 "path": "$.holdings[*].items[*].notes[?(@.itemNoteTypeId=='bd68d7f1-2535-48af-bfac-c554cf8204f6' && (!(@.staffOnly) || @.staffOnly == false))].note",
                 "recordType": "ITEM", "transformation": "99900$p", "enabled": True},
                {"fieldId": "item.status", "path": "$.holdings[*].items[*].status.name", "recordType": "ITEM",
                 "transformation": "99900$s", "enabled": True},
                {"fieldId": "item.volume", "path": "$.holdings[*].items[*].volume", "recordType": "ITEM",
                 "transformation": "99900$v", "enabled": True}
            ],
            "recordTypes": ["SRS", "HOLDINGS", "ITEM"],
            "outputFormat": "MARC",
            "name": profile_name
        })
        await async_request("POST", profile_url, headers=headers, data=data)
    else:
        # Mapping profile already exists - no output needed
        pass


async def profile_picture():
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    body = {
        "module": "USERS",
        "configName": "profile_pictures",
        "enabled": True,
        "value": True
    }

    response = await async_request("GET",
                                   f"{st.session_state.okapi}/configurations/entries?query=(module=USERS and configName=profile_pictures)",
                                   headers=headers)
    if response['configs']:
        config_id = response['configs'][0]['id']
        await async_request("PUT", f"{st.session_state.okapi}/configurations/entries/{config_id}", headers=headers,
                            data=json.dumps(body))
    else:
        await async_request("POST", f"{st.session_state.okapi}/configurations/entries", headers=headers,
                            data=json.dumps(body))


def get_location_id():
    url = f'{st.session_state.okapi}/locations?limit=3000&query=cql.allRecords%3D1%20sortby%20name'

    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes

    data = response.json()

    # Extract any location ID
    if 'locations' in data and data['locations']:
        return data['locations'][0]['id']  # Return the first location ID
    else:
        return None


def get_material_type_id():
    url = f'{st.session_state.okapi}/material-types?query=cql.allRecords=1%20sortby%20name&limit=2000'

    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes

    data = response.json()

    # Extract any material type ID
    if 'mtypes' in data and data['mtypes']:
        return data['mtypes'][0]['id']  # Return the first material type ID
    else:
        return None


def get_loan_type_id():
    url = f'{st.session_state.okapi}/loan-types?query=cql.allRecords=1%20sortby%20name&limit=2000'

    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}

    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise an error for bad status codes

    data = response.json()

    # Extract any loan type ID
    if 'loantypes' in data and data['loantypes']:
        return data['loantypes'][0]['id']  # Return the first loan type ID
    else:
        return None


def create_instance_for_analytics():
    """Create a suppressed instance directly for analytics (no MARC record needed)"""
    tenant = st.session_state.get('tenant') or st.session_state.get('tenant_name')
    okapi = st.session_state.get('okapi') or st.session_state.get('okapi_url')
    token = st.session_state.get('token')

    if not all([tenant, okapi, token]):
        logging.error("Cannot create analytics instance: tenant connection details missing")
        if hasattr(st, 'error'):
            st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        return None

    url = f'{okapi}/inventory/instances'
    headers = {
        "x-okapi-tenant": tenant,
        "x-okapi-token": token,
        "Content-Type": "application/json"
    }
    
    # Get default instance type ID (try to get first available)
    instance_types_url = f'{okapi}/instance-types?limit=1000'
    try:
        types_response = requests.get(instance_types_url, headers=headers)
        if types_response.status_code == 200:
            types_data = types_response.json()
            if types_data.get('instanceTypes') and len(types_data['instanceTypes']) > 0:
                instance_type_id = types_data['instanceTypes'][0]['id']
            else:
                # Default instance type ID (text/print)
                instance_type_id = "a2c91e87-6bab-44d6-8adb-1fd02481fc4f"
        else:
            instance_type_id = "a2c91e87-6bab-44d6-8adb-1fd02481fc4f"
    except Exception as e:
        logging.warning(f"Could not fetch instance types: {e}. Using default.")
        instance_type_id = "a2c91e87-6bab-44d6-8adb-1fd02481fc4f"
    
    # For analytics: discoverySuppress=True (hidden from public discovery)
    # BUT staffSuppress=False (visible to staff) so items can be found in ILS
    data = {
        "discoverySuppress": True,
        "staffSuppress": False,  # Set to False so staff can see it in ILS
        "previouslyHeld": False,
        "source": "FOLIO",
        "title": "kamautomation",
        "instanceTypeId": instance_type_id,
        "precedingTitles": [],
        "succeedingTitles": [],
        "parentInstances": [],
        "childInstances": []
    }

    logging.info(f"Creating instance with data: {json.dumps(data, indent=2)}")
    logging.info(f"POST URL: {url}")
    logging.info(f"Headers: {headers}")
    
    response = requests.post(url, headers=headers, json=data)
    
    # Log full response for debugging
    logging.info(f"Instance creation response: Status={response.status_code}")
    logging.info(f"Response text (full): {response.text}")
    logging.info(f"Response headers: {dict(response.headers)}")

    if response.status_code == 201 or response.status_code == 200:
        try:
            # Try to parse JSON response if there's content
            if response.text and response.text.strip():
                instance_data = response.json()
                return instance_data.get('id')
        except (ValueError, requests.exceptions.JSONDecodeError) as json_error:
            # If JSON parsing fails, that's okay - try Location header
            logging.debug(f"JSON parsing failed (expected for empty response): {json_error}")
        
        # If response is empty or JSON parsing failed, check Location header
        location_header = response.headers.get('Location', '')
        if location_header:
            # Extract ID from location header (e.g., /inventory/instances/{id} or full URL)
            # Handle both relative and absolute URLs
            if 'http' in location_header:
                # Absolute URL: extract the ID part
                parts = location_header.rstrip('/').split('/')
                if parts:
                    return parts[-1]
            else:
                # Relative URL: /inventory/instances/{id}
                parts = location_header.strip('/').split('/')
                if len(parts) >= 2:
                    return parts[-1]
        
        # If still no ID, try to query for the instance we just created
        # Wait a moment for the instance to be indexed
        import time
        time.sleep(2)
        
        try:
            # Try multiple query formats
            query_formats = [
                f'{url}?query=title=="kamautomation"',
                f'{url}?query=title=~"kamautomation"',
                f'{url}?query=title=="kamautomation"&limit=100',
            ]
            
            for query_url in query_formats:
                try:
                    query_response = requests.get(query_url, headers=headers)
                    if query_response.status_code == 200:
                        query_data = query_response.json()
                        if query_data.get('instances') and len(query_data['instances']) > 0:
                            instance_id_found = query_data['instances'][0].get('id')
                            logging.info(f"Found instance via query: {instance_id_found}")
                            return instance_id_found
                except Exception as query_error:
                    logging.debug(f"Query format failed: {query_error}")
                    continue
        except Exception as query_error:
            logging.warning(f"Could not query for instance: {query_error}")
        
        logging.warning("Instance created (201) but could not extract ID from response, Location header, or query")
        return None
    else:
        error_text = response.text[:500] if response.text else 'No response text'
        logging.error(f"Failed to create instance: {response.status_code} - {error_text}")
        # Try to get more details about the error
        if hasattr(st, 'error'):
            st.error(f"❌ Instance creation failed: {response.status_code} - {error_text[:200]}")
        return None


def verify_instance_exists(instance_id):
    """Verify that the instance actually exists in the tenant"""
    if not instance_id:
        return False
    try:
        url = f'{st.session_state.okapi}/inventory/instances/{instance_id}'
        headers = {
            "x-okapi-tenant": f"{st.session_state.tenant}",
            "x-okapi-token": f"{st.session_state.token}"
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            instance_data = response.json()
            if instance_data.get('title') == 'kamautomation':
                logging.info(f"✅ Instance verified: {instance_id}, Title: {instance_data.get('title')}")
                return True
            else:
                logging.warning(f"Instance found but title mismatch: {instance_data.get('title')} != kamautomation")
        else:
            logging.warning(f"Instance GET returned status {response.status_code}: {response.text[:200]}")
        return False
    except Exception as e:
        logging.error(f"Error verifying instance: {e}")
        return False


def verify_instance_by_search():
    """Verify instance exists by searching for it"""
    try:
        url = f'{st.session_state.okapi}/inventory/instances'
        headers = {
            "x-okapi-tenant": f"{st.session_state.tenant}",
            "x-okapi-token": f"{st.session_state.token}"
        }
        
        # Try different query formats
        queries = [
            'query=title=="kamautomation"',
            'query=title=~"kamautomation"',
            'query=title=="kamautomation"&limit=100',
        ]
        
        for query in queries:
            try:
                query_url = f'{url}?{query}'
                response = requests.get(query_url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    instances = data.get('instances', [])
                    if instances:
                        for inst in instances:
                            if inst.get('title') == 'kamautomation':
                                logging.info(f"✅ Found instance via search: {inst.get('id')}, Title: {inst.get('title')}")
                                return inst.get('id')
            except Exception as e:
                logging.debug(f"Search query failed: {e}")
                continue
        
        logging.warning("Could not find instance 'kamautomation' via search")
        return None
    except Exception as e:
        logging.error(f"Error searching for instance: {e}")
        return None


def create_dummy_suppressed_location():
    """Create a dummy suppressed location with full tree structure (Institution, Campus, Library, Location) for analytics"""
    tenant_raw, okapi, token = _get_connection_details()
    if not tenant_raw:
        return None

    headers = {
        "x-okapi-tenant": tenant_raw,
        "x-okapi-token": token,
        "Content-Type": "application/json"
    }

    identifiers = _build_dummy_location_identifiers(tenant_raw)
    dummy_institution_name = identifiers["institution_name"]
    dummy_institution_code = identifiers["institution_code"]
    dummy_campus_name = identifiers["campus_name"]
    dummy_campus_code = identifiers["campus_code"]
    dummy_library_name = identifiers["library_name"]
    dummy_library_code = identifiers["library_code"]
    dummy_location_name = identifiers["location_name"]
    dummy_location_code = identifiers["location_code"]
    dummy_service_point_name = identifiers["service_point_name"]
    dummy_service_point_code = identifiers["service_point_code"]

    try:
        # Step 1: Check if location already exists
        location_check_url = f'{okapi}/locations?query=code=={dummy_location_code}'
        location_check = requests.get(location_check_url, headers=headers)
        if location_check.status_code == 200:
            location_data = location_check.json()
            if location_data.get('locations') and len(location_data['locations']) > 0:
                location_id = location_data['locations'][0]['id']
                logging.info(f"✅ Dummy location already exists: {location_id}")
                return location_id
        
        # Step 2: Create or get Service Point
        sp_url = f'{okapi}/service-points'
        sp_check_url = f'{okapi}/service-points?query=code=={dummy_service_point_code}'
        sp_check = requests.get(sp_check_url, headers=headers)
        sp_id = None
        
        if sp_check.status_code == 200:
            sp_data = sp_check.json()
            if sp_data.get('servicepoints') and len(sp_data['servicepoints']) > 0:
                sp_id = sp_data['servicepoints'][0]['id']
            else:
                # Create service point
                sp_data = {
                    "name": dummy_service_point_name,
                    "code": dummy_service_point_code,
                    "discoveryDisplayName": dummy_service_point_name,
                    "description": "Dummy service point for analytics",
                    "pickupLocation": True,
                    "holdShelfExpiryPeriod": {"duration": 30, "intervalId": "Days"}
                }
                sp_response = requests.post(sp_url, headers=headers, json=sp_data)
                if sp_response.status_code == 201:
                    sp_data = sp_response.json()
                    sp_id = sp_data.get('id')
                elif sp_response.status_code == 422:
                    # Already exists, try to get it
                    sp_check2 = requests.get(sp_check_url, headers=headers)
                    if sp_check2.status_code == 200:
                        sp_data = sp_check2.json()
                        if sp_data.get('servicepoints'):
                            sp_id = sp_data['servicepoints'][0]['id']
        
        if not sp_id:
            logging.error("Failed to create or get service point")
            return None
        
        # Step 3: Create or get Institution
        inst_url = f'{okapi}/location-units/institutions'
        inst_check_url = f'{okapi}/location-units/institutions?query=code=={dummy_institution_code}'
        inst_check = requests.get(inst_check_url, headers=headers)
        inst_id = None
        
        if inst_check.status_code == 200:
            inst_data = inst_check.json()
            if inst_data.get('locinsts') and len(inst_data['locinsts']) > 0:
                inst_id = inst_data['locinsts'][0]['id']
            else:
                inst_data = {"name": dummy_institution_name, "code": dummy_institution_code}
                inst_response = requests.post(inst_url, headers=headers, json=inst_data)
                if inst_response.status_code in [201, 422]:
                    if inst_response.status_code == 201:
                        inst_data = inst_response.json()
                        inst_id = inst_data.get('id')
                    else:
                        # Try to get it again
                        inst_check2 = requests.get(inst_check_url, headers=headers)
                        if inst_check2.status_code == 200:
                            inst_data = inst_check2.json()
                            if inst_data.get('locinsts'):
                                inst_id = inst_data['locinsts'][0]['id']
        
        if not inst_id:
            logging.error("Failed to create or get institution")
            return None
        
        # Step 4: Create or get Campus
        campus_url = f'{okapi}/location-units/campuses'
        campus_check_url = f'{okapi}/location-units/campuses?query=code=={dummy_campus_code}'
        campus_check = requests.get(campus_check_url, headers=headers)
        campus_id = None
        
        if campus_check.status_code == 200:
            campus_data = campus_check.json()
            if campus_data.get('loccamps') and len(campus_data['loccamps']) > 0:
                campus_id = campus_data['loccamps'][0]['id']
            else:
                campus_data = {
                    "name": dummy_campus_name,
                    "code": dummy_campus_code,
                    "institutionId": inst_id
                }
                campus_response = requests.post(campus_url, headers=headers, json=campus_data)
                if campus_response.status_code in [201, 422]:
                    if campus_response.status_code == 201:
                        campus_data = campus_response.json()
                        campus_id = campus_data.get('id')
                    else:
                        campus_check2 = requests.get(campus_check_url, headers=headers)
                        if campus_check2.status_code == 200:
                            campus_data = campus_check2.json()
                            if campus_data.get('loccamps'):
                                campus_id = campus_data['loccamps'][0]['id']
        
        if not campus_id:
            logging.error("Failed to create or get campus")
            return None
        
        # Step 5: Create or get Library
        lib_url = f'{okapi}/location-units/libraries'
        lib_check_url = f'{okapi}/location-units/libraries?query=code=={dummy_library_code}'
        lib_check = requests.get(lib_check_url, headers=headers)
        lib_id = None
        
        if lib_check.status_code == 200:
            lib_data = lib_check.json()
            if lib_data.get('loclibs') and len(lib_data['loclibs']) > 0:
                lib_id = lib_data['loclibs'][0]['id']
            else:
                lib_data = {
                    "name": dummy_library_name,
                    "code": dummy_library_code,
                    "campusId": campus_id
                }
                lib_response = requests.post(lib_url, headers=headers, json=lib_data)
                if lib_response.status_code in [201, 422]:
                    if lib_response.status_code == 201:
                        lib_data = lib_response.json()
                        lib_id = lib_data.get('id')
                    else:
                        lib_check2 = requests.get(lib_check_url, headers=headers)
                        if lib_check2.status_code == 200:
                            lib_data = lib_check2.json()
                            if lib_data.get('loclibs'):
                                lib_id = lib_data['loclibs'][0]['id']
        
        if not lib_id:
            logging.error("Failed to create or get library")
            return None
        
        # Step 6: Create Location (suppressed)
        location_url = f'{okapi}/locations'
        location_data = {
            "name": dummy_location_name,
            "code": dummy_location_code,
            "discoveryDisplayName": dummy_location_name,
            "isActive": True,
            "institutionId": inst_id,
            "campusId": campus_id,
            "libraryId": lib_id,
            "primaryServicePoint": sp_id,
            "servicePointIds": [sp_id]
        }
        
        location_response = requests.post(location_url, headers=headers, json=location_data)
        if location_response.status_code == 201:
            location_data = location_response.json()
            location_id = location_data.get('id')
            logging.info(f"✅ Dummy suppressed location created: {location_id}")
            return location_id
        elif location_response.status_code == 422:
            # Already exists, get it
            location_check_final = requests.get(f'{okapi}/locations?query=code=={dummy_location_code}', headers=headers)
            if location_check_final.status_code == 200:
                location_data = location_check_final.json()
                if location_data.get('locations') and len(location_data['locations']) > 0:
                    location_id = location_data['locations'][0]['id']
                    logging.info(f"✅ Dummy location already exists: {location_id}")
                    return location_id
        
        logging.error(f"Failed to create location: {location_response.status_code} - {location_response.text}")
        return None
        
    except Exception as e:
        logging.error(f"Error creating dummy location: {e}")
        return None


def fetch_help_url_status():
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, "Missing tenant info"

    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}
    url = f"{okapi}/configurations/entries?query=(module==MISCELLANEOUS and configName==HELP_URL)"

    try:
        response = requests.get(url, headers=headers)
    except Exception as exc:
        logging.error(f"Failed to fetch help URL config: {exc}")
        return False, f"Request failed: {exc}"

    if response.status_code != 200:
        logging.error(f"Help URL fetch failed: {response.status_code} - {response.text[:200]}")
        return False, f"HTTP {response.status_code}: {response.text[:200]}"

    data = response.json()
    configs = data.get('configs', [])
    if not configs:
        return False, "Not configured"

    raw_value = configs[0].get('value') or '{}'
    try:
        parsed_value = json.loads(raw_value)
    except json.JSONDecodeError:
        logging.error("Help URL value is not valid JSON")
        return False, "Invalid stored value"

    return True, parsed_value


def fetch_address_types_status():
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, []

    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}
    url = f"{okapi}/addresstypes"

    try:
        response = requests.get(url, headers=headers)
    except Exception as exc:
        logging.error(f"Failed to fetch address types: {exc}")
        return False, []

    if response.status_code != 200:
        logging.error(f"Address types fetch failed: {response.status_code} - {response.text[:200]}")
        return False, []

    data = response.json()
    if isinstance(data, dict):
        entries = data.get('addressTypes') or data.get('addresstypes') or []
    elif isinstance(data, list):
        entries = data
    else:
        entries = []

    names = []
    for entry in entries:
        name = entry.get('addressType') or entry.get('name')
        if name:
            names.append(name)

    return True, names


def fetch_dummy_location_status():
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, {"error": "Missing tenant info"}

    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}
    identifiers = _build_dummy_location_identifiers(tenant)

    results = {}

    def _exists(endpoint: str, key: str, label: str, code_key: str, name_key: str):
        try:
            resp = requests.get(f"{okapi}/{endpoint}", headers=headers)
            if resp.status_code != 200:
                logging.warning(f"Fetch {label} failed: {resp.status_code}")
                results[label] = False
                return
            data = resp.json()
            items = data.get(key) if isinstance(data, dict) else None
            if not items:
                results[label] = False
                return
            expected_values = {identifiers.get(code_key), identifiers.get(name_key)}
            match = next((item for item in items if (item.get('code') or item.get('name')) in expected_values), None)
            results[label] = match is not None
        except Exception as exc:
            logging.error(f"Error fetching {label}: {exc}")
            results[label] = False

    _exists(f"service-points?query=code=={identifiers['service_point_code']}", 'servicepoints', 'ServicePoint', 'service_point_code', 'service_point_name')
    _exists(f"location-units/institutions?query=code=={identifiers['institution_code']}", 'locinsts', 'Institution', 'institution_code', 'institution_name')
    _exists(f"location-units/campuses?query=code=={identifiers['campus_code']}", 'loccamps', 'Campus', 'campus_code', 'campus_name')
    _exists(f"location-units/libraries?query=code=={identifiers['library_code']}", 'loclibs', 'Library', 'library_code', 'library_name')
    _exists(f"locations?query=code=={identifiers['location_code']}", 'locations', 'Location', 'location_code', 'location_name')

    success = all(results.values()) if results else False
    return success, results

def post_holdings(instance_id):
    """Create holdings record for analytics - location is optional"""
    url = f'{st.session_state.okapi}/holdings-storage/holdings'
    headers = {
        "x-okapi-tenant": f"{st.session_state.tenant}",
        "x-okapi-token": f"{st.session_state.token}",
        "Content-Type": "application/json"
    }
    
    # Get source ID (MARC source)
    source_id = None
    try:
        sources_url = f'{st.session_state.okapi}/instance-sources?limit=1000'
        sources_response = requests.get(sources_url, headers=headers)
        if sources_response.status_code == 200:
            sources_data = sources_response.json()
            if sources_data.get('instanceSources') and len(sources_data['instanceSources']) > 0:
                # Find FOLIO source or use first one
                for source in sources_data['instanceSources']:
                    if source.get('name') == 'FOLIO' or source.get('code') == 'folio':
                        source_id = source['id']
                        break
                if not source_id:
                    source_id = sources_data['instanceSources'][0]['id']
    except:
        pass
    
    # If no source found, use default FOLIO source ID
    if not source_id:
        source_id = "f32d531e-df79-46b3-8932-cdd35f7a2264"
    
    # Get or create dummy suppressed location for analytics
    location_id = create_dummy_suppressed_location()
    
    # Note: Only discoverySuppress=True (not staffSuppress) so it's visible to staff but hidden from public discovery
    data = {
        "instanceId": instance_id,
        "sourceId": source_id,
        "discoverySuppress": True
        # DO NOT set staffSuppress - holdings need to be visible to staff for analytics
    }
    
    # Add location if we got one
    if location_id:
        data["permanentLocationId"] = str(location_id)
    else:
        logging.warning("Could not create dummy location, creating holdings without location")

    logging.info(f"Creating holdings with data: {json.dumps(data, indent=2)}")
    response = requests.post(url, headers=headers, json=data)
    logging.info(f"Holdings creation response: Status={response.status_code}, Response: {response.text[:200] if response.text else 'Empty'}")

    if response.status_code == 201 or response.status_code == 200:
        # Verify holdings was created
        try:
            if response.text and response.text.strip():
                holdings_data = response.json()
                holdings_id = holdings_data.get('id')
                if holdings_id:
                    logging.info(f"Holdings created successfully with ID: {holdings_id}")
                    return True
        except:
            pass
        
        # Check Location header
        location_header = response.headers.get('Location', '')
        if location_header:
            logging.info(f"Holdings created, Location: {location_header}")
            return True
        
        logging.warning("Holdings creation returned 201 but could not verify ID")
        return True  # Still return True as API says it was created
    else:
        error_text = response.text[:500] if response.text else 'No response text'
        logging.error(f"Failed to create holdings: {response.status_code} - {error_text}")
        if hasattr(st, 'error'):
            st.error(f"❌ Holdings creation failed: {response.status_code} - {error_text[:200]}")
        return False


def get_holdings_id(instance_id):
    url = f'{st.session_state.okapi}/holdings-storage/holdings?limit=1000&query=instanceId%3D%3D{instance_id}'
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}


    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        holdings_data = response.json()
        if holdings_data['holdingsRecords']:
            holding_id = holdings_data['holdingsRecords'][0]['id']
            return holding_id
        else:
            return None
    else:
        return None

def post_inventory_item(holding_id):
    """Create inventory item for analytics - location and material type are optional"""
    url = f'{st.session_state.okapi}/inventory/items'
    headers = {
        "x-okapi-tenant": f"{st.session_state.tenant}",
        "x-okapi-token": f"{st.session_state.token}",
        "Content-Type": "application/json"
    }
    
    # Try to get loan type and material type (optional)
    loan_type_id = get_loan_type_id()
    material_type_id = get_material_type_id()
    
    # Get or create dummy suppressed location for analytics
    location_id = create_dummy_suppressed_location()
    
    # Note: Only discoverySuppress=True (not staffSuppress) so it's visible to staff but hidden from public discovery
    data = {
        "status": {"name": "Available"},
        "holdingsRecordId": holding_id,
        "discoverySuppress": True
        # DO NOT set staffSuppress - items need to be visible to staff for analytics
    }
    
    # Add location if we got one
    if location_id:
        data["permanentLocation"] = {"id": str(location_id)}
    
    # Only add fields if they exist
    if loan_type_id:
        data["permanentLoanType"] = {"id": str(loan_type_id)}
    
    if material_type_id:
        data["materialType"] = {"id": str(material_type_id)}

    logging.info(f"Creating inventory item with data: {json.dumps(data, indent=2)}")
    logging.info(f"POST URL: {url}")
    response = requests.post(url, headers=headers, json=data)
    logging.info(f"Item creation response: Status={response.status_code}, Response: {response.text}")

    if response.status_code == 201 or response.status_code == 200:
        item_id = None
        # Verify item was created
        try:
            if response.text and response.text.strip():
                item_data = response.json()
                item_id = item_data.get('id')
                if item_id:
                    logging.info(f"Inventory item created successfully with ID: {item_id}")
        except:
            pass
        
        # Check Location header if no ID from response
        if not item_id:
            location_header = response.headers.get('Location', '')
            if location_header:
                # Extract ID from location header
                if 'http' in location_header:
                    parts = location_header.rstrip('/').split('/')
                    if parts:
                        item_id = parts[-1]
                else:
                    parts = location_header.strip('/').split('/')
                    if len(parts) >= 2:
                        item_id = parts[-1]
        
        # Now verify the item actually exists via API
        if item_id:
            # Wait a moment for indexing
            import time
            time.sleep(1)
            
            # Verify item exists by direct GET
            verify_url = f'{st.session_state.okapi}/inventory/items/{item_id}'
            verify_response = requests.get(verify_url, headers=headers)
            if verify_response.status_code == 200:
                verify_data = verify_response.json()
                logging.info(f"✅ Item verified via API: {item_id}, HoldingsRecordId: {verify_data.get('holdingsRecordId')}")
                return True
            else:
                logging.warning(f"Item ID {item_id} returned from API but GET failed: {verify_response.status_code}")
        
        if item_id:
            return True  # Return True if we got an ID, even if verification failed
        else:
            logging.warning("Item creation returned 201 but could not extract ID")
            return True  # Still return True as API says it was created
    else:
        error_text = response.text[:500] if response.text else 'No response text'
        logging.error(f"Failed to create inventory item: {response.status_code} - {error_text}")
        if hasattr(st, 'error'):
            st.error(f"❌ Inventory item creation failed: {response.status_code} - {error_text[:200]}")
        return False

def post_loan_period():

    url = f'{st.session_state.okapi}/loan-policy-storage/loan-policies?limit=1000&query=cql.allRecords%3D1'
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    data = {
        "name": f"{st.session_state.tenant} Loan Policy",
        "loanable": False,
        "renewable": False
    }

    response = requests.post(url, headers=headers, json=data)
    # Response output suppressed - return success status
    return response.status_code == 200

def post_overdue_fines_policy():
    url = f'{st.session_state.okapi}/overdue-fines-policies?limit=1000&query=cql.allRecords%3D1'
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    data = {
        "countClosed": True,
        "forgiveOverdueFine": True,
        "gracePeriodRecall": True,
        "maxOverdueFine": "0.00",
        "maxOverdueRecallFine": "0.00",
        "name": f"{st.session_state.tenant} Loan Policy"
    }

    response = requests.post(url, headers=headers, json=data)
    # st.write(response)
    # st.write(response.status_code)

def post_lost_item_fees_policy():
    url = f'{st.session_state.okapi}/lost-item-fees-policies?limit=1000&query=cql.allRecords%3D1'
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    data = {
        "chargeAmountItem": {
            "amount": "0.00",
            "amountWithoutVat": "0.00",
            "vat": "0.00",
            "chargeType": "anotherCost"
        },
        "lostItemProcessingFee": "0.00",
        "chargeAmountItemPatron": False,
        "chargeAmountItemSystem": False,
        "returnedLostItemProcessingFee": False,
        "replacedLostItemProcessingFee": False,
        "replacementProcessingFee": "0.00",
        "replacementAllowed": False,
        "lostItemReturned": "Charge",
        "name": f"{st.session_state.tenant} Lost Policy",
        "vat": "0",
        "lostItemProcessingFeeWithoutVat": "0.00",
    }

    response = requests.post(url, headers=headers, json=data)
    # Response output suppressed - return success status
    return response.status_code == 200

def post_patron_notice_policy():
    url = f'{st.session_state.okapi}/patron-notice-policy-storage/patron-notice-policies?limit=1000&query=cql.allRecords%3D1'
    headers = {"x-okapi-tenant": f"{st.session_state.tenant}", "x-okapi-token": f"{st.session_state.token}"}
    data = {
        "name": f"{st.session_state.tenant} Notice Policy"
    }

    response = requests.post(url, headers=headers, json=data)


# Embedded Portal Configuration Payloads (from Postman collection)
# These payloads are embedded directly in the code for Basic Configuration

MARC_CONFIG_ID = '541ffdc2-8cc4-46fa-a223-0bc075537396'
ITEM_CONFIG_ID = 'd711117f-5dc8-4ac2-8ed3-55b8540b5d55'

# MARC Configuration Payload (130 configurations)
MARC_CONFIG_PAYLOAD = {
    "configurations": [
        {"fieldName": "title", "from": None, "to": None, "fieldType": "search", "tags": ["245"], "indicator1": None, "indicator2": None, "subfields": None, "joinBy": "", "multi": False, "regex": None},
        {"fieldName": "lccn", "from": None, "to": None, "fieldType": "search", "tags": ["010"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "lccn", "from": None, "to": None, "fieldType": "display", "tags": ["010"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "isbn", "from": None, "to": None, "fieldType": "search", "tags": ["020"], "indicator1": None, "indicator2": None, "subfields": ["a", "z"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "isbn_se_0", "from": None, "to": None, "fieldType": "search", "tags": ["776", "786"], "indicator1": None, "indicator2": None, "subfields": ["z"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "isbn", "from": None, "to": None, "fieldType": "display", "tags": ["020"], "indicator1": None, "indicator2": None, "subfields": ["a", "z"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "issn", "from": None, "to": None, "fieldType": "search", "tags": ["022"], "indicator1": None, "indicator2": None, "subfields": ["a", "y", "z"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "issn", "from": None, "to": None, "fieldType": "display", "tags": ["022"], "indicator1": None, "indicator2": None, "subfields": ["a", "y", "z"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "doi", "from": None, "to": None, "fieldType": "display", "tags": ["024"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "language_fa_0", "from": None, "to": None, "fieldType": "facet", "tags": ["041"], "indicator1": None, "indicator2": None, "subfields": ["d"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "language_fa_1", "from": None, "to": None, "fieldType": "facet", "tags": ["041"], "indicator1": None, "indicator2": None, "subfields": ["e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "language_fa_2", "from": None, "to": None, "fieldType": "facet", "tags": ["041"], "indicator1": None, "indicator2": None, "subfields": ["f"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "language_fa_3", "from": None, "to": None, "fieldType": "facet", "tags": ["041"], "indicator1": None, "indicator2": None, "subfields": ["g"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "language_fa_4", "from": None, "to": None, "fieldType": "facet", "tags": ["041"], "indicator1": None, "indicator2": None, "subfields": ["j"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "notrim_lc", "from": None, "to": None, "fieldType": "search", "tags": ["050"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "notrim_lc", "from": None, "to": None, "fieldType": "display", "tags": ["050"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "notrim_lc", "from": None, "to": None, "fieldType": "facet", "tags": ["050"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "lc_and_local", "from": None, "to": None, "fieldType": "search", "tags": ["050", "090"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "lc_and_local", "from": None, "to": None, "fieldType": "display", "tags": ["050", "090"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "lc_and_local", "from": None, "to": None, "fieldType": "facet", "tags": ["050", "090"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "nlm_cn", "from": None, "to": None, "fieldType": "search", "tags": ["060"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "nlm_cn", "from": None, "to": None, "fieldType": "display", "tags": ["060"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "local_cn", "from": None, "to": None, "fieldType": "search", "tags": ["090", "091", "092", "093", "094", "095", "096", "097", "098", "099"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "local_cn", "from": None, "to": None, "fieldType": "display", "tags": ["090", "091", "092", "093", "094", "095", "096", "097", "098", "099"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author", "from": None, "to": None, "fieldType": "search", "tags": ["100", "700"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_main", "from": None, "to": None, "fieldType": "display", "tags": ["100"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": False, "regex": None},
        {"fieldName": "contributors", "from": None, "to": None, "fieldType": "display", "tags": ["700"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_corporate", "from": None, "to": None, "fieldType": "search", "tags": ["110", "710"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_corporate_main", "from": None, "to": None, "fieldType": "display", "tags": ["110"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": False, "regex": None},
        {"fieldName": "contributors_corporate", "from": None, "to": None, "fieldType": "display", "tags": ["710"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_meeting", "from": None, "to": None, "fieldType": "search", "tags": ["111", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_meeting_main", "from": None, "to": None, "fieldType": "display", "tags": ["111"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": False, "regex": None},
        {"fieldName": "contributors_meeting", "from": None, "to": None, "fieldType": "display", "tags": ["711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_all", "from": None, "to": None, "fieldType": "search", "tags": ["100", "700", "110", "710", "111", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_all", "from": None, "to": None, "fieldType": "display", "tags": ["100", "700", "110", "710", "111", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_all", "from": None, "to": None, "fieldType": "facet", "tags": ["100", "700", "110", "710", "111", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_no_edc_all", "from": None, "to": None, "fieldType": "search", "tags": ["100", "700", "110", "710", "111", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_no_edc_all", "from": None, "to": None, "fieldType": "display", "tags": ["100", "700", "110", "710", "111", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_no_edc_all", "from": None, "to": None, "fieldType": "facet", "tags": ["100", "700", "110", "710", "111", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_one100", "from": None, "to": None, "fieldType": "search", "tags": ["100", "110", "111"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_one100", "from": None, "to": None, "fieldType": "display", "tags": ["100", "110", "111"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "author_one100", "from": None, "to": None, "fieldType": "facet", "tags": ["100", "110", "111"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "cont_one700", "from": None, "to": None, "fieldType": "search", "tags": ["700", "710", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "cont_one700", "from": None, "to": None, "fieldType": "display", "tags": ["700", "710", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "cont_one700", "from": None, "to": None, "fieldType": "facet", "tags": ["700", "710", "711"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "main_entery_uniform_title", "from": None, "to": None, "fieldType": "display", "tags": ["130", "730"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "abbreviated_title", "from": None, "to": None, "fieldType": "display", "tags": ["210"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "periodical_title", "from": None, "to": None, "fieldType": "display", "tags": ["222"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "uniform_title", "from": None, "to": None, "fieldType": "display", "tags": ["240", "740"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "translation_title", "from": None, "to": None, "fieldType": "display", "tags": ["242"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "collective_uniform_title", "from": None, "to": None, "fieldType": "display", "tags": ["243"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title", "from": None, "to": None, "fieldType": "display", "tags": ["245"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title_abh", "from": None, "to": None, "fieldType": "display", "tags": ["245"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "h"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title_all", "from": None, "to": None, "fieldType": "display", "tags": ["245"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title_medium", "from": None, "to": None, "fieldType": "display", "tags": ["245"], "indicator1": None, "indicator2": None, "subfields": ["h"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "varying_form_title", "from": None, "to": None, "fieldType": "display", "tags": ["246"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "former_title", "from": None, "to": None, "fieldType": "display", "tags": ["247"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "alternetive_title", "from": None, "to": None, "fieldType": "display", "tags": ["210", "240", "740", "242", "243", "246", "247"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title", "from": None, "to": None, "fieldType": "search", "tags": ["130", "210", "222", "240", "740", "245", "242", "243", "246", "247"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title_se_0", "from": None, "to": None, "fieldType": "search", "tags": ["505", "772"], "indicator1": None, "indicator2": None, "subfields": ["t"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title_se_1", "from": None, "to": None, "fieldType": "search", "tags": ["770", "774", "776", "787"], "indicator1": None, "indicator2": None, "subfields": ["t", "s"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title_se_2", "from": None, "to": None, "fieldType": "search", "tags": ["630", "730"], "indicator1": None, "indicator2": None, "subfields": ["a", "d", "e", "f", "g", "k", "p", "r", "t"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "title_se_3", "from": None, "to": None, "fieldType": "search", "tags": ["800", "810", "811", "830"], "indicator1": None, "indicator2": None, "subfields": ["f", "k", "p", "r", "n", "s", "t", "g", "v"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "edition", "from": None, "to": None, "fieldType": "display", "tags": ["250", "251", "254"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "3"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_info", "from": None, "to": None, "fieldType": "display", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "e", "f", "g", "m"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_date_hijri", "from": None, "to": None, "fieldType": "display", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["m"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_place", "from": None, "to": None, "fieldType": "search", "tags": ["260"], "indicator1": None, "indicator2": None, "subfields": ["e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_place_se_0", "from": None, "to": None, "fieldType": "search", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_place", "from": None, "to": None, "fieldType": "display", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_place", "from": None, "to": None, "fieldType": "facet", "tags": ["260"], "indicator1": None, "indicator2": None, "subfields": ["e"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_place_fa_0", "from": None, "to": None, "fieldType": "facet", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_date", "from": None, "to": None, "fieldType": "search", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["c", "g"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_date", "from": None, "to": None, "fieldType": "facet", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["c", "g"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_date", "from": None, "to": None, "fieldType": "display", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["c", "g"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publication_date_srt", "from": None, "to": None, "fieldType": "display", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["c"], "joinBy": "", "multi": False, "regex": None},
        {"fieldName": "publisher", "from": None, "to": None, "fieldType": "search", "tags": ["260"], "indicator1": None, "indicator2": None, "subfields": ["f"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publisher_se_0", "from": None, "to": None, "fieldType": "search", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publisher", "from": None, "to": None, "fieldType": "facet", "tags": ["260"], "indicator1": None, "indicator2": None, "subfields": ["f"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publisher_fa_0", "from": None, "to": None, "fieldType": "facet", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "publisher", "from": None, "to": None, "fieldType": "display", "tags": ["260", "264"], "indicator1": None, "indicator2": None, "subfields": ["b", "f"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "physical_description", "from": None, "to": None, "fieldType": "display", "tags": ["300", "306", "307"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "physical_description_subs", "from": None, "to": None, "fieldType": "display", "tags": ["300", "306", "307"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "e", "f", "g"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "current_pub_freq", "from": None, "to": None, "fieldType": "display", "tags": ["310"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "former_pub_freq", "from": None, "to": None, "fieldType": "display", "tags": ["321"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "pub_freq", "from": None, "to": None, "fieldType": "facet", "tags": ["310", "321"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "content_type", "from": None, "to": None, "fieldType": "display", "tags": ["336"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "media_type", "from": None, "to": None, "fieldType": "display", "tags": ["337"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "carrier_type", "from": None, "to": None, "fieldType": "display", "tags": ["338"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "dates_pub_seq", "from": None, "to": None, "fieldType": "display", "tags": ["362"], "indicator1": None, "indicator2": None, "subfields": ["a", "z"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "other_physical_description", "from": None, "to": None, "fieldType": "display", "tags": ["340", "341", "342", "343", "344", "345", "346", "347", "348", "349", "350", "351", "352", "353", "354", "355", "356", "357", "358", "359", "370", "371", "372", "373", "374", "375", "376", "377", "378", "379", "380", "381", "382", "383", "384", "385", "386", "387", "388", "389", "390", "391", "392", "393", "394", "395", "396", "397", "398", "399"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "hsl_note", "from": None, "to": None, "fieldType": "display", "tags": ["500", "505", "520"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "hsl_note", "from": None, "to": None, "fieldType": "search", "tags": ["500", "505", "520"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "general_note", "from": None, "to": None, "fieldType": "display", "tags": ["500"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "with_note", "from": None, "to": None, "fieldType": "display", "tags": ["501"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "disertation_note", "from": None, "to": None, "fieldType": "display", "tags": ["502"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "g", "o"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "disertation_note", "from": None, "to": None, "fieldType": "search", "tags": ["502"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "g", "o"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "disertation_note_type", "from": None, "to": None, "fieldType": "facet", "tags": ["502"], "indicator1": None, "indicator2": None, "subfields": ["b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "disertation_note_name", "from": None, "to": None, "fieldType": "facet", "tags": ["502"], "indicator1": None, "indicator2": None, "subfields": ["c"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "note_etc", "from": None, "to": None, "fieldType": "display", "tags": ["504"], "indicator1": None, "indicator2": None, "subfields": ["a", "b"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "content_note", "from": None, "to": None, "fieldType": "display", "tags": ["505"], "indicator1": None, "indicator2": None, "subfields": ["a", "g", "r", "t", "u"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "summery", "from": None, "to": None, "fieldType": "display", "tags": ["520"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "u"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "summery", "from": None, "to": None, "fieldType": "search", "tags": ["520"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "u"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "system_details_note", "from": None, "to": None, "fieldType": "display", "tags": ["538"], "indicator1": None, "indicator2": None, "subfields": ["u"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "note_aqu", "from": None, "to": None, "fieldType": "display", "tags": ["541"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "h", "n", "o"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "local_note", "from": None, "to": None, "fieldType": "display", "tags": ["590", "591", "592", "593", "594", "595", "596", "597", "598", "599"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "subjects_geographic", "from": None, "to": None, "fieldType": "facet", "tags": ["651"], "indicator1": None, "indicator2": None, "subfields": ["a"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "subjects_geographic_fa_0", "from": None, "to": None, "fieldType": "facet", "tags": ["600", "610", "611", "630", "647", "648", "650", "651", "654", "655"], "indicator1": None, "indicator2": None, "subfields": ["z"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "subjects_form", "from": None, "to": None, "fieldType": "facet", "tags": ["600", "610", "611", "630", "647", "648", "650", "651", "654", "655"], "indicator1": None, "indicator2": None, "subfields": ["v"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "subjects_general", "from": None, "to": None, "fieldType": "facet", "tags": ["600", "610", "611", "630", "647", "648", "650", "651", "654", "655"], "indicator1": None, "indicator2": None, "subfields": ["x"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "subjects", "from": None, "to": None, "fieldType": "search", "tags": ["600", "610", "611", "630", "647", "648", "650", "651", "653", "654", "655", "656", "689"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "w", "x", "z", "y", "v"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "subjects", "from": None, "to": None, "fieldType": "display", "tags": ["600", "610", "611", "630", "647", "648", "650", "651", "653", "654", "655", "656", "689"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "w", "x", "z", "y", "v"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "subjects", "from": None, "to": None, "fieldType": "facet", "tags": ["600", "610", "611", "630", "647", "648", "650", "651", "653", "654", "655", "656", "689"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "w", "x", "z", "y", "v"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "main_series_entry", "from": None, "to": None, "fieldType": "display", "tags": ["760"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "subseries_entry", "from": None, "to": None, "fieldType": "display", "tags": ["762"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "original_language_entry", "from": None, "to": None, "fieldType": "display", "tags": ["765"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "translation_entry", "from": None, "to": None, "fieldType": "display", "tags": ["767"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "supplement", "from": None, "to": None, "fieldType": "display", "tags": ["770"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "supplement_parent_entry", "from": None, "to": None, "fieldType": "display", "tags": ["772"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "host_item_entry", "from": None, "to": None, "fieldType": "display", "tags": ["773"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "constituent_unit_entry", "from": None, "to": None, "fieldType": "display", "tags": ["774"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "other_edition_entry", "from": None, "to": None, "fieldType": "display", "tags": ["775"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "issued_with_entry", "from": None, "to": None, "fieldType": "display", "tags": ["777"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "preceding_entry", "from": None, "to": None, "fieldType": "display", "tags": ["780"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "series_added_entry_personal_name", "from": None, "to": None, "fieldType": "display", "tags": ["800"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "series_added_entry_corporate_name", "from": None, "to": None, "fieldType": "display", "tags": ["810"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "series_added_entry_meeting_name", "from": None, "to": None, "fieldType": "display", "tags": ["811"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "full_text_urlu", "from": None, "to": None, "fieldType": "display", "tags": ["856"], "indicator1": None, "indicator2": None, "subfields": ["u"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "full_text_url", "from": None, "to": None, "fieldType": "display", "tags": ["856"], "indicator1": None, "indicator2": None, "subfields": ["u", "z"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "full_text_url_all", "from": None, "to": None, "fieldType": "display", "tags": ["856"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None},
        {"fieldName": "summery_of_holdings", "from": None, "to": None, "fieldType": "display", "tags": ["866"], "indicator1": None, "indicator2": None, "subfields": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], "joinBy": "", "multi": True, "regex": None}
    ]
}

# Item/Holding Configuration Payload (6 configurations)
ITEM_CONFIG_PAYLOAD = {
    "configurations": [
        {"fieldName": "item_barcodes", "sourceType": "item", "jsonPath": "barcode", "operation": "list", "groupBy": None, "matcher": None, "regex": None},
        {"fieldName": "locationName", "sourceType": "item", "jsonPath": "locationName", "operation": "latest", "groupBy": None, "matcher": {"path": "locationName", "operator": "=", "value": "Popular Reading Collection"}, "regex": None},
        {"fieldName": "libraryName", "sourceType": "item", "jsonPath": "libraryName", "operation": "aggregate", "groupBy": "barcode", "matcher": {"path": "libraryName", "operator": "=", "value": "Datalogisk Institut"}, "regex": None},
        {"fieldName": "materialTypeName", "sourceType": "item", "jsonPath": "materialTypeName", "operation": "list", "groupBy": None, "matcher": {"path": "materialTypeName", "operator": "=", "value": "book"}, "regex": None},
        {"fieldName": "item_status", "sourceType": "item", "jsonPath": "status.name", "operation": "list", "groupBy": None, "matcher": None, "regex": None},
        {"fieldName": "item_note", "sourceType": "item", "jsonPath": "notes.itemNoteTypeId", "operation": "aggregate", "groupBy": None, "matcher": None, "regex": None}
    ]
}

def load_postman_collection_payloads():
    """Load MARC and Item/Holding configuration payloads - embedded in code"""
    return {
        'marc_config': MARC_CONFIG_PAYLOAD,
        'item_config': ITEM_CONFIG_PAYLOAD,
        'marc_config_id': MARC_CONFIG_ID,
        'item_config_id': ITEM_CONFIG_ID
    }


async def configure_portal_marc():
    """Configure MARC configuration for portal integration"""
    try:
        payloads = load_postman_collection_payloads()
        
        url = f"{st.session_state.okapi}/portal-ingestor/marc-configurations/{payloads['marc_config_id']}"
        headers = {
            "x-okapi-tenant": f"{st.session_state.tenant}",
            "x-okapi-token": f"{st.session_state.token}",
            "Content-Type": "application/json"
        }
        
        response = await async_request("PUT", url, headers=headers, data=json.dumps(payloads['marc_config']))
        return True
    except Exception as e:
        logging.error(f"Error configuring MARC: {str(e)}")
        return False


async def configure_portal_item_holding():
    """Configure Item/Holding configuration for portal integration"""
    try:
        payloads = load_postman_collection_payloads()
        
        url = f"{st.session_state.okapi}/portal-ingestor/item-holding-configurations/{payloads['item_config_id']}"
        headers = {
            "x-okapi-tenant": f"{st.session_state.tenant}",
            "x-okapi-token": f"{st.session_state.token}",
            "Content-Type": "application/json"
        }
        
        response = await async_request("PUT", url, headers=headers, data=json.dumps(payloads['item_config']))
        return True
    except Exception as e:
        logging.error(f"Error configuring Item/Holding: {str(e)}")
        return False


async def configure_portal_medad():
    """Configure Medad configuration for portal integration"""
    # Medad configuration - this might need to be customized based on specific requirements
    # For now, we'll use a placeholder or check if there's a specific endpoint
    # This can be updated based on actual Medad configuration requirements
    try:
        # If there's a specific Medad configuration endpoint, add it here
        # For now, we'll return True as a placeholder
        return True
    except Exception as e:
        logging.error(f"Error configuring Medad: {str(e)}")
        return False


def send_completion_email(config_type, output_log, tenant_name):
    """Send email notification when configuration is completed"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    try:
        sender_email = "ilsconfigration@gmail.com"
        sender_password = "pmgargvvawxpltow"
        receiver_email = "ilsconfigration@gmail.com"
        tenant_upper = tenant_name.upper()
        subject = f"{tenant_upper}_{config_type.upper()} CONFIGURATION Completed"
        
        msg = MIMEMultipart('alternative')
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        
        plain_body = f"Tenant: {tenant_upper}\n\n{config_type} configuration has completed.\n\nDetails:\n{output_log}\n\nPlease review the tenant to confirm everything is set up correctly."

        html_body = f"""
        <html>
          <head>
            <style>
              body {{ font-family: Arial, sans-serif; color: #333; }}
              .wrapper {{ background: #f4f6fb; padding: 24px; }}
              .card {{ max-width: 720px; margin: 0 auto; background: #fff; border-radius: 12px; box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08); overflow: hidden; }}
              .header {{ background: linear-gradient(135deg, #1f4e79 0%, #1e83c2 100%); color: #fff; padding: 24px 32px; }}
              .header h1 {{ margin: 0; font-size: 24px; }}
              .meta {{ padding: 20px 32px; border-bottom: 1px solid #eef2f7; font-size: 14px; color: #475569; }}
              .meta strong {{ display: block; color: #0f172a; font-size: 15px; margin-bottom: 4px; }}
              .summary {{ padding: 24px 32px; }}
              .summary h2 {{ font-size: 18px; margin-top: 0; color: #1f2937; }}
              pre {{ background: #f8fafc; padding: 16px; border-radius: 8px; font-size: 13px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; margin: 0; border: 1px solid #e2e8f0; }}
              .footer {{ padding: 16px 32px 24px; font-size: 13px; color: #64748b; border-top: 1px solid #eef2f7; }}
            </style>
          </head>
          <body>
            <div class="wrapper">
              <div class="card">
                <div class="header">
                  <h1>Configuration Completed</h1>
                  <div>{tenant_upper}</div>
                </div>
                <div class="meta">
                  <strong>Tenant</strong>
                  {tenant_upper}
                  <strong>Configuration</strong>
                  {config_type}
                </div>
                <div class="summary">
                  <h2>Summary</h2>
                  <pre>{output_log}</pre>
                </div>
                <div class="footer">
                  Please review the configuration inside the tenant to confirm everything looks correct.
                </div>
              </div>
            </div>
          </body>
        </html>
        """

        msg.attach(MIMEText(plain_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.set_debuglevel(0)
        server.starttls()
        
        try:
            server.login(sender_email, sender_password)
        except smtplib.SMTPAuthenticationError as auth_error:
            logging.error(f"SMTP Authentication failed: {auth_error}")
            if hasattr(st, 'error'):
                st.error("Email authentication failed. Please verify SMTP credentials.")
            server.quit()
            return False
        
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()
        
        logging.info(f"Email sent successfully to {receiver_email}")
        return True
    except smtplib.SMTPException as smtp_error:
        error_msg = f"SMTP Error: {smtp_error}"
        logging.error(error_msg)
        if hasattr(st, 'error'):
            st.error(error_msg)
        return False
    except Exception as e:
        error_msg = f"Unexpected error sending email: {e}"
        logging.error(error_msg)
        if hasattr(st, 'error'):
            st.error(error_msg)
        return False