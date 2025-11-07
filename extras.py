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


MARC_TEMPLATES_JSON = r'''[
  {
    "module": "MARC_AUTHORITY_EDITOR",
    "id": "62c0a66a-1f8e-4b4d-bfd8-8b58f0831500",
    "title": "AUTHROTY-RDA-2015 - AUC-TEMP-PERSON-PORTAL",
    "description": "AUC-TEMP-PERSON-PORTAL",
    "content": {
      "fields": [
        {
          "tag": "001",
          "content": "6235009",
          "isProtected": true,
          "id": "25504846-ba8b-4584-aeff-ac54a518f813",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "005",
          "content": "20250506052508.4",
          "isProtected": false,
          "id": "a0ef6a05-5313-486c-ae50-399db1c093c1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Date Ent": "150301",
            "Geo Subd": "\\",
            "Roman": "n",
            "Lang": "|",
            "Kind rec": "a",
            "Cat Rules": "z",
            "SH Sys": "z",
            "Series": "n",
            "Numb Series": "n",
            "Main use": "a",
            "Subj use": "a",
            "Series use": "b",
            "Type Subd": "n",
            "Undef_18": "\\\\\\\\\\\\\\\\\\\\",
            "Govt Ag": "\\",
            "RefEval": "a",
            "Undef_30": "\\",
            "RecUpd": "a",
            "Pers Name": "a",
            "Level Est": "d",
            "Undef_34": "\\\\\\\\",
            "Mod Rec Est": "|",
            "Source": "c"
          },
          "isProtected": false,
          "id": "3f17bd6d-6844-4f93-8819-c2345e50f813",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $f aucnm $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6af13463-0520-4aa4-bb52-79e03c16ab89",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "046",
          "content": "$f : $g :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1799ae40-b149-48b1-81de-8fc7500a0d16",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "075",
          "content": "$a Ø§Ø³Ù Ø´Ø®Øµâªâªâª $b nm $2 auce",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2ffc5365-417c-4b08-b3f7-4c19599a752d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $b : $c : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "0a5a78f8-c1f9-439e-ac49-551dcf583a08",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "370",
          "content": "$a : $b : $2 aucsh",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6e0f0915-bf0f-46f5-9c7b-31b718c75321",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "371",
          "content": "$a : $b : $c : $d : $e : $m : $u : $z :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bfcf2cdd-ef48-4b70-937d-4cad4f5c4b38",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "372",
          "content": "$a : $2 aucsh",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b71eab7c-faed-4ed8-a437-c252fa4c3a71",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "373",
          "content": "$a : $2 aucnm",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3d05668c-f152-49c9-92cc-2b5abd57df99",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "374",
          "content": "$a : $2 aucsh",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "098c4c03-ec15-49e5-a8c5-41dcd192a7ef",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "375",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0491a640-daec-4705-965b-4fc593f38c59",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "377",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ed60a390-dd89-4832-a8d1-032a93026464",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "378",
          "content": "$q :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5e319df8-f553-4289-8338-f452bac9a341",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "400",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "0787c348-9f03-4ad1-a83b-a1ba0713b69b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "8afe7ed5-ca91-4a6c-b897-3f29366945fb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "670",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "daa16c61-aa39-4783-981b-027ac55f693c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "678",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ba3d3405-db6f-418c-a22e-979c5e4cc63f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "cbf0860b-fb62-40fb-aa87-2fd6014f5457",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "fd679263-a8c7-433b-ba95-9378d82f1afa",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00675",
        "status": "c",
        "type": "z",
        "undefined": "\\\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00289",
        "encoding": "n",
        "punctuation": "\\",
        "undefined1": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined2": "0"
      }
    }
  },
  {
    "module": "MARC_AUTHORITY_EDITOR",
    "id": "0878d728-77af-4055-a61c-c21966e67ed4",
    "title": "AUC Subjects (Topical/Gegraphical) - AUC-TEMP-GEOGRAPIC-PORTAL",
    "description": "ÙÙØ¶ÙØ¹ (ÙÙØ¶ÙØ¹Ù/Ø¬ØºØ±Ø§ÙÙ)",
    "content": {
      "fields": [
        {
          "tag": "001",
          "content": "6235091",
          "isProtected": true,
          "id": "98afaa09-1f33-40e8-917b-f205c38a2380",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "005",
          "content": "20250506052508.8",
          "isProtected": false,
          "id": "105a57c8-7394-41c0-88fc-2f6bb6bfae4a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "003",
          "content": "SA-RiAUC",
          "isProtected": false,
          "id": "1b1205f2-8f9c-4452-97a7-31a22b4a0342",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Date Ent": "071208",
            "Geo Subd": "|",
            "Roman": "n",
            "Lang": "|",
            "Kind rec": "a",
            "Cat Rules": "z",
            "SH Sys": "z",
            "Series": "n",
            "Numb Series": "n",
            "Main use": "b",
            "Subj use": "a",
            "Series use": "b",
            "Type Subd": "|",
            "Undef_18": "\\\\\\\\\\\\\\\\\\\\",
            "Govt Ag": "\\",
            "RefEval": "|",
            "Undef_30": "\\",
            "RecUpd": "a",
            "Pers Name": "n",
            "Level Est": "a",
            "Undef_34": "\\\\\\\\",
            "Mod Rec Est": "|",
            "Source": "c"
          },
          "isProtected": false,
          "id": "5877932b-35fa-40d0-8704-f838b494326d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $f aucsh $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "27109ac3-5955-4d20-86ff-1b08257d9da0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "af7fcaf6-1b0e-4047-8b15-bff971ac7825",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "053",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "1c83a88e-e081-4df9-8398-93fe75fd0a93",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "075",
          "content": "$a ÙÙØ§Ù Ø¬ØºØ±Ø§ÙÙâªâªâª $b ge $2 auce",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e2b77772-8409-4fd0-83df-c674fd830774",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "083",
          "content": "$a :",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "8b62a0d4-42ec-4259-b8be-34f12cf0e66e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "151",
          "content": "$a : $x : $z : $y : $v :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1be8b361-917a-430a-86fd-c8770331a00f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "360",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "41dddd86-baf3-4789-8d49-b479b461362d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "451",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4799a9fa-a797-4fbc-b5ee-e2050ce1280a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "451",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bc6bf8db-65f2-40c3-b3cc-b3852e33e109",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "551",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "25951e52-81ce-4117-ad35-4dc1a8f9b94d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "677",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6751dfc5-06d1-4694-8834-44c91ae87cdd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "680",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "586c8135-1147-4637-a4cb-95d3c695739b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "681",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "05a36440-3176-46ef-9ac5-a0fb3dcb6a7d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "751",
          "content": "$a : $0 :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "e5ebadd8-a66f-4cdd-a1f9-1f61e129b868",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "781",
          "content": "$z : $z : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "e22bdc1d-be3a-493a-bf67-8e90b7352212",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u : $x :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "fe4126b0-adc2-4959-8554-bb194820e9a4",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00625",
        "status": "c",
        "type": "z",
        "undefined": "\\\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00277",
        "encoding": "n",
        "punctuation": "\\",
        "undefined1": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined2": "0"
      }
    }
  },
  {
    "module": "MARC_AUTHORITY_EDITOR",
    "id": "a7f24d98-556f-45c9-8f2d-8b51d4e236db",
    "title": "AUC Subjects (Topical/Gegraphical) - AUC-TEMP-SUBJECT-PORTAL",
    "description": "ÙÙØ¶ÙØ¹ (ÙÙØ¶ÙØ¹Ù/Ø¬ØºØ±Ø§ÙÙ)",
    "content": {
      "fields": [
        {
          "tag": "001",
          "content": "6235045",
          "isProtected": true,
          "id": "cdeaaa6f-7424-42f0-b96a-5b870ae0b954",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "005",
          "content": "20250506052508.6",
          "isProtected": false,
          "id": "08fb35ea-4fb2-4a21-808b-c442b99031ad",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "003",
          "content": "SA-RiAUC",
          "isProtected": false,
          "id": "042cc0a7-708e-4c0f-a765-a806ee497a93",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Date Ent": "071208",
            "Geo Subd": "|",
            "Roman": "n",
            "Lang": "|",
            "Kind rec": "a",
            "Cat Rules": "z",
            "SH Sys": "z",
            "Series": "n",
            "Numb Series": "n",
            "Main use": "b",
            "Subj use": "a",
            "Series use": "b",
            "Type Subd": "|",
            "Undef_18": "\\\\\\\\\\\\\\\\\\\\",
            "Govt Ag": "\\",
            "RefEval": "|",
            "Undef_30": "\\",
            "RecUpd": "a",
            "Pers Name": "n",
            "Level Est": "a",
            "Undef_34": "\\\\\\\\",
            "Mod Rec Est": "|",
            "Source": "c"
          },
          "isProtected": false,
          "id": "a5c20ad5-2e22-4523-945e-96451eb5bbb4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $f aucsh $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "682add5b-23c2-4727-bca8-4fcdea798c60",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "053",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "26aac1da-a34b-4edb-9cc3-ae4fb4c641a0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "075",
          "content": "$a ÙØµØ·ÙØ­ ÙÙØ¶ÙØ¹Ùâªâªâª $b su $2 auce",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fe16016d-87d0-4286-b77b-364be55409d3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "083",
          "content": "$a :",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "513e4e75-ae3a-441e-a292-95a09377f62b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "150",
          "content": "$a : $x : $z : $y : $v :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "96473dc7-0346-49b2-962a-b87b33bce2f0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "360",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "deea3932-6754-4672-8516-ea7ddf6469be",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "450",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d810ff1d-ce73-4938-b1df-9207782535ae",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "550",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e7e253d1-778f-4397-8c5f-83fe82fa7eae",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "677",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b3c8c2f1-9793-4d48-b2ab-a9dd001f4044",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "680",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bfa80391-237c-4347-902e-1d978c822dbb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "681",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7327693d-a3e5-48da-baca-95d4c3e51c47",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "750",
          "content": "$a : $0 :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "32d3cfe2-0220-47e6-a076-45a8f270125e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u : $x :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "324597fb-5e39-4ce5-91f0-46767360c0bc",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00562",
        "status": "c",
        "type": "z",
        "undefined": "\\\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00241",
        "encoding": "n",
        "punctuation": "\\",
        "undefined1": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined2": "0"
      }
    }
  },
  {
    "module": "MARC_AUTHORITY_EDITOR",
    "id": "a37646cd-7a77-48d0-97ca-015b195374c2",
    "title": "AUTHROTY-RDA-2015",
    "description": "AUTHROTY-RDA-2015",
    "content": {
      "fields": [
        {
          "tag": "001",
          "content": "",
          "isProtected": true,
          "id": "253d0bef-60cd-4ed0-8cc8-f18e540a1711",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "005",
          "content": "20250506060637.2",
          "isProtected": false,
          "id": "775864fb-f387-43c2-b944-035246300568",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Date Ent": "150301",
            "Geo Subd": "\\",
            "Roman": "n",
            "Lang": "|",
            "Kind rec": "a",
            "Cat Rules": "z",
            "SH Sys": "z",
            "Series": "n",
            "Numb Series": "n",
            "Main use": "a",
            "Subj use": "a",
            "Series use": "b",
            "Type Subd": "n",
            "Undef_18": "\\\\\\\\\\\\\\\\\\\\",
            "Govt Ag": "\\",
            "RefEval": "a",
            "Undef_30": "\\",
            "RecUpd": "a",
            "Pers Name": "a",
            "Level Est": "d",
            "Undef_34": "\\\\\\\\",
            "Mod Rec Est": "|",
            "Source": "c"
          },
          "isProtected": false,
          "id": "e827c90e-06f7-40b6-8171-bc1f28143951",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $f aucnm $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fd130579-5096-4651-bdee-bd9638edfc3c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "046",
          "content": "$f : $g :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3f8b69b8-454b-4a89-98f1-10799b8a1779",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "075",
          "content": "$a Ø§Ø³Ù Ø´Ø®Øµ $b nm $2 auce",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "72931a98-fc5c-4ff5-9981-6c827b156718",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "368",
          "content": "$c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8491c59f-2a76-4d8b-baff-94d4715d8922",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "370",
          "content": "$a : $2 aucsh $h :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "dae12d89-0ee6-45e7-8fb4-87f7c8c7ae0a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "371",
          "content": "$a : $b : $c : $d : $e : $m : $s : $t : $u : $v : $z :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0154418b-6a2f-4044-bc33-55d0b0c180a5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "372",
          "content": "$a : $2 aucsh $s : $t : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b9cec215-cd5d-4885-b5eb-7314619ec7b7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "373",
          "content": "$a : $2 aucnm $s : $t : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "176d7bb8-bb48-4122-8730-d2f668739f7c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "374",
          "content": "$a : $2 aucsh",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2cf01df4-6504-44d9-a175-e5746bbc4d61",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "375",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "58581dc9-1dd1-4497-81f2-19b174822c63",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "377",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a491dd2d-cca7-4e9f-9d04-fbd777124a0c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "378",
          "content": "$q :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "09256119-be89-4c03-bfd5-927f0589e26e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "400",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "5ff02781-3795-495c-a9c0-2b920afc7173",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$w r $i : $a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "fec7b5fe-6d97-4dfe-92ed-82165a382088",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "670",
          "content": "$a : $b : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "45c8d151-e0cd-4c82-8474-98cc81dd5e74",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "678",
          "content": "$a : $b : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e609577f-25f1-4a70-aa20-867d92c1bf66",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$a : $d : $0 : $1 :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "3b552c80-d5bd-4e44-b1ba-d69fc465b9d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u : $x :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "999efd61-6603-4e31-bbb4-45a105e12119",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "880",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "795e8fa5-fc9f-431b-99f4-c2f4589aa234",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00729",
        "status": "c",
        "type": "z",
        "undefined": "\\\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00301",
        "encoding": "n",
        "punctuation": "\\",
        "undefined1": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined2": "0"
      }
    }
  },
  {
    "module": "MARC_AUTHORITY_EDITOR",
    "id": "a549d6e0-d220-427f-a1fa-cf508d5c0963",
    "title": "AUC Subjects (Topical/Gegraphical) - AUC_SUBJECT-RDA",
    "description": "ÙÙØ¶ÙØ¹ (ÙÙØ¶ÙØ¹Ù)",
    "content": {
      "fields": [
        {
          "tag": "001",
          "content": "",
          "isProtected": true,
          "id": "af35de41-4277-4303-9601-e449eae74a52",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "005",
          "content": "20250506060958.1",
          "isProtected": false,
          "id": "61b7e897-8416-4782-8f40-434fa149c97d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "003",
          "content": "SA-RiAUC",
          "isProtected": false,
          "id": "6d4130ef-8602-40f0-a7e0-c75ae7c30cb6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Date Ent": "071208",
            "Geo Subd": "\\",
            "Roman": "n",
            "Lang": "|",
            "Kind rec": "a",
            "Cat Rules": "z",
            "SH Sys": "z",
            "Series": "n",
            "Numb Series": "n",
            "Main use": "b",
            "Subj use": "a",
            "Series use": "b",
            "Type Subd": "|",
            "Undef_18": "\\\\\\\\\\\\\\\\\\\\",
            "Govt Ag": "\\",
            "RefEval": "|",
            "Undef_30": "\\",
            "RecUpd": "a",
            "Pers Name": "n",
            "Level Est": "a",
            "Undef_34": "\\\\\\\\",
            "Mod Rec Est": "|",
            "Source": "c"
          },
          "isProtected": false,
          "id": "03d6634b-dde2-4488-b3f2-5d44b72001de",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $f aucsh $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "71d584d0-733a-45d1-9130-bdf502ea2bb4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "053",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "2f9ef7b4-3465-4695-a7eb-bddc95ad884c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "075",
          "content": "$a ÙØµØ·ÙØ­ ÙÙØ¶ÙØ¹Ù $b su $2 auce",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3a279d9a-754e-435b-bf49-1c1e9e0e667d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "083",
          "content": "$a :",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "e126610e-ef61-4950-a344-e5525835ce79",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "360",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "778dfd0c-6192-4222-b379-7b528678245b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "450",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6b2798ef-e02b-4bb3-b812-748bd45c7d0f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "450",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d999290b-4b86-4844-bf7c-b7b8c3d1892b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "550",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "434f987c-d5b0-47e9-9a83-0eb94ba4ecd7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "677",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ce35efdd-907c-4d2e-a7b1-3b9efacf1dc9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "680",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c2aa7a0c-11de-4364-8897-65caf6d4cdf9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "681",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "58ada28f-d9ce-48b8-810f-4349dbbfe938",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "750",
          "content": "$a : $0 :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "3de68dc5-48d8-4ea3-be4c-507353830e94",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u : $x :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "16e56cb4-b1cc-429b-a891-1bec9362be4b",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00547",
        "status": "c",
        "type": "z",
        "undefined": "\\\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00241",
        "encoding": "n",
        "punctuation": "\\",
        "undefined1": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined2": "0"
      }
    }
  },
  {
    "module": "MARC_AUTHORITY_EDITOR",
    "id": "fe0fa486-30d0-447e-b314-8e13bed3f1d8",
    "title": "AUC Subjects (Topical/Gegraphical) - AUC-GEOGRAPIC SUBJECT RDA",
    "description": "ÙÙØ¶ÙØ¹ (Ø¬ØºØ±Ø§ÙÙ)",
    "content": {
      "fields": [
        {
          "tag": "001",
          "content": "",
          "isProtected": true,
          "id": "06cde052-a303-44a9-9d62-eaefd707b446",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "005",
          "content": "20250506062516.9",
          "isProtected": false,
          "id": "9818d52b-7e9b-42a3-924f-821ea3dc7cad",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "003",
          "content": "SA-RiAUC",
          "isProtected": false,
          "id": "496799cd-be04-428f-be5c-8da4bfe56eb8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Date Ent": "071208",
            "Geo Subd": "\\",
            "Roman": "n",
            "Lang": "|",
            "Kind rec": "a",
            "Cat Rules": "z",
            "SH Sys": "z",
            "Series": "n",
            "Numb Series": "n",
            "Main use": "b",
            "Subj use": "a",
            "Series use": "b",
            "Type Subd": "|",
            "Undef_18": "\\\\\\\\\\\\\\\\\\\\",
            "Govt Ag": "\\",
            "RefEval": "|",
            "Undef_30": "\\",
            "RecUpd": "a",
            "Pers Name": "n",
            "Level Est": "a",
            "Undef_34": "\\\\\\\\",
            "Mod Rec Est": "|",
            "Source": "c"
          },
          "isProtected": false,
          "id": "ced9b565-4f9e-4d35-bad3-81273bc97611",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $f aucsh $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "199edeb4-7d09-404c-aab5-868329190a81",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "df8bc0d8-faf2-4103-be6c-95c61cb1d049",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "053",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "e88761fe-226a-4975-b8d6-85b980753c16",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "075",
          "content": "$a ÙÙØ§Ù Ø¬ØºØ±Ø§ÙÙ $b ge $2 auce",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c833c740-6d5d-403c-849c-c624787971fe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "083",
          "content": "$a :",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "6ce4dfdd-e5a8-4b6a-88fa-fb2cb243811a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "360",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "16a7da4a-ac07-401b-8bb0-20b04c9009ab",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "451",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fd74e645-1bcb-4c9a-9d2f-f4ff96d7e9f5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "451",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bd5766fc-7c32-4ffd-bb19-509b017d491e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "551",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7dcc0d09-0738-4e7e-a0c6-bd1417b8d6f3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "680",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1a76f3c4-4361-4c95-9c0d-b476ebd360f6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "681",
          "content": "$i : $a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "addc3142-9d56-49f2-9360-c0de69f512d2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "751",
          "content": "$a : $0 :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "4c15514c-539f-4311-8ef2-cdf44d6b424f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "781",
          "content": "$z : $z : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "8026ba55-58ef-434a-898e-e05fc35d8cda",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u : $x :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "a1e87f9b-eb21-45f1-bd15-09aaadaa6cd2",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00577",
        "status": "c",
        "type": "z",
        "undefined": "\\\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00253",
        "encoding": "n",
        "punctuation": "\\",
        "undefined1": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined2": "0"
      }
    }
  },
  {
    "module": "MARC_AUTHORITY_EDITOR",
    "id": "4a90d859-dd13-4cb1-858e-19765772108c",
    "title": "AUTHROTY-RDA-2015 - AUC-TEMP-CORPORATE-PORTAL",
    "description": "AUC-TEMP-CORPORATE-PORTAL",
    "content": {
      "fields": [
        {
          "tag": "001",
          "content": "",
          "isProtected": true,
          "id": "c0e99245-f5f8-44c5-872e-77a122566728",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "005",
          "content": "20250506062727.4",
          "isProtected": false,
          "id": "33566803-4872-442b-9c38-9df88d27ebff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Date Ent": "150301",
            "Geo Subd": "n",
            "Roman": "n",
            "Lang": "|",
            "Kind rec": "a",
            "Cat Rules": "z",
            "SH Sys": "z",
            "Series": "n",
            "Numb Series": "n",
            "Main use": "a",
            "Subj use": "a",
            "Series use": "b",
            "Type Subd": "n",
            "Undef_18": "\\\\\\\\\\\\\\\\\\\\",
            "Govt Ag": "\\",
            "RefEval": "a",
            "Undef_30": "\\",
            "RecUpd": "a",
            "Pers Name": "n",
            "Level Est": "d",
            "Undef_34": "\\\\\\\\",
            "Mod Rec Est": "|",
            "Source": "c"
          },
          "isProtected": false,
          "id": "b3240a6f-2e54-4278-b61c-263b2ad2528b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $f aucnm $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "007b2c2f-cb93-4d62-a984-57f49c8c6182",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "075",
          "content": "$a Ø§Ø³Ù ÙÙØ¦Ø© $b co $2 auce",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "52cff457-6eb5-407e-82ae-dbe164370e32",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "370",
          "content": "$e : $2 aucsh $h :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f755f7c2-7919-4c32-81e0-31456881074e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "371",
          "content": "$a : $b : $c : $d : $e : $m : $u : $z :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d850c4de-a6c1-4499-be65-e7bb22469acf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "372",
          "content": "$a : $2 aucsh",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "065854f8-a1a5-4b95-b82a-e08b5d4b26f6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "373",
          "content": "$a : $2 aucnm",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "67e36c64-4a10-4739-93db-f6973a6af41b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "377",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0044498e-e649-4656-ad0c-5bac90fc8f5b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "410",
          "content": "$a : $b :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "36e4b413-89f2-4ca4-8c77-ca94ca93857c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "510",
          "content": "$a : $b :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "5f6e5c31-bd73-49e6-b224-6073851ab093",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "670",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0c3c1606-7d5f-4065-90a5-6c8b0581b4fe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "678",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fecc105a-3b90-4f56-a167-abafafa1bd63",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$a : $b : $0 :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "43b7da42-ba93-4462-b71f-4d2d4d41b6fe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "3fd090a9-f73a-4643-8088-0b382a7b3e23",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00567",
        "status": "c",
        "type": "z",
        "undefined": "\\\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00229",
        "encoding": "n",
        "punctuation": "\\",
        "undefined1": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined2": "0"
      }
    }
  },
  {
    "module": "MARC_AUTHORITY_EDITOR",
    "id": "fb266708-43e3-4eb8-ad87-f29d2f6d47b9",
    "title": "AUTHROTY-RDA-2015 - AUC-TEMP-MEETING -PORTAL",
    "description": "AUC-TEMP-MEETING -PORTAL",
    "content": {
      "fields": [
        {
          "tag": "001",
          "content": "",
          "isProtected": true,
          "id": "c7485fed-ce60-4850-aa0f-bbe037b3a4cf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "005",
          "content": "20250506063040.9",
          "isProtected": false,
          "id": "a40d9f96-c113-4227-85e2-a3bdf9c268ff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Date Ent": "150301",
            "Geo Subd": "n",
            "Roman": "n",
            "Lang": "|",
            "Kind rec": "a",
            "Cat Rules": "z",
            "SH Sys": "z",
            "Series": "n",
            "Numb Series": "n",
            "Main use": "a",
            "Subj use": "a",
            "Series use": "b",
            "Type Subd": "n",
            "Undef_18": "\\\\\\\\\\\\\\\\\\\\",
            "Govt Ag": "\\",
            "RefEval": "a",
            "Undef_30": "\\",
            "RecUpd": "a",
            "Pers Name": "n",
            "Level Est": "d",
            "Undef_34": "\\\\\\\\",
            "Mod Rec Est": "|",
            "Source": "c"
          },
          "isProtected": false,
          "id": "01beb762-3ac4-4fd3-9a88-a2ebe3eb4cbf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $f aucnm $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5aaab090-900b-46c2-ba0b-24dc920f9ea0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "075",
          "content": "$a Ø§Ø³Ù ÙØ¤ØªÙØ± $b cn $2 auce",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ce5b99c0-a1fb-4658-9cda-c50de4398f84",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "370",
          "content": "$e : $2 aucsh $h :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3afabff9-579e-4d24-83f0-5f6990903c04",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "372",
          "content": "$a : $2 aucsh",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "eb97d7ff-85c3-4f36-b74f-50d7abb88710",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "373",
          "content": "$a : $2 aucnm",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "22f0b974-e62e-4601-a2cc-23bafd411bd8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "377",
          "content": "$a ara",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "172737bf-fa8e-446f-ae38-5ae9159ba191",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "411",
          "content": "$a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "3b814fca-6d32-4acd-b62c-98cfa96be956",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "411",
          "content": "$a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "fc482a49-0d26-49ad-ad07-f6cb646eb9b0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a : $c : $d :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "48711b14-27ea-4757-8d14-9a3b88f44286",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "670",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "143e7269-a5c5-44d6-8d42-483bf9484db0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "678",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4e0dae73-0cd9-42c9-bd1f-45275602205a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$a : $n : $d : $c : $0 :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "7dc3acac-d4ad-4fdb-a3a0-8c61c6b18685",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u : $x :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "d1fc666a-a370-4410-a1b3-d283fdc021a1",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00576",
        "status": "c",
        "type": "z",
        "undefined": "\\\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00229",
        "encoding": "n",
        "punctuation": "\\",
        "undefined1": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined2": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "3a840492-dc5b-4779-a87a-c616dc451116",
    "title": "Book",
    "description": null,
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505120526.2",
          "id": "3869ec81-c95b-404d-84e0-6213f500338b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "ELvl": "\\",
            "Desc": "a",
            "DtSt": "s",
            "Entered": "250505",
            "Srce": "d",
            "MRec": "\\",
            "Date2": "\\\\\\\\",
            "Ctry": "aku",
            "Lang": "ara",
            "Biog": "c",
            "Audn": "d",
            "Fest": "0",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Conf": "0",
            "Form": "\\",
            "GPub": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Indx": "0",
            "LitF": "0",
            "Date1": "\\\\\\\\"
          },
          "id": "ddefbbe7-3a10-49c4-a941-db1ec63ff186",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "014",
          "content": "$a0920",
          "id": "a75f0058-a6a7-4e52-992b-03cceb666253",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$aMOFA$bara$cSA-RiAUC",
          "id": "94ed7ed1-9a35-43ae-b691-3c43cbd43b09",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a$b$221",
          "id": "e6c0e190-7149-47b6-86cf-71ca7ce949ea",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a $d",
          "id": "6929ea87-ae88-497b-afb8-7feb2942877a",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "0"
          ]
        },
        {
          "tag": "245",
          "content": "$a: $b $c",
          "indicators": [
            "1",
            "0"
          ],
          "id": "983777be-7bbf-45f7-9483-9dd06958bada",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a",
          "id": "d9516ac1-9a99-4a13-957d-63d43645deb5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "260",
          "content": "$a $b $c",
          "id": "6ed91844-8e1c-4aa6-8471-bf6268420298",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a$b$c",
          "indicators": [
            "#",
            "#"
          ],
          "id": "f64e25ce-a158-4947-ba03-d4c891700fad",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ",
          "indicators": [
            "#",
            "#"
          ],
          "id": "b5ec5ed9-4c07-44a0-b10f-84e4a8bdaf3a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a$x$y$z$v$2aucsh",
          "id": "261a1c8b-3e4a-4668-a26a-62f1852168f8",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            null,
            "7"
          ]
        },
        {
          "tag": "650",
          "content": "$a$x$y$z$v$2aucsh",
          "id": "c394e5b6-01c7-457a-abb9-0adb3d06d07e",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            null,
            "7"
          ]
        },
        {
          "tag": "700",
          "content": "$a$q$d$e",
          "id": "3b62b370-cbcb-46d3-92bf-8c99facdad39",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "1"
          ]
        },
        {
          "tag": "856",
          "content": "$3$a$uhttp://10.0.0.90/Mofa7/$x$z",
          "id": "980b0083-0bdc-4716-8b77-a87a804a3932",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "4"
          ]
        },
        {
          "id": "e15fa3d4-b610-42e5-87cb-fedc4b7cf077",
          "tag": "910",
          "content": "$aOffsite-MOFA2-7",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "d4b88589-6b28-4c62-8f48-82b0a8b20d86",
          "tag": "949",
          "content": "$aMOFA$d$i$j$n$u",
          "indicators": [
            "\\",
            "\\"
          ]
        }
      ],
      "leader": {
        "length": "00000",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": " ",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00000",
        "encoding": " ",
        "form": "a",
        "resource": " ",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "cf747c1c-7f40-4056-b063-723ed8289ed8",
    "title": "DAMAM_BOOK",
    "description": "KAC-ARA-BOOKs-2015",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505120594.9",
          "id": "40247101-2a81-463d-a052-6b8068b66136",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "ELvl": "\\",
            "Desc": "a",
            "DtSt": "s",
            "Entered": "250505",
            "Srce": "d",
            "MRec": "\\",
            "Date2": "\\\\\\\\",
            "Ctry": "aku",
            "Lang": "ara",
            "Biog": "c",
            "Audn": "d",
            "Fest": "0",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Conf": "0",
            "Form": "\\",
            "GPub": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Indx": "0",
            "LitF": "0",
            "Date1": "\\\\\\\\"
          },
          "id": "cc07303c-6f0a-4bfa-8226-560500cc4e79",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "id": "a603d919-bc5b-476a-b683-dd17cfd4c351",
          "tag": "020",
          "content": "$a",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "fd3450ac-ad51-4447-a81f-4bf72b09bc7d",
          "tag": "024",
          "content": "$a",
          "indicators": [
            "0",
            "\\"
          ]
        },
        {
          "tag": "040",
          "content": "$aKAC$bara$cSA-RiAUC$erda",
          "id": "9ea902e3-784c-4478-a7d4-36e4d64f36a5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "id": "4416d53f-7871-4699-914b-6a464f1f8934",
          "tag": "041",
          "content": "$a",
          "indicators": [
            "1",
            "\\"
          ]
        },
        {
          "tag": "082",
          "content": "$a$221$qSA-RiAUC",
          "id": "5116aa2f-2505-4328-8028-7b20973f8b21",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "0",
            "4"
          ]
        },
        {
          "id": "87aa3a1d-aa3e-48c5-8626-43967cebafd0",
          "tag": "092",
          "content": "$a$223",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "b0703923-a310-47a9-9318-e2aeb302e9ba",
          "tag": "099",
          "content": "$a",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "tag": "100",
          "content": "$a$d$eÙØ¤ÙÙ.â",
          "id": "b84e8f21-c6ba-4dc5-9d83-1e72809f3af0",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "1"
          ]
        },
        {
          "tag": "245",
          "content": "$a: $b /$c.",
          "indicators": [
            "1",
            "0"
          ],
          "id": "202a24af-ec83-405b-879c-cf82cf1982b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a",
          "id": "0c0a5822-fad5-4354-aff8-4e7ffff1cfd5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a:$bØ$c$m.",
          "id": "b2af2d8f-4fb5-4d22-a110-7e59d7b51ab9",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "#",
            "1"
          ]
        },
        {
          "tag": "300",
          "content": "$aØµÙØ­Ø© :â$b Øâ$cØ³Ùâ",
          "indicators": [
            "#",
            "#"
          ],
          "id": "db48eb53-a58d-4d24-b4e6-4347a7d695bd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "id": "6825b100-93d6-49cc-bc60-9346ad54561e",
          "tag": "336",
          "content": "$aÙØµâ$btxt$2rdacontent$3ÙØªØ§Ø¨â",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "440bdfc8-888e-4b35-879d-85cac1b25620",
          "tag": "337",
          "content": "$aØ¨Ø¯ÙÙ ÙØ³ÙØ·â$bn$2rdamediaâ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "c216b66c-dd79-4b3e-8064-235ceaac1abd",
          "tag": "338",
          "content": "$aÙØ¬ÙØ¯â$bnc$2rdacarrierâ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "a2349757-db01-4037-ae30-7aef97bf4fa4",
          "tag": "490",
          "content": "$a",
          "indicators": [
            "0",
            "\\"
          ]
        },
        {
          "tag": "500",
          "content": "$a ",
          "indicators": [
            "#",
            "#"
          ],
          "id": "a4bc2647-5a40-4fcc-bf73-903c95c7ca69",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "id": "c1dff9cf-19c7-4da1-9c8b-43f9b05a2854",
          "tag": "504",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "58d6c385-fe47-43c9-9819-77e02825b29c",
          "tag": "505",
          "content": "$a ",
          "indicators": [
            "0",
            "\\"
          ]
        },
        {
          "id": "060a0701-25a6-4c0a-899c-ac45b8aee3cf",
          "tag": "520",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "f5568323-4284-4e3e-b6a3-84eb44f5ea81",
          "tag": "521",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "0a7efcfb-8566-4aa0-8473-8c33323dc942",
          "tag": "590",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "tag": "650",
          "content": "$a$x$y$z$v$2aucsh",
          "id": "77002338-be39-4d05-8721-e43764ad3ee3",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            null,
            "7"
          ]
        },
        {
          "tag": "650",
          "content": "$a$x$y$z$v$2aucsh",
          "id": "e9e86bfc-f360-4f56-a5f1-776aaed4ebb1",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            null,
            "7"
          ]
        },
        {
          "tag": "830",
          "content": "$a",
          "id": "f8c86bd2-a0ea-4c35-968b-d2c4d1f0ab65",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "1",
            "0"
          ]
        },
        {
          "tag": "856",
          "content": "$3Book Cover$qJPEG$uhttps://library.ithra.com/bc/0.jpeg$x$z>CLICK_TO_VIEW_BOOK_COVER>",
          "id": "c914ae8b-9183-44a2-a487-ea78df5fc783",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "4",
            "2"
          ]
        },
        {
          "id": "4853bc45-b621-4d6c-96b9-51ea8735c0b5",
          "tag": "856",
          "content": "$3Table of contents$qPDF$uhttps://library.ithra.com/pdf/.pdf$x$z>CLICK_TO_ACCESS_TOC>",
          "indicators": [
            "4",
            "2"
          ]
        },
        {
          "id": "9e696341-f9be-46a6-8f83-c53c2137c9e2",
          "tag": "949",
          "content": "$aKAC$d$i$j$n$u",
          "indicators": [
            "\\",
            "\\"
          ],
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "id": "001cbb91-9f0e-45f4-989a-20ec73638131",
          "tag": "956",
          "content": "$aÙØ´Ø±ÙØ¹ Ø£Ø±Ø§ÙÙÙ 2024-Ø§ÙØ¯ÙØ¹Ø©â$x",
          "indicators": [
            "\\",
            "\\"
          ],
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00000",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": " ",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00000",
        "encoding": " ",
        "form": "a",
        "resource": " ",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "699181be-9359-4b05-8dda-baa97e8cd0ad",
    "title": "AUC RDA Template",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505120594.9",
          "id": "40247101-2a81-463d-a052-6b8068b66136",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "ELvl": "\\",
            "Desc": "a",
            "DtSt": "s",
            "Entered": "250505",
            "Srce": "d",
            "MRec": "\\",
            "Date2": "\\\\\\\\",
            "Ctry": "aku",
            "Lang": "ara",
            "Biog": "c",
            "Audn": "d",
            "Fest": "0",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Conf": "0",
            "Form": "\\",
            "GPub": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Indx": "0",
            "LitF": "0",
            "Date1": "\\\\\\\\"
          },
          "id": "cc07303c-6f0a-4bfa-8226-560500cc4e79",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "id": "a603d919-bc5b-476a-b683-dd17cfd4c351",
          "tag": "020",
          "content": "$a",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "tag": "040",
          "content": "$aSA-RiAUC$bara$cSA-RiAUC$erda",
          "id": "9ea902e3-784c-4478-a7d4-36e4d64f36a5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a$221$qSA-RiAUC",
          "id": "5116aa2f-2505-4328-8028-7b20973f8b21",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "0",
            "#"
          ]
        },
        {
          "id": "87aa3a1d-aa3e-48c5-8626-43967cebafd0",
          "tag": "090",
          "content": "$a",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "tag": "100",
          "content": "$a$b$c$d$q$e",
          "id": "b84e8f21-c6ba-4dc5-9d83-1e72809f3af0",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "0"
          ]
        },
        {
          "tag": "245",
          "content": "$a: $b $c",
          "indicators": [
            "1",
            "0"
          ],
          "id": "202a24af-ec83-405b-879c-cf82cf1982b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a",
          "id": "0c0a5822-fad5-4354-aff8-4e7ffff1cfd5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a$b$c",
          "id": "b2af2d8f-4fb5-4d22-a110-7e59d7b51ab9",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "#",
            "1"
          ]
        },
        {
          "tag": "300",
          "content": "$aØµ.â$b$câ",
          "indicators": [
            "#",
            "#"
          ],
          "id": "db48eb53-a58d-4d24-b4e6-4347a7d695bd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "id": "6825b100-93d6-49cc-bc60-9346ad54561e",
          "tag": "336",
          "content": "$aÙØµâ$btxt$2rdacontent$3ÙØªØ§Ø¨â",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "440bdfc8-888e-4b35-879d-85cac1b25620",
          "tag": "337",
          "content": "$aØ¨Ø¯ÙÙ ÙØ³ÙØ·â$bn$2rdamediaâ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "c216b66c-dd79-4b3e-8064-235ceaac1abd",
          "tag": "338",
          "content": "$aÙØ¬ÙØ¯â$bnc$2rdacarrierâ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "a2349757-db01-4037-ae30-7aef97bf4fa4",
          "tag": "490",
          "content": "$a$x$v",
          "indicators": [
            "0",
            "\\"
          ]
        },
        {
          "tag": "500",
          "content": "$a ",
          "indicators": [
            "#",
            "#"
          ],
          "id": "a4bc2647-5a40-4fcc-bf73-903c95c7ca69",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "id": "c1dff9cf-19c7-4da1-9c8b-43f9b05a2854",
          "tag": "504",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "0a7efcfb-8566-4aa0-8473-8c33323dc942",
          "tag": "600",
          "content": "$a$d$x$2aucnm",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "3c6f0d3e-7e20-4005-9ccc-8e5c19fde4e4",
          "tag": "630",
          "content": "$a$2aucut",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "tag": "650",
          "content": "$a$x$y$z$v$2aucsh",
          "id": "77002338-be39-4d05-8721-e43764ad3ee3",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            null,
            "7"
          ]
        },
        {
          "tag": "650",
          "content": "$a$x$y$z$v$2aucsh",
          "id": "e9e86bfc-f360-4f56-a5f1-776aaed4ebb1",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            null,
            "7"
          ]
        },
        {
          "id": "b5a0d9f9-a91b-4868-b494-cad3a4d011c3",
          "tag": "650",
          "content": "$a$x$y$z$v$2aucsh",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "14b202d8-a5e4-4a4b-82d5-d886a8774a21",
          "tag": "651",
          "content": "$a$x$2aucsh",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "id": "1cdb17ec-c1a2-40ff-bcb2-efb1bc824145",
          "tag": "700",
          "content": "$a$b$c$q$d$t$e$i",
          "indicators": [
            "\\",
            "\\"
          ]
        },
        {
          "tag": "830",
          "content": "$a$p$n$v$x",
          "id": "f8c86bd2-a0ea-4c35-968b-d2c4d1f0ab65",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "1",
            "0"
          ]
        },
        {
          "tag": "888",
          "content": "$a",
          "id": "c914ae8b-9183-44a2-a487-ea78df5fc783",
          "_isDeleted": false,
          "_isLinked": false,
          "indicators": [
            "4",
            "2"
          ]
        }
      ],
      "leader": {
        "length": "00000",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": " ",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00000",
        "encoding": " ",
        "form": "a",
        "resource": " ",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "8f63ef12-ec04-41f4-af2c-13103f16d189",
    "title": "DSPACE_TYPE_ÙÙØ§ÙØ§Øª",
    "description": "DSPACE_TYPE_ÙÙØ§ÙØ§Øª",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.3",
          "isProtected": false,
          "id": "11992d6a-ffe5-4170-919c-1899413ae210",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367699",
          "isProtected": false,
          "id": "acc7d64a-e4f8-4c2c-8501-24dfe7337a01",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "39b06836-c040-4228-aff7-4c906fc0dfb0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "70ba1dfe-ba7f-48b6-945f-3cae182999dc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a ÙÙØ§ÙØ§Øªâªâªâªâª $c 3b1a7968-0e79-4179-b139-aac4e7ad0a10",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ee0b3a7d-f728-4ea2-9a5e-2dc46e7c312c",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00334",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "ce0c9ac2-802c-4b74-8eb2-11f7119830b1",
    "title": "DAMAM_BOOK",
    "description": "KAC-ARA-BOOKs-2015",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "f13a5b6b-a39c-434d-acaa-9df9a453ea55",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "4890542",
          "isProtected": false,
          "id": "c030ffd3-a447-4583-b30f-eb7c7bbd3314",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "c",
            "BLvl": "m",
            "Entered": "150209",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "eng",
            "MRec": "\\",
            "Srce": "c",
            "Comp": "||",
            "FMus": "l",
            "Part": "\\",
            "Audn": "\\",
            "Form": "\\",
            "AccM": [
              "\\",
              "\\",
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "LTxt": [
              "n",
              "\\"
            ],
            "TrAr": "n"
          },
          "isProtected": false,
          "id": "9bf5ffeb-3c49-4ce2-87cb-7ae8baae085b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "17939eb9-7e7f-4747-aed4-cc6ff10dbaca",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "028",
          "content": "$a :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "798a6874-790c-4287-8596-82ed762227e8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a KAC $b eng",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a13b3be4-da85-4694-9f5a-b207f2ea5c7e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "092",
          "content": "$a : $2 23",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4c3547f3-9dec-4315-aa97-3436b9cba539",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "21a311e0-5e29-498e-856a-0462db57619b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $h [music] : $b / $c .",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "2eee05a3-e13b-487d-b7a0-c0db8bfb93e1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "254",
          "content": "$a Score.",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bc112b60-412e-491f-ba41-897096f7bcc7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "260",
          "content": "$a : $b , $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d9c5abba-e5cc-4fb9-8be8-de6d6acfdeab",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a 1 score (p) ; $c cm.",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7e6dd6e2-8e71-44f9-a265-6591d5e71120",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v Scores",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "8847d154-000c-4b89-ac71-019a40c6be13",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a KAC",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "926e291c-1d4c-41c8-b5b6-b628f8d3d17c",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00521",
        "status": "c",
        "type": "c",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00217",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "1475b58c-0942-4c97-8565-761364888a80",
    "title": "AUC RDA Template - AUC-VIEDO-RDA",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "dbf0a26e-d1d4-433f-92ed-9d398ce2ae76",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5166192",
          "isProtected": false,
          "id": "abb5f56c-3800-46dd-aaa7-289c5fa15750",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Videorecording",
            "Category": "v",
            "SMD": "z",
            "Color": "c",
            "Videorecording format": "u",
            "Sound on medium or separate": "a",
            "Medium for sound": "u",
            "Dimensions": "|",
            "Configuration of playback channels": "u"
          },
          "isProtected": false,
          "id": "284bb602-04f9-4d73-8e8d-9e6533a25a4a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "g",
            "BLvl": "m",
            "Entered": "141021",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "xx\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Time": [
              "0",
              "4",
              "8"
            ],
            "Audn": "g",
            "GPub": "\\",
            "Form": "o",
            "TMat": "v",
            "Tech": "l"
          },
          "isProtected": false,
          "id": "294a7810-603c-4708-b9ef-1f9884d4ea86",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "033",
          "content": "$a : $p :",
          "indicators": [
            "0",
            "1"
          ],
          "isProtected": false,
          "id": "2abecf43-9816-487b-bbf1-40760916bff9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "faa59b41-a39b-4831-ad68-a3b0f21d997f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "1b4c5861-c058-4531-a4d2-44dc949d0597",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $b : $c : $d : $q : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "1e4968ad-4f9a-4b25-bc71-8b772659d0d9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a6f4c021-0f76-4fdb-8cad-40de12b48078",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "bde1db9c-8bcb-4c25-9f82-c205564d65b4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "257",
          "content": "$a .",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8f481e21-e71a-45ba-9edf-7164ad2aa300",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a [ÙÙØ§Ù Ø§ÙÙØ´Ø± ØºÙØ± ÙØ­Ø¯Ø¯] :âªâªâªâª $b ÙØ­ÙØ¯ Ø±Ø¶Ø§ ÙØµØ± Ø§ÙÙÙØâªâªâªâª $c : $m :",
          "indicators": [
            "#",
            "1"
          ],
          "isProtected": false,
          "id": "9c114bbd-8865-4c02-beff-25f5b74e1464",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a 1 ÙÙØ±Ø¯ Ø¹ÙÙ Ø§ÙØ®Ø· Ø§ÙÙØ¨Ø§Ø´Ø± (1 ÙÙÙ ÙÙØ¯ÙÙ(1 Ø³Ø§Ø¹Ø©Ø 23 Ø¯Ù)) :âªâªâªâª $b ÙØ§Ø·ÙØ ÙÙÙÙâªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "670dc245-1e8d-468a-842a-2bc3ebd1c007",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "306",
          "content": "$a 012300",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7838b054-719e-4b5e-bf3d-ee46379d086e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ØµÙØ±Ø©  ÙØªØ­Ø±ÙØ© Ø«ÙØ§Ø¦ÙØ© Ø§ÙØ£Ø¨Ø¹Ø§Ø¯âªâªâªâª $b tdi $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f6ec449d-ce95-4ba3-98ba-083c43d5519f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a ÙÙØ¨ÙÙØªØ±âªâªâªâª $b c $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "081a1856-0bc1-4d42-b388-243e53ecb184",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙÙØ±Ø¯ Ø¹ÙÙ Ø§ÙØ®Ø· Ø§ÙÙØ¨Ø§Ø´Ø±âªâªâªâª $b cr  $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "aecae23b-3bb9-404f-846b-05b941d32021",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$a Ø±ÙÙÙâªâªâªâª $2 rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4da58dac-3322-49e8-a2ee-bc38ca9f7300",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a ÙÙÙ ÙÙØ¯ÙÙâªâªâªâª $2 rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "af14fb9c-1ed3-4500-a110-7b3c4c492b58",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a Ø¥ÙØªØ§Ø¬ : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "75e6a35a-35a9-45f8-a9c7-6a63e1d20067",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "4afbe197-29af-4b24-9a59-7c271ec173fc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "518",
          "content": "$d :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8770a54a-6ba9-4673-a2f9-3ee01089d744",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a Ø·Ø±ÙÙØ© Ø§ÙÙØµÙÙ : Ø´Ø¨ÙØ© Ø§ÙØ¥ÙØªØ±ÙØª.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "32c96220-4b85-49bd-acd4-e565987c806f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a ØªØ§Ø±ÙØ® Ø§ÙØ§Ø·ÙØ§Ø¹ : 4 / 7 / 2019.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bb23c574-5a06-4e69-9296-3031a5f72954",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$v ÙÙØ§Ø¨ÙØ§Øªâªâªâªâª $v ÙØ³Ø§Ø¦Ù Ø³ÙØ¹ÙØ© Ø¨ØµØ±ÙØ©âªâªâªâª $2 aucnm",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "fad540e2-645f-476a-8f14-46081b5a3663",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a Ø§ÙÙÙØ§Ø¨ÙØ§Øª Ø§ÙØªÙÙÙØ²ÙÙÙÙØ©âªâªâªâª $v ÙØ³Ø§Ø¦Ù Ø³ÙØ¹ÙØ© Ø¨ØµØ±ÙØ©âªâªâªâª $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "f73250ae-6bc6-475c-b1bf-8e481de91c55",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a Ø§ÙÙØ³Ø§Ø¦Ù Ø§ÙØ³ÙØ¹ÙØ© ÙØ§ÙØ¨ØµØ±ÙØ©âªâªâªâª $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "72c5dc93-2b10-40d7-879a-69237476a83f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$a : $b : $c : $q : $d : $t : $e :",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "33fe0748-8e8a-40c2-a72e-62300527e250",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "218a7dcc-8911-4b2d-8e26-7b46146529ad",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "d41d2609-2991-4bd4-b0e0-b857a2a02891",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01307",
        "status": "c",
        "type": "g",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00409",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "fa4ecd54-968b-4b84-be15-6bed6b5dbde8",
    "title": "DSPACE_SUBJECT_Ø£Ø¯Ø¨ Ø¹Ø±Ø¨Ù",
    "description": "DSPACE_SUBJECT_Ø£Ø¯Ø¨ Ø¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "67af78e4-4114-426a-bb52-245ff9f15356",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367705",
          "isProtected": false,
          "id": "ad5d086a-2f29-471d-9e48-d2cc5a440eda",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "89b8d4fa-98ee-40f0-8f59-040908d969b7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ad847470-dc62-4dd7-a9a0-34b52101a38e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø£Ø¯Ø¨ Ø¹Ø±Ø¨Ùâªâªâªâª $c d3f4aed9-2113-400a-ba76-66d3d2ff6743",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "32cbc01a-c123-4d70-93d8-2929f662703e",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00336",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "ac07a2ac-72ee-41e5-88c5-b737d4fb6e0b",
    "title": "DAMAM_BOOK - KAC-ENG-SOUND",
    "description": "KAC-ARA-BOOKs-2015",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "3f97eafa-482f-41b8-ac21-bd2f56acd75d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "4986594",
          "isProtected": false,
          "id": "cd10a917-786f-44ef-b344-eeab9c8732cb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Sound recording",
            "Category": "s",
            "SMD": "d",
            "Speed": "u",
            "Configuration of playback channels": "u",
            "Groove width/ groove pitch": "u",
            "Dimensions": "g",
            "Tape width": "n",
            "Tape configuration": "n",
            "Kind of disc, cylinder, or tape": "m",
            "Kind of material": "m",
            "Kind of cutting": "u",
            "Special playback characteristics": "e",
            "Capture and storage technique": "d"
          },
          "isProtected": false,
          "id": "de112c10-4685-4bdf-8f57-3bcc3ca85135",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "j",
            "BLvl": "m",
            "Entered": "150209",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "eng",
            "MRec": "\\",
            "Srce": "c",
            "Comp": "||",
            "FMus": "n",
            "Part": "\\",
            "Audn": "\\",
            "Form": "s",
            "AccM": [
              "\\",
              "\\",
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "LTxt": [
              "n",
              "\\"
            ],
            "TrAr": "u"
          },
          "isProtected": false,
          "id": "ddd18bb2-3307-40f5-b3e8-1aac652396ac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "9a99d674-acfe-4270-853c-5e576ac7b828",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "028",
          "content": "$a :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "de9aa4af-00cc-4361-bf43-90e85714fd8c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a KAC $b eng",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f40e3028-9d62-4a44-9f59-fa769a0e6150",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "296b13c2-bf11-4d8b-8c7b-3bd058ca16e1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "092",
          "content": "$a : $2 23",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "993b75c3-8317-455a-aa05-c0fc5772d9de",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "098",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fb458e1e-2ec5-4da9-9821-e5d6a7225c52",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "8417fbc2-0518-4f7f-bddf-1445e439677e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $h [sound recording] : $b / $c .",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "f0cd5ca3-9e2a-4f3f-ab74-9bfec92c6a2b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "260",
          "content": "$a : $b , $c .",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b685c0f1-276d-49bf-9ddb-6eeb7b77e48a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a sound disc () : $b digital ; $c 4 3/4 in.",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1bb8eb2b-c750-47f3-9468-bbebf3308f8b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "306",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "02970ff1-0ec0-4e9c-bba6-878870a0e8dd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "2aedc41b-59b5-4ba5-9832-9d8f6c9bb0e5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a08e9b4f-0b11-4991-bcfc-629b566749a0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "121ea180-b391-4d48-a3d0-4aa46fd7dae1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "82e3149d-3f3b-4632-802b-1baaa0fdda15",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c17e2e73-dea5-4c5e-a69a-820acf61d489",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "e5117b0c-0f7d-4bdb-a49d-80e9fc50da00",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "ffae3448-015f-4894-8970-2f604f64b9b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a KAC",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "680b90b4-4f70-43b6-b7c4-5ffba9ba1aff",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00711",
        "status": "c",
        "type": "j",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00325",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "76216871-11f6-4f45-b928-56c2d05ca3b2",
    "title": "AUC -RDA-BOOKS",
    "description": "MBRL_RDA_BOOK-MODFIY",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.9",
          "isProtected": false,
          "id": "2e82cfff-4faa-4076-8a94-fafb8959b624",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5944690",
          "isProtected": false,
          "id": "b9099e41-9c4e-4dbe-a814-e7c6d6b963e5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "g\\\\\\\\\\",
            "DtSt": "\\",
            "Date1": "000\\",
            "Date2": "0\\ar",
            "Ctry": "a\\c",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "c4efcfb1-3657-4fc6-8937-e37b476bf3a7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1a0b55a8-7e03-444f-b973-1ab44249b002",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "93f992b7-3f91-4a37-84f5-d77aa93ddf21",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "3275f955-7be6-419b-9f96-cbf334770718",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b / $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "1f8a2284-82e3-4f2c-8d76-de08247a34cd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8076a4f5-1e86-4823-b4c2-1e45740471ad",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a  : $b Ø $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "f0d67680-d16d-4c3a-b24b-b7b9beb98e47",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ØµÙØ­Ø© :âªâªâªâª $b Øâªâªâªâª $c Ø³Ùâªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "695ce67a-22f5-428a-8b31-efd24fc742fc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 ÙØªØ§Ø¨âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "68a445bf-5abd-4a93-9136-152a40af2441",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9c179083-37bf-4afc-8148-24cd9c871a5f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "51bb5ad1-e475-4e3d-9539-23d23929f75e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4c55db4a-7d5d-4161-9abe-e204f147970b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "25d816a4-14cb-4c9a-88ba-3d311edb0312",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "ade519f8-2912-4cb4-973e-6f464237b018",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "988",
          "content": "$a Publisher $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "368b1179-7b08-44c8-9449-fccbdfca0773",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00711",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00253",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "0d347703-3389-4e58-8ad3-84265aa2eaf6",
    "title": "AUC Books Constant Template - AUC-TEMP-THESES-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.1",
          "isProtected": false,
          "id": "90c1573b-c59f-4b14-88b3-7d1bccfa4e7e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6101337",
          "isProtected": false,
          "id": "bc7cac46-2ecd-493a-8b5e-df977a82acde",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "t",
            "BLvl": "m",
            "Entered": "f\\bm\\\\",
            "DtSt": "\\",
            "Date1": "000\\",
            "Date2": "0\\ar",
            "Ctry": "a\\c",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "dd4da401-4b27-40ef-b92b-d7c46b4920c4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3adcade6-9394-499e-b5ce-71038c32ead3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b9d5e4b7-3bc6-49ff-93ef-58297dd53adf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "73210fcd-aa33-4019-b09f-2d154ecfb71b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5d28b571-84d3-42f7-b904-7184d2bcfae5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "b5bcad84-f98f-4625-9a3b-b292a5ce9a0d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "1fdc4498-78cd-4545-a30f-e73aea6a21b6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "1405888c-c467-4717-b6ed-2e1653d7180b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$c : $m :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "d55e7c43-ae75-4d64-8c93-6b4c12e08d2c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e75c7bf1-6cb2-44ca-8a16-8650f529ab0f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 Ø£Ø·Ø±ÙØ­Ø©âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "25c34447-5419-40fa-b798-1d80412fcc56",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "62300382-0ea3-4ba5-8735-9161825aa67b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8a3d1d7f-27e4-447b-9abe-2fa8abecdbff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a Ø¥Ø´Ø±Ø§Ù : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a505302e-35ea-4dcf-a6a0-9d34f05dbfe9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙÙØ§Ø­Ù :  âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3f973d0a-c82f-420b-8312-9f13109c5614",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "502",
          "content": "$b : $c : $d :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "45d932c5-249c-40f7-8319-a521e9cee0d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a Ø¨Ø¨ÙÙÙØ¬Ø±Ø§ÙÙØ© :  âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6c38e2eb-000d-4a65-9f00-c7a288312241",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "506",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "1d9b886f-a0c8-47e2-a028-79833bf44fcf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "520",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "65eabc60-972e-488d-923d-0a69b8e382f5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "530",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f7eecd4b-62bb-48f3-8a9d-c1e1a2399ce2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c276e335-c11d-496e-80a3-74f575bf964a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "19f3be47-3dc6-4a55-ba50-27eeb191312d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "041b109b-b4b5-44b7-a7b5-f07a2fc4820e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "f0932520-423f-4740-867e-6556cfc58581",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "6a3352f0-1e09-4c0e-9be4-b311e33baf5d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "3fe75080-20a2-4818-8729-633a27caf1d2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "fb7d4bb8-a089-4c55-a19f-3391a7ed7c4b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "24580318-ec86-47a5-ba89-57cffd476441",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01035",
        "status": "n",
        "type": "t",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00409",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "0bc3b0b7-fb8f-40bf-b494-6aa8f800610f",
    "title": "DSPACE_SUBJECT_ÙØ¹Ø§Ø±Ù Ø¹Ø§ÙØ©",
    "description": "DSPACE_SUBJECT_ÙØ¹Ø§Ø±Ù Ø¹Ø§ÙØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.3",
          "isProtected": false,
          "id": "acc051b1-d494-4d23-85ee-7a5606570228",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367721",
          "isProtected": false,
          "id": "abd65b31-eab0-49b3-894d-c6f82987813e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "40a40738-3d8b-4773-b3be-2f97052cab75",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1e473d52-1b46-40fd-9aaa-276d0386b0f2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a ÙØ¹Ø§Ø±Ù Ø¹Ø§ÙØ©âªâªâªâª $c c19670d2-fb3a-4ef5-8254-f81211c0d29f",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6135389e-d752-46cd-841d-1149e2c0367f",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00338",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "3042c55f-4d33-44e4-b78c-d14e294758ff",
    "title": "AUC RDA Template - AUC-PDF-RDA",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "563ea215-c7e7-426f-8a4d-c8ba894151a8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5166594",
          "isProtected": false,
          "id": "6eae2a97-78f1-4e6d-8eb5-b2f6a7d89bdc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Electronic resource",
            "Category": "c",
            "SMD": "r",
            "Color": "c",
            "Dimensions": "n",
            "Sound": "\\",
            "Image bit depth": "\\\\\\",
            "File formats": "|",
            "Quality assurance target(s)": "|",
            "Antecedent/ Source": "|",
            "Level of compression": "|",
            "Reformatting quality": "|"
          },
          "isProtected": false,
          "id": "caf8c6ab-6f99-403e-ba82-1a2e70fe4896",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "141021",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "g",
            "Form": "o",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "f",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "4daf6f26-fa3a-4463-bf5e-2aa349d2bd9c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "079b267f-f66e-489b-b068-4dfa83c88046",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "f9f3391b-dcfe-40a6-a5fc-cf36fd902c90",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $b : $c : $d : $q : $e :",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "0517b11c-1768-4bdf-b673-1a1ec1db4e59",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "728584d9-464d-4195-881b-ed275f5ca3c6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "#",
            "1"
          ],
          "isProtected": false,
          "id": "bd408f6a-408f-4c32-a4d4-db3ece0972a6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a 1 ÙÙØ±Ø¯ Ø¹ÙÙ Ø§ÙØ®Ø· Ø§ÙÙØ¨Ø§Ø´Ø± (ÙØ±ÙØ©) :âªâªâªâª $b Ø¥ÙØ¶Ø§Ø­ÙØ§ØªØ ÙÙÙÙâªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "50d47131-f03d-453f-9cbc-018b0cd4595b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt  $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7e21ada6-9c84-473e-80b5-923d44e56d48",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a ÙÙØ¨ÙÙØªØ±âªâªâªâª $b c $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a0372a3f-4c82-48b4-bffb-d9efe94e4132",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙÙØ±Ø¯ Ø¹ÙÙ Ø§ÙØ®Ø· Ø§ÙÙØ¨Ø§Ø´Ø±âªâªâªâª $b cr  $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7fe1d1f6-47b0-4810-8ede-90ea7b5a990f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a ÙÙÙ ÙØµÙâªâªâªâª $2 rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cc641d75-283d-4ed5-b038-e12d4069c015",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$b Ø¨Ù Ø¯Ù Ø£Ùâªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e4ad1a15-fc05-4f23-a44e-a841a264eefd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ØªØ§Ø±ÙØ® Ø§ÙØ§Ø·ÙØ§Ø¹ :âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a3cd8acd-1657-4074-a1a3-ab05bd6e50c5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ec7dbaee-422f-47d3-b0ee-0a10929bce99",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$a : $b : $c : $q : $d : $t : $e : $i :",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "a388c523-b77f-472c-98bc-45b9fb42f2e4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u : $x ØªØ§Ø±ÙØ® Ø§ÙØ§Ø·ÙØ§Ø¹ : âªâªâªâª",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "e223989b-9b23-4b2d-805e-cb9e8011ca47",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00861",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00277",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "5310b733-933d-4559-9195-569588ffbdde",
    "title": "DSPACE_SUBJECT_ÙØ§ÙÙÙ",
    "description": "DSPACE_SUBJECT_ÙØ§ÙÙÙ",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.7",
          "isProtected": false,
          "id": "ea8fdefa-2498-42c6-91ba-fbe526c74c8f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367717",
          "isProtected": false,
          "id": "a5b8ec60-f4fa-4c42-8e7e-ec10ed24a101",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "d4150444-54d5-4627-ad64-65f1b634e29e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ab351c48-d0a9-4782-8154-50a394ff4650",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a ÙØ§ÙÙÙâªâªâªâª $c fb987fbc-ba39-43bf-a5ed-1c2367474962",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3c5c84de-9f7d-41ed-bc76-21d67218d49f",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00333",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "11c82f45-6b90-49ee-b043-33896c4b8cab",
    "title": "AUC Books Constant Template - BRAILLE-BOOKS RDA MBRL ARA",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "fd6f8583-6d59-4a29-af33-3cb562ad132e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6392211",
          "isProtected": false,
          "id": "91fb70c0-6324-4d0e-9704-3a1dcb42e419",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "210405",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "f",
            "Form": "f",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "2d1b7d20-cb78-44fc-aab4-cd095d3984dc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "64f8be43-5ec4-4730-a697-0fd190675feb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "48c1297f-ac1c-47f0-b67f-48cf7020a532",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5560ba64-17b6-45b6-ade2-8b0453b5416c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2f4e2589-421f-4b08-955c-83d9ff7b627f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "c44d44f2-d562-4a13-9efd-b31efdd3ef9e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "864ffd9c-6967-4ce6-8f47-bbd385395cd6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "625cf718-5af3-4809-bc51-26c1cfae9559",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "9ae7d566-1d60-49ec-850f-c99d3db1f5f1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "e54219fa-b4e3-433e-8ee4-dd1f23d0cc3b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "78fe2ec0-04ab-4f64-b076-eebfa08deedb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "04852f7c-d99d-424f-b6b3-73c3331b7fa0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "348ae0e0-ce36-45b8-be9d-23924b6d1e75",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµ ÙÙØ³Ùâª $b tct $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7fcbf416-cedc-4fc3-89fa-e70dbce0404f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4fbb887f-f297-4547-9593-c50a558fefda",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "408883f9-8a76-40be-9a10-8c515d170a45",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "341",
          "content": "$a ÙÙØ³Ùâª $e Ø¨Ø±Ø§ÙÙâª $2 w3c",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f8f9285f-2452-4c6a-8228-06d1af6b3e12",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "715d678b-07db-4706-83d3-9057d8e964d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "502e888f-6321-4c39-927d-852f60f39bb2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "069150ee-40c8-4886-bcef-cc165d45d2bb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "4f2d272f-6536-47a5-a835-3128215d893a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "ab8ed370-3520-48cb-8919-1713e536f072",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "b984872a-a16e-4383-903c-18004045e3f9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a ÙØªØ¨ Ø§ÙÙÙÙÙÙÙÙâª $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "049c9ab3-5f4d-4921-ace4-e19cf83d4b35",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "7099d330-d3bb-4b5c-b064-9e0088584692",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "7f57a608-18c3-4016-8ebc-b8581dfea646",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00977",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00385",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "87464543-1d1a-4f9d-997c-7219a5af9937",
    "title": "AUC Books Constant Template - MOC HERITAGE-ENG",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "4a1db1c7-b547-4868-b184-7535788d683d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "7096952",
          "isProtected": false,
          "id": "20f5742e-6a97-4af5-9c31-7145ee2800be",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "240415",
            "DtSt": "\\",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "eng",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "g",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "5fc7219b-a81a-4f51-b46b-4fdffd4b728d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "63e85c6b-3881-497a-906f-1e31d2edbc52",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "38ac9dc5-fb8f-4840-9e77-c722f061409b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiMOC $b eng $c SA-RiMOC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "25b456e3-bb96-45fd-9867-6179307fbe1f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "02608bf9-189d-4a75-af5e-5e137d8246f1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $b : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "6752794a-34de-4ad8-b3d6-49e7b6ea9f80",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "809aae15-49e2-46d0-bd0f-f0eec2dc0ac5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "7e53f81c-56b0-422e-9361-81166ee58109",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "01c89ce4-5bba-49d5-9743-5ab370db0590",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "5ac2a58f-2a8e-4c4f-b536-304b8e013a95",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "933d85dd-2696-4839-bb45-318c0eca107b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a text $b txt $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "507582a9-a8ed-4e8c-a3aa-d922a23e9498",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "524882b2-ddea-44ce-b412-388be30112c4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a volume $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0c52d8ff-4ff1-402a-a75d-f42b3d47649a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "401c7440-87b5-48d0-aa20-df126668897e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1ccf261b-0e2f-4e56-aae0-77fdb5a23c2a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fe31d9a2-99e5-401a-983a-4966eab1f2f7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "0596c4ae-c39c-4cf4-85a5-f5a923ba06e3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "a58d9586-fa18-4821-b952-6439be2247ad",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "16f6a3b2-34ce-4e4d-804a-a1c73b8b9b77",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "f0c2e9a5-a1f1-44fa-82d9-9e6cf446bbae",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a MOC Heritage1-BATCH 15 $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b4a693eb-4656-4f96-ae39-fd3f8c4a11e2",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00829",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00337",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "28ccfe48-fd6b-4289-8053-e3909ad9828e",
    "title": "AUC Books Constant Template - AUC-TEMP-PICTURE-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.6",
          "isProtected": false,
          "id": "cffa476e-23d5-44af-9c55-24f03102fd83",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6105412",
          "isProtected": false,
          "id": "76f121fe-89a3-4b01-811e-2a729d4d3326",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Nonprojected graphic",
            "Category": "k"
          },
          "isProtected": false,
          "id": "3d4a2392-8ad8-41a9-b3c9-2304adbea936",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "k",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Time": [
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "GPub": "\\",
            "Form": "\\",
            "TMat": "\\",
            "Tech": "\\"
          },
          "isProtected": false,
          "id": "eca02a1a-2ba4-4bee-b80e-a0ba1c5c749b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "dd3a6d8b-9b7f-4261-b7cf-37c6ce05b503",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8af2a4ca-feed-49d1-859f-0602629704ca",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "530a2ecc-1bf1-4d97-a68c-001e12b66ee1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "71a0025f-5a36-444f-8d30-9f13a8bd847c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2245b655-e85a-4422-b335-b71a02416209",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "e74c351a-81d2-4b0a-9b18-e23a0ec8c375",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "7c9cbe2e-6768-4f28-b548-cfd0c34dad8d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "75f2a2c0-7e17-441a-b1a2-a5febdcac5f1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "b7895989-2cf1-4a69-ac5c-5f964f9105b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0fb3c2ca-c4dd-4e29-b20b-9ed5c0345026",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a : $b : $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9a20309b-5539-4f59-8f75-019a106d3e44",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a : $b : $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cb2eba89-2f14-4389-a78c-51b2b9207692",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a : $b : $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "141c7cda-5e88-42aa-a0fd-0512e2fd2b37",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$a : $c : $d : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "df5e204a-512b-41b8-8882-cb4446d098b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "110208a6-1ce3-4444-90a4-5ba9017b9996",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "42dfe7eb-c426-4af3-81d9-92f7dfcfd6e3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "70638b0f-1629-4fb1-93c9-c682c2421e35",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "5cd05c3f-bbb8-4546-86f4-0e26ae2a9173",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "11d759a9-969b-4449-875f-26f2c02ede29",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "7e062d4a-bdaa-4531-b7b5-d7b406b1e846",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "454f9027-3119-49d1-a423-ae1b7d32529d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "16479ab7-6683-4c2c-b6c9-f2dc362ef6fe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "f0001d7a-f35b-47e7-b2f8-00ed5f679a70",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "332e2e66-9196-4d9d-9601-eee807576fff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "c410496b-ee7e-4c55-8e46-3bc87f7726e3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5905896e-170c-44b7-ba4f-ad6dc15b9bbd",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00990",
        "status": "n",
        "type": "k",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00409",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "6a0fc7e6-2ff0-4138-9f2d-f397e5e73a58",
    "title": "AUC Books Constant Template - MBRL-MAPS-ENG",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115713.2",
          "isProtected": false,
          "id": "cebf8316-81de-42d5-90dc-8765b71725b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6836193",
          "isProtected": false,
          "id": "35bb9f7e-2e71-4998-8bd1-ef3a4dc683df",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Map",
            "Category": "a",
            "SMD": "j",
            "Color": "c",
            "Physical medium": "a",
            "Type of reproduction": "u",
            "Production/reproduction details": "u",
            "Positive/negative aspect": "|"
          },
          "isProtected": false,
          "id": "18bec2cf-2db9-4bba-ac8e-3f6f07dd998c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "e",
            "BLvl": "m",
            "Entered": "a\\\\\\\\0",
            "DtSt": "0",
            "Date1": "\\\\\\e",
            "Date2": "ng\\c",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Relf": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Proj": "\\\\",
            "CrTp": "\\",
            "GPub": "\\",
            "Form": "\\",
            "Indx": "\\",
            "SpFm": [
              "\\",
              "\\"
            ]
          },
          "isProtected": false,
          "id": "6c02a088-317c-4f51-bcb0-e95914cb4555",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ca052675-4be6-4a4b-bb03-0b3d0660e83d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "034",
          "content": "$a a",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "40e0cf62-a671-45d0-95b2-2e5054f4cd8e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "072727da-cadb-42a8-8451-1ac929406c65",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "78cb40a3-d785-422b-81fb-411e3aa6a51e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "f888a917-cfef-4506-ae41-9aa70f30d2b6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $e cartographer.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "70ea1bc4-3739-471b-bf8f-adf481a7a0b1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "9f79ae9a-cf73-4f09-9e88-241e5d77d3cb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "37aafd1f-2fb0-4ad3-bde4-bb72c3028eee",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b8132017-0772-431f-882b-962b688368a0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "255",
          "content": "$a Scale ",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e1ba0c72-5b5d-4f85-8999-ee274f6f9ab2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "254d308d-243f-4b9b-96fa-d91045ddc37f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a 1 map : $b color ; $c cm, folded to  cm",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "02d836f5-024c-43db-b2a0-cd051881316d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a cartographic image $b cri $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e6cdef7c-37ad-4dee-a175-c90e79aa4017",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c92c0891-b376-4bfb-8ad7-9a47f3c25d44",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a sheet $b nb $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cb5ad1cd-047b-4ca8-a7dc-556577806269",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "8293cfea-4272-4ec4-afa5-0cdc4e8dd8bb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0d0f93a3-b054-4096-80d9-2605ef355e3c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "0918d08c-8102-4c37-b548-de08344dac3f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "c8258e25-0332-4d70-bf07-a2e03b80e1e5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "07c06801-2a81-4428-8707-b8adfae130ec",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "26ba7cf7-85e9-4fa2-9686-bd661684d3aa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "17f0e38a-355b-4ef7-8183-b1b01ef31a8f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a : $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "44365a83-475d-4b25-920c-28a4d7faa1e6",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00913",
        "status": "c",
        "type": "e",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00373",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "bb4f6d8a-f3e0-4531-b6b5-531fd81096df",
    "title": "AUC Books Constant Template - BRAILLE-BOOKS RDA MBRL ENG",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "b907d203-d734-4f52-9171-2cc1e1646387",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6392257",
          "isProtected": false,
          "id": "90f77981-1e82-4c95-af4c-41a91c92f4a0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "210405",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "eng",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "f",
            "Form": "f",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "5ebaf4f7-f36e-4889-a7c9-e50e4f8656d6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e4d45d1b-e5be-4b6e-bf1b-b76a600d7d41",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "7b9b50af-1099-4fd4-ad78-00fced3b97e9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6a2d2d5d-f08e-4834-afe9-fbf232967a2b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "dc5fe577-1c04-4ceb-a149-e278eedad395",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "6ed4d0ff-69f0-457b-bd8e-02771ac730c7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "8cb07fa6-c851-407d-8c11-3d099e549d7c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "1cb389d6-4f32-42f4-a355-ecf969cfb824",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3082a01f-1844-422f-b468-fcdc8283fec4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "8b31a955-3c89-4d41-99f9-b46c7688825d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3d797d0c-7c18-4e0c-8b08-f4231bec7264",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a tactile text $b tct $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "91fb738b-a1b7-462e-bb9f-f206fcd316b6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e75c5eb5-d676-4824-be30-5c10c1f4f077",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a volume $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5ba98c7b-f678-4329-a959-b79cf20958a9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "341",
          "content": "$a tactile $e braille $2 w3c",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1a2c796f-7100-4d1b-8f5d-770afd136679",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "09a60251-52b5-4a15-90ef-5c9ae35ce926",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "0997e075-8bd1-491a-bd82-c750759a65ce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a Braille books",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "98d34a99-1ba1-4665-96f6-7c61e58ecd4a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "bf3ea53b-0bf9-43ed-a1c8-f010778c1f8f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "6b6ac463-acbc-44bd-93e4-332ff97c159d",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00784",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00313",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "03da9338-de41-4588-896a-3fc11689ccaf",
    "title": "AUC -RDA-BOOKS - AUC-PUBLISER 2025",
    "description": "AUC-PUBLISER 2024",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115713.5",
          "isProtected": false,
          "id": "2133a279-90ae-4c6c-ae58-f9a49ac8742f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "7001846",
          "isProtected": false,
          "id": "b34cfb8f-43ac-4b5e-8fd7-7664132e241c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "25\\\\\\\\",
            "DtSt": "\\",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "b3524a87-2fc6-49f3-a02c-876464a4b693",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "017",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4b3a807c-cfcf-4eeb-b1e8-06665c6300c5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f56faba5-3fc3-4e3d-843c-1008e6cb94aa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1cdc7865-c2ba-434c-8075-493dc513f4ba",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "be5c098a-ff9d-4ae3-b7f1-6d6f188b0291",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "375bac7d-b499-4586-ba15-d6b9a2b85900",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a / $c .",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "ef9e7f26-e5e7-4b1d-b793-7b3926dfc16a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2217b190-6094-46e7-b964-ae421da562aa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b Ø $c : $m :",
          "indicators": [
            "#",
            "1"
          ],
          "isProtected": false,
          "id": "40896bf2-d4a9-4b06-983f-496f6b0bf02d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ØµÙØ­Ø© :âª $b  Øâª $c Ø³Ùâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5a719357-e37d-4b91-828e-b3476356a29e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâª $b txt $2 rdacontent $3 ÙØªØ§Ø¨âª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c307adc3-3f8b-4c81-a2af-ecda49d208eb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f4b30d56-411b-45c3-96b2-cb419536d8f5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "091de2de-759b-4eb8-be9e-406eb5ce3c73",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "aa783e86-2bfd-4e85-998f-a97444eb5b69",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fdea1990-a695-4022-8a89-1c4c9fe678d6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "325f9d9c-42c5-49e1-aa78-2a189475895b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "4c282485-c2e1-4b3b-96d7-9a153fd0ad08",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "b9cd3b30-2706-4bf0-824c-038d3c4f57c5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "988",
          "content": "$a Publisher 2024/2025",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2f844efc-1ec8-4b70-9895-76920efc4968",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00775",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00301",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "347e90cf-3411-4c02-8cac-8a2a1ab52b3d",
    "title": "AUC Books Constant Template - AUC-TEMP-COIN-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.3",
          "isProtected": false,
          "id": "7a534ad0-f682-418e-a978-562c2708c18b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6105413",
          "isProtected": false,
          "id": "9295556e-ca18-45c3-b9f6-cd91feb089d8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "r",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Time": [
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "GPub": "\\",
            "Form": "\\",
            "TMat": "\\",
            "Tech": "\\"
          },
          "isProtected": false,
          "id": "0092419e-de12-4da2-a49d-6224f2fd0e18",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "93be47f6-f4ff-4bdc-8ba1-264ba07de7ac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "efab6872-3007-4058-8bc9-399ab77dd862",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "25d0ffb1-bdf4-44fe-8cf7-6416bf6e2cbf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "66e03f7e-8994-4af8-97dc-03684f0e56d8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "29c8c8da-bbfb-4c9d-bd09-fdd60168a97c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "dd75df56-5b8e-4881-86c1-eea9e957e684",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$c : $m :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "577f92d7-69ec-4a63-b0ce-27d31dd7464c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "042dde47-2c34-44d2-bb20-eb269b31171c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a : $b : $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "90869efc-697b-4803-adf4-4d8d957ed30f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a   $b : $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bc2d3c72-94fd-45d5-b3dc-6ff154bb97ac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a : $b : $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b295094e-bae1-4f73-8195-a128dba9ec5c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "341a6d1f-e2f4-4648-a95f-62d7cdb6aa40",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c290546d-398d-4252-a25b-ebf68cd1d738",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a Ø§ÙØ¸ÙØ± :âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "88417e9a-4141-4cc0-8be9-759ba7e89757",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a Ø§ÙÙØ¬Ù :âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cbbd922c-8480-45c4-aa81-11b01a4d52a2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙØ²Ù Ø§ÙØ¹ÙÙØ© : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8bcf5fd7-e934-43b8-832b-58dabe141b37",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "8f401c59-9ffa-445b-8e5b-742dfbdb144c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "a42bf58a-a478-4de5-8dd4-7d545dfac78d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "007d9aba-c52c-4475-a669-8e049dc82166",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "5440a004-3de7-41a8-ae2b-f64289eec4cd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "852",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "767e16cc-495d-4e11-a4a2-749bf37c0d04",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f3d3bbbb-89a5-4cf0-aa40-226f00624f3e",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00855",
        "status": "n",
        "type": "r",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00349",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "ab2d2cb3-f1d0-4586-b6ad-90a024e16497",
    "title": "DSPACE_TYPE_ÙÙØ§Ø¯ Ø³ÙØ¹ÙØ© Ù Ø¨ØµØ±ÙØ©",
    "description": "DSPACE_TYPE_ÙÙØ§Ø¯ Ø³ÙØ¹ÙØ© Ù Ø¨ØµØ±ÙØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "82ad3370-7e78-49cf-b434-24cf36c16f5c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367672",
          "isProtected": false,
          "id": "97ca1657-70fe-42dd-a02f-01e623919aac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "14204b0e-7b07-4a03-83f4-44b6e0db29b7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3d2b6969-c0db-4779-b9b0-445b653a6628",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a ÙÙØ§Ø¯ Ø³ÙØ¹ÙØ© Ù Ø¨ØµØ±ÙØ©âªâªâªâª $c 38851e6f-6eb0-48df-ab3a-0cb95c689b2a",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1fca65be-6547-486a-8848-2ad7f2f79d4a",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00346",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "6625e371-0442-493d-9380-99f4c522cd61",
    "title": "DAMAM_BOOK - KAC-ARA-CD",
    "description": "KAC-ARA-BOOKs-2015",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "b185f6fd-b556-4ca2-9a26-25ba75c91573",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "4873223",
          "isProtected": false,
          "id": "99daa4ea-a249-490a-8c31-e3a589bacbbe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Electronic resource",
            "Category": "c",
            "SMD": "o",
            "Color": "c",
            "Dimensions": "g",
            "Sound": "u",
            "Image bit depth": "---",
            "File formats": "u",
            "Quality assurance target(s)": "u",
            "Antecedent/ Source": "u",
            "Level of compression": "u",
            "Reformatting quality": "u"
          },
          "isProtected": false,
          "id": "41345851-0ae1-4e51-99b8-f8a65bf317b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "m",
            "BLvl": "m",
            "Entered": "150209",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Audn": "\\",
            "Form": "s",
            "File": "\\",
            "GPub": "\\"
          },
          "isProtected": false,
          "id": "c3cb7c75-02fa-4d58-867f-a485e4021b95",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "a16bd243-dcfa-4534-9aac-8b13b1559156",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "028",
          "content": "$a :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "d51d909b-a99e-433b-b5ed-1ac8edde24f2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a KAC $b ara",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "722b0f12-e5a6-4d5f-a3af-c7f984e4e2e2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "6287de2c-62df-4335-b76d-2f48381fc69a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "092",
          "content": "$a : $2 23",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "47c49617-bfdc-45d7-8e1e-5c4fc8c51b00",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "098",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cc5d1dae-6b86-4f1e-8c81-8baf2900b073",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "8506be9a-ecc9-44a2-bc51-f8b5c4aa1d98",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $h [ÙØµØ¯Ø± Ø¥ÙÙØªØ±ÙÙÙ] :âªâªâªâª $b / $c .",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "27457663-a51f-426f-9ea6-ed9b14f769d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "67885e0f-f6b1-48ab-a2bc-6ef1c90d41dc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "260",
          "content": "$a : $b Ø $c : $m .",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "22590fc9-c1b4-4938-9004-1b7bb05d7643",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ÙØ±Øµ ÙÙØ¨ÙÙØªØ± Øâªâªâªâª $c 4 3/4 Ø¨Ù.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fe9ce566-ade4-42a1-8495-1d4a0ae9a078",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "23b75386-dabc-4255-9630-89d6e054edd7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "516",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4414e5fb-c11a-443a-8883-1f6e63979e0a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2d26fc11-e921-4818-8260-c912684120e5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "59b5ff3b-c4f8-4138-a88e-ae85e723ba50",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v Ø£ÙØ±Ø§Øµ ÙØ¯ÙØ¬Ø©âªâªâªâª $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "fcb06d25-0a49-4cad-b4b5-111fefe2722f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a KAC",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "98a40faa-bcbe-4bad-b7f8-d2ef0bc17c4c",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00710",
        "status": "c",
        "type": "m",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00301",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "ffe78ca8-2169-4828-bfe0-947e907defcc",
    "title": "DSPACE_SUBJECT_Ø¥Ø³ÙØ§ÙÙØ§Øª",
    "description": "DSPACE_SUBJECT_Ø¥Ø³ÙØ§ÙÙØ§Øª",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "87bc8be3-c6fe-414c-9ac9-93413ec5d23c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367722",
          "isProtected": false,
          "id": "164e21c4-2a1a-4c3f-90b9-4fbe4ca0604b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "bcf31f1d-37ef-453d-abcf-27a74a9fc9d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bf420090-c5bc-4398-a48b-238214e916b8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø¥Ø³ÙØ§ÙÙØ§Øªâªâªâªâª $c 4ccccd76-a2ae-4ec2-af6b-cedb388d1f86",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d5f2655b-6f3a-47ac-ae59-eb38fe31a587",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00336",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "c2d36d37-1270-42f4-b3c0-a6bff90abae0",
    "title": "DSPACE_TYPE_ÙØªØ¨",
    "description": "DSPACE_TYPE_ÙØªØ¨",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.2",
          "isProtected": false,
          "id": "d20893ff-73d1-4a53-98be-4a18f7711419",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367646",
          "isProtected": false,
          "id": "5e78deee-9fad-426f-8974-647433360e21",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "432396f1-dcb5-4a84-a8a2-bf4ff778fca0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "25d69a67-abcc-42ca-91f6-fb49e35bbbc6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a ÙØªØ¨âªâªâªâª $c 148508a8-70bf-498b-b40b-6ed0ddcf8c7c",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a7f4ea5d-00ab-4bd9-ab8e-7619059e355e",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00331",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "2adbb363-c1b8-48ec-9556-4bdeec9182c7",
    "title": "AUC Books Constant Template - MBRL -PERIODICAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "dc7632bb-3aca-4526-90e6-2f9a2e309448",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6231035",
          "isProtected": false,
          "id": "6b5741c9-5ace-4b4c-a9bb-38cbd824174b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "s",
            "Entered": "000\\f1",
            "DtSt": "a",
            "Date1": "ra\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Freq": "\\",
            "Regl": "\\",
            "SrTp": "\\",
            "Orig": "\\",
            "Form": "\\",
            "EntW": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Alph": "\\",
            "S/L": "\\"
          },
          "isProtected": false,
          "id": "be997216-4946-4b30-a2de-aaeec9582a88",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "014",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "dc08cc4f-5306-413b-a4cb-661c99a671f2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "022",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8e87da95-616f-4c92-9dfe-0953d9b45b02",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6ca814d5-f4f1-4f8d-9094-5fbf80cab770",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4ca15ab6-7e32-4809-89d4-1e4688171c22",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "33ac0a64-8326-4656-b1df-77da322691ca",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "ba8be424-4b43-4b9d-9dde-457e7930e9f5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "110",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "dd69f4cc-3c51-42b8-99cd-9bcca2085bb2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "9dc9010c-a36e-44ae-a557-174b51fe57ac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "eb400010-006c-4d61-8a04-f4429ff44edc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "f1abdf74-abbb-447a-a181-6f3df4b5acdd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9ef0502e-caaa-4153-9e3f-e0be99a1e78b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "310",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2b9df36b-9c24-4cc5-a6ce-67da34228592",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "321",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "40dc8d1b-0382-4cca-9d45-85fc4f7770cc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 Ø¯ÙØ±ÙØ©âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "74188b73-f2a3-4195-87ad-06b09a681c36",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8d6c838a-05a5-45b1-922a-b5366b3be03e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "85cb67ae-44b1-49ee-97e6-b8aeb8821ad2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "362",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "fac60dd3-f256-4a81-b471-057de9ec95e1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "adfa6730-dc74-435e-a88f-8274b278141b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "07d326b5-f533-4330-8ee1-22b2727784f5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "515",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2439533d-32ce-4f32-8f92-02cb6fba4bf7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "525",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7f543ad5-3bc0-466c-9dbf-4e0f55a59c5e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Ø§ÙÙØµÙ ÙØ£Ø®ÙØ° ÙÙ :âªâªâªâª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "f75906ee-8e55-4b60-90cd-863f2d878dc9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Ø¢Ø®Ø± Ø¹Ø¯Ø¯ ØªÙ ØªØ¯Ø§ÙÙÙ : âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "104c3981-0e4d-4036-b8cc-af72d47b89f0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "5882e778-a980-4df3-9335-0bc5b3603873",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "67782d12-4dcf-47f1-9e89-2e59b2a33d85",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "dd89b4ac-691f-461d-9ba0-918078aa3245",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "16e7a9f5-fb72-49e8-9e6b-66245407032f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "7ab24156-73f9-4ce3-a935-4de404170b30",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "e694e116-1d2c-442a-997d-0455b29c17a1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "c47e6c19-f0c4-4eac-99ea-f8fabe5e8273",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "770",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "cd69be90-2e23-4861-af11-dcdc3c6ab917",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "772",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "932bc27f-8d5d-4633-8f3b-1c26369a89f7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "780",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "a0b1dc96-93c1-4d87-875e-d60ec76d2c74",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "785",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "afe55031-6962-4f5a-a0a3-c96443ced0ab",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "01290525-ea81-479a-9fcb-501030fe7d8a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$u : $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b59c2c53-1a74-4e63-9b60-e3eeae1aa4fc",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01258",
        "status": "c",
        "type": "a",
        "level": "s",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00517",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "407f11f4-24b9-478a-88c3-cd06bfcdfdc2",
    "title": "DSPACE_TYPE_ÙÙØ§Ø¯ Ø£Ø±Ø´ÙÙÙØ©",
    "description": "DSPACE_TYPE_ÙÙØ§Ø¯ Ø£Ø±Ø´ÙÙÙØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.2",
          "isProtected": false,
          "id": "1c451cda-d51d-489d-b909-68aa8a9161da",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6144892",
          "isProtected": false,
          "id": "57227ae7-39e4-4369-b5ce-1faebfb1db5d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "8c1977d5-229d-4843-941b-3ce8ec90733e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b6806193-6322-4018-858d-cb35a679c031",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a ÙÙØ§Ø¯ Ø£Ø±Ø´ÙÙÙØ©âªâªâªâª $c cc2cd28e-87ee-45f9-931d-c42a0c67d3d7",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4437ffdb-7b80-4cb9-8b28-4cbd4bb832d9",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00340",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "a1580514-8b69-4c4b-9603-b1838ed54791",
    "title": "DSPACE_SUBJECT_Ø¥ÙØªØµØ§Ø¯",
    "description": "DSPACE_SUBJECT_Ø¥ÙØªØµØ§Ø¯",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.3",
          "isProtected": false,
          "id": "a3a324ac-16ea-42ca-8082-bfa44c17813d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367708",
          "isProtected": false,
          "id": "cf18c608-dcff-423b-b570-0f67bbf6f969",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "838971b0-fbed-411a-856b-b9261abc8bce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "80cad725-83b1-47be-ad3e-f5bfb5489a27",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø¥ÙØªØµØ§Ø¯âªâªâªâª $c 2f66019a-ec49-4e85-a3f0-b93278af1762",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ee9ffee3-900b-423f-a68d-992facd6fbbc",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00334",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "9d9f2765-91c4-462f-8ae6-7a42405afc00",
    "title": "AUC Books Constant Template - MBRL-PERIODICALS ENG",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "91d271cb-3a64-4e6e-b63a-f4d738049e2b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6639375",
          "isProtected": false,
          "id": "0c26c3b2-44a1-4746-abca-545f1b8edd36",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "s",
            "Entered": "000\\a1",
            "DtSt": "e",
            "Date1": "ng\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Freq": "\\",
            "Regl": "\\",
            "SrTp": "\\",
            "Orig": "\\",
            "Form": "\\",
            "EntW": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Alph": "\\",
            "S/L": "\\"
          },
          "isProtected": false,
          "id": "9fa42cd2-4ba0-4e02-8660-39f44da0ab72",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "022",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e4a250ff-a149-4873-b660-e3d1ab8549d0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "748a89fa-d618-40d4-a4c5-7c1a7e6b77db",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "868a1218-f118-49f2-9975-bdf5c87fd34f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f4806c88-abbe-438b-96a0-4056124b7c81",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "7e48dccd-f55e-4665-8db2-8cab238152c1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "110",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "960915e6-cfc4-4944-b8ce-673b61d9a92b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "3646e21f-a9ea-47c2-a51d-3ce3de6c0796",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "80e4a6d5-e001-408f-8490-36a3267606c6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9844e455-3703-4670-a434-a2a57c11ccae",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "310",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "68cba14a-a605-4602-b390-519c3fa79136",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "321",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cfcde515-546c-4081-b75c-436de66ae367",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a text $b txt $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8ed5c899-62c0-4679-82e6-d4802370491d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0b58fa6b-c441-4d85-94a3-9b087246e9b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a volume $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5faa53ea-b1d7-449d-b726-3aed8ec3dfcb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "362",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "c9db2677-2fec-4bf8-8eaf-0f6f7735ac0e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "2becfc77-0341-4628-913d-e83c87098756",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "55b2d47e-d833-46f7-bd98-b2702090b8af",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "515",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "84e28827-8e32-4294-b5ae-2e79b4bfe981",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Description based on :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "cc1c626c-4440-41c2-a296-06384c2bb7e9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Latest issue consulted : ",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "5ccabd39-ac6b-4afa-b104-e7158df25d1c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "3e7b3bf3-d458-4883-8df0-f72b5d15d61c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "b2414841-cfc6-4934-9110-4851632777ce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "4fa522e2-bf86-40fe-bce3-3380c78b18fd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "9ca17691-317a-4533-86ce-50d047732549",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "0d03e29d-e3e6-40ce-b90e-331b83b8e1b8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "906ec15d-370c-4b6d-a561-0e06d502bed9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "9bf62edf-0591-4c6d-b3a7-5991fdeccdbd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e issuing body.",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "ff984897-ac79-4633-81f2-c2b4429d984a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "bba6cd07-0da9-4496-8c89-fe4b9997f6ba",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "d23251fa-7edc-4aa8-9a82-d5aca3803b15",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "770",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "66e0cc52-9963-4879-976e-50e7264c957d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "772",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "e5719be5-2068-49ac-b412-9862cd3fc854",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "780",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "ffbfccbc-6891-4667-bfc8-33b76a180c16",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "785",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "bda8e25e-6d80-4b67-a5a6-c702228c23f7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "257e1832-8c32-41fd-9345-85a2444813df",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01191",
        "status": "c",
        "type": "a",
        "level": "s",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00505",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "2cb4ca57-9cba-4da4-b51e-fbf6e45baf1d",
    "title": "AUC Books Constant Template - AE-FUPHI-ENG",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "658f3799-7e14-4f33-9986-d864208836fe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6974996",
          "isProtected": false,
          "id": "5e7827cf-3d6a-4ba1-89f7-0c8115722ef6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "250114",
            "DtSt": "\\",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "eng",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "g",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "56f09257-f5a7-4efe-a5c4-2d73bdf9c560",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3a056c93-0b43-443a-94c2-55c0b3abbed1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "77233d33-80c2-4087-b3bb-cc1215c2d96d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-Fuphi $b eng $c AE-Fuphi $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "edc72fd1-deb0-4d4d-8870-322a6f9c232a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f0aa811b-756a-4558-ad24-5933ef5f880c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "48a34b2c-afae-4f61-9940-dc159dd975d6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5e3db4bc-43ff-48bb-b18e-3d8d1958065d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "ebcc5005-84c9-41a7-b486-e18e1c747a6b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "8df505dc-5f9c-4f11-b049-dc2cac811d9a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "606dad6a-3078-49bc-ad51-1041ba58d98f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "a11ebe83-b47b-4d20-9486-5c53f0e83230",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fb663a1b-388e-45fc-90b2-5fa0b98cc66b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a text $b txt $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "206e27b2-3294-42ed-abca-e785c24938b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "30f5657a-a897-4ca3-a6c3-a4899a36b49f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a volume $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7a9b097a-253e-4a85-856c-62fd3cf000ea",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "97cd6e6c-50aa-403b-ad2c-27bb3872b888",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "144f9c6c-2627-4b29-a05b-0b2a94c9ba44",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "29b7996e-f2b3-453d-ac7b-2b8f8bcc795c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "2bc77a1f-b592-4694-a543-14c75e7b4fbe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "0e865852-16c1-4a37-aa91-5a8fd6104814",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "4b4c31cc-2895-44b7-b113-c40f994e69c0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "e92effce-6a6f-4c42-a91b-f0c49b2ec638",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a PHILOSOPHY HOUSE2024-BATCH11 $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8f07cb74-23fd-4db6-9b3d-8abea0d8119e",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00853",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00349",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "b5628925-b00a-4ce4-8a4f-55f8c35f4fd7",
    "title": "AUC Books Constant Template - AUC-TEMP-VIDEO-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.8",
          "isProtected": false,
          "id": "50c19277-cbad-4900-8b71-44eccfe8105b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6103313",
          "isProtected": false,
          "id": "44e417f8-31b0-4f92-a864-22b7fdfea82b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Videorecording",
            "Category": "v"
          },
          "isProtected": false,
          "id": "0ced59ab-da13-4f58-b611-84eda5d39a01",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "g",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Time": [
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "GPub": "\\",
            "Form": "\\",
            "TMat": "\\",
            "Tech": "\\"
          },
          "isProtected": false,
          "id": "5aca9352-8450-4400-bd4c-fe86afb58acc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ff5324b7-906c-4281-bc5d-56cf884aa76b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "67c75193-33d7-40f0-8c43-b3a5a6288ce2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "033",
          "content": "$a : $p :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c55311f6-6e03-4369-9d6b-c9553e5bf49d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5559b5f3-eda2-4975-952a-e0622fa1f8be",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$a : $k : $h : $j :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "d6f29b2f-ab0b-46b2-b6a8-9150f3a3f8b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b3b2c313-361a-4f46-bec7-990a95d3e92e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "c0cb63f6-81c1-4091-b449-446eb800f45b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "142b1e45-fd37-4374-87c6-6b1a7742fce2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "47b55c14-556f-4341-9716-deb905ea7758",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "3fa52b48-21cb-49fb-b6f3-9a1f22e3881a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bc61dab1-cc7f-42d9-819c-17219126184d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "257",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "70958047-673b-40c5-a7b7-db6a2fc922dd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "40ea9125-6e1c-43fc-921b-fb24122cbc1a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e26d96e2-ea5f-470a-b7a3-d96231545f2a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "306",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e65dd1c1-9ba8-4eb7-9ed7-cc4f0a0848de",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a : $b : $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cad5e400-f2b2-41a2-8850-011eb13f713e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a : $b : $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8db3db56-cb06-49b9-920b-92ebf086fd80",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a : $b : $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b6c17835-177d-45ab-8013-62059d904b2e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$a : $b : $c : $d : $e : $g : $h : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "56d03445-c6c6-44f6-bc0b-ad26f6cc260c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "345",
          "content": "$a : $b : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "842c69d6-a8e1-4214-ab69-5d7856ef343e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "346",
          "content": "$a : $b : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "25d70e3e-891e-474a-a167-a3c616268391",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a : $b : $c : $d : $e : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f1987dfa-d685-42d2-87e7-d9ec2b0e787b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "92c5e542-c3c5-4e83-897c-4ed8c36c9f20",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "505",
          "content": "$a Ø§ÙÙØ­ØªÙÙØ§Øª : âª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "383fca07-e336-4db0-b3ee-51f5ec4c0b1c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "135a7365-27fe-4110-b744-c4f37a09a426",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "e55213a6-ebf3-4342-90d6-ffdcaf282217",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "518",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "29823e9f-d868-4666-88a8-cecb1ce781dc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1d99a51a-932e-476e-afd3-a1de0bafee32",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "deffd77f-63a0-43b2-bfb4-ef164913fea2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1ac52ab0-8016-4e80-b9d2-f20c05b613da",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "147c92ff-8823-43e1-a235-b56dd38dffef",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "83f781ab-4048-499f-be41-b0e7e52562f3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "9bf49a7b-8972-4f01-a379-ebb41e3614ff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "788c7df0-0c13-4bf8-80fd-898f5fc37e60",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "516f3e0a-08c4-4ff6-a74b-14467f4aa75e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "3817e65d-e23e-409f-8631-82a151def9a9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "78509f02-5763-44ff-a8ae-0287bf378835",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "8798d41b-b389-4cc5-9d49-5b8679864d9f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "5e284eea-56ec-4d33-9a4f-96922d272d77",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "9dd3e314-9c13-4c8f-bfb6-d1dda71ffca1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "10372264-e521-4a57-b705-65693d7985b9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "b3c52e81-1970-4534-8086-9fb27215e6ac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6ef439e4-0ca5-44f6-95fa-a88f7a990815",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01363",
        "status": "n",
        "type": "g",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00613",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "85749610-55dc-4769-9b7f-14564f23f2d6",
    "title": "AUC Books Constant Template - AUC-TEMP-PERIODICALS-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨Ø© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "bed7d0da-447d-4b7e-9e40-e17011ed6a8e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6101294",
          "isProtected": false,
          "id": "b240a6e3-7bb9-4ec8-8558-a2dfe64294d1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "s",
            "Entered": "000\\f\\",
            "DtSt": "a",
            "Date1": "ra\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Freq": "\\",
            "Regl": "\\",
            "SrTp": "\\",
            "Orig": "\\",
            "Form": "\\",
            "EntW": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Alph": "\\",
            "S/L": "\\"
          },
          "isProtected": false,
          "id": "41d62f47-280f-455e-95b0-e7e65af7c527",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "022",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2148c6c6-bf50-4495-80ac-1995b3402e4c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ea1d12cd-de8e-4799-9252-4e0f23fbca54",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2c590fea-a3a1-4947-9dcb-8154ad144630",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "0f4d775d-bb31-46a2-af73-05bd897662f2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7b012100-fd14-4b06-b622-cb5277b8cdcf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "110",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "880ff0fb-2da1-4d23-9d59-3cfe9e46e7ce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "fc0db15e-cfb5-4402-a3e7-8b5ae1dd3339",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "4a771413-c87c-4a96-987b-079a058e0287",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a9edc9d3-2c85-4dc5-a0ab-39ac0ae94b2c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "1f0b56c0-e050-4697-9faa-dfad4cf5b369",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c09d64da-7960-4142-9148-f54833856b48",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "310",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6e34ac9a-417c-44fe-a96c-92283a997854",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "321",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8596b2d3-8a20-4357-b365-21c9c99b49de",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 Ø¯ÙØ±ÙØ©âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "11ea489d-a18b-4d29-8182-79a150fc3a80",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ffbbaf56-88b9-4ed3-a177-b7cae5c8db05",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b6c19f6b-0718-42c2-8371-3f2ff9d5d78a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "362",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "8c7a8728-9e3f-4a19-bad9-37aa266f3b02",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "4ad41638-9ce1-45c0-9011-f124f6294343",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "248e9771-499f-46a2-b1b5-5ac97ea3b402",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "515",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ed17f40d-5e28-4dba-8823-433c17d9b524",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "525",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1d50eb2a-0ac0-4985-a76c-7626ad861762",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "555",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "dea7f838-be53-4746-b51c-22922bdf5bd9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Ø§ÙÙØµÙ ÙØ£Ø®ÙØ° ÙÙ :âªâªâªâª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "8ef90b5a-4f25-450a-8211-8d471f948eb6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Ø¢Ø®Ø± Ø¹Ø¯Ø¯ ØªÙ ØªØ¯Ø§ÙÙÙ : âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "f4aefd54-7e35-417e-9b80-ddc9fbe347f9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "604159c2-b44a-48eb-9cca-cb5f0ba521d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "4a115ca7-c7fe-485b-b393-104132b885a2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "0337c810-8cc3-4826-9074-d5c1be907316",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "f35ac401-968c-4620-af3b-6e74a42a38d4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "e34e0e01-1b89-4e40-be04-46727ef2b28d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "9b37ee44-f73d-4cc6-bdcb-f26dcd7bff23",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "0df31668-dfc5-4025-9f53-f8e45872b5f5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "60c74f0f-2751-4d08-8132-8adc295a995c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "5d5bdb23-798b-4299-b652-4319816cb1b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "3fce948b-2397-4698-a404-37bc1d0c87e9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "770",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "4b34c336-da01-4049-b7dd-42423c235451",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "772",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "65a01641-b154-4d31-b200-7f24188c379d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "780",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "ee1d9041-32ab-4915-9c90-1532e812d523",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "785",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "bed9bdb7-d38f-4fa8-a0cc-2cd14fe85a76",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "245c4704-2157-4bc3-b1e0-1ce1b24be497",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d7a17fff-5bb5-4a15-b920-f44ea2f96185",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01365",
        "status": "n",
        "type": "a",
        "level": "s",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00565",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "fd6d03dc-2472-4302-bd33-cdec80089d8c",
    "title": "DAMAM_BOOK - KAC-ARA-SOUND",
    "description": "KAC-ARA-BOOKs-2015",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "f6e930fd-c9b8-4270-b65e-7ffdc9a60e16",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "4873143",
          "isProtected": false,
          "id": "2f2e0ab6-3b09-4276-9265-31588f1cd3a8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Sound recording",
            "Category": "s",
            "SMD": "d",
            "Speed": "u",
            "Configuration of playback channels": "u",
            "Groove width/ groove pitch": "u",
            "Dimensions": "g",
            "Tape width": "n",
            "Tape configuration": "n",
            "Kind of disc, cylinder, or tape": "m",
            "Kind of material": "m",
            "Kind of cutting": "u",
            "Special playback characteristics": "e",
            "Capture and storage technique": "d"
          },
          "isProtected": false,
          "id": "476f90ca-92c6-474a-aea4-b061f7cfb603",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "i",
            "BLvl": "m",
            "Entered": "150209",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Comp": "nn",
            "FMus": "n",
            "Part": "n",
            "Audn": "\\",
            "Form": "s",
            "AccM": [
              "\\",
              "\\",
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "LTxt": [
              "\\",
              "\\"
            ],
            "TrAr": "u"
          },
          "isProtected": false,
          "id": "55d93e89-7e60-4470-8875-050626195be8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "0acd1ae0-3bb5-4d5b-8afb-d21f5f97b827",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "028",
          "content": "$a :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "a54f7da7-a20e-42b9-a049-65c9a596fa83",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a KAC $b ara",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a2760ad0-f8db-4354-8711-3d51d7c15212",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "a4004831-3bc7-4cbe-9f96-94d75d31315e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "60515ba4-cf72-4d04-8dbd-5cd3603b7a38",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "092",
          "content": "$a : $2 23",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2ccafc35-6e1a-400d-b90e-bd4762cda5fd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "098",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "602d670b-b93b-4b33-9be9-b07decd3f271",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "be3686aa-57d0-4315-a8df-37f34bcfe73b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $h [ØªØ³Ø¬ÙÙ ØµÙØªÙ] :âªâªâªâª $b / $c .",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "279408b2-61e0-40d9-bca8-954931ee04e0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "260",
          "content": "$a : $b Ø $c : $m .",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d4eb36b6-4005-4c26-9855-74e9f6ed4e1d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ÙØ±Øµ ØµÙØªÙ :âªâªâªâª $b Ø±ÙÙÙ Øâªâªâªâª $c 4 3/4 Ø¨Ù.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e58fe04a-47e4-45e2-b95a-6669642aa76b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "306",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "df8bea47-baae-40ad-b21c-6599d5de5908",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "2415de4d-826b-4aaf-9035-f77674557226",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙØ±Øµ ÙØ¯ÙØ¬ ÙÙØªØ§Ø¨ ØµÙØªÙ.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "752fd1c2-f2f3-455c-ad97-415f1ba0b9c6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a Ø¥ÙØªØ§Ø¬ : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c413d8f4-d472-4b47-b1d7-3443e7f51b57",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "b470a50b-1593-490a-ba66-bb40ca637ab9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d248897d-e90d-46c0-bfc8-f4d98c45bb4f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "24ed5ed4-a3f3-485d-80d6-ecd4fc6e4dd1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v ÙØ³Ø§Ø¦Ù Ø³ÙØ¹ÙØ© Ø¨ØµØ±ÙØ©âªâªâªâª $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "64c3eed5-3a07-4ac8-8647-f421626a782f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a KAC",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a723effd-f8d9-4d28-a7e3-b0a3d429fa0d",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00810",
        "status": "c",
        "type": "i",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00337",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "fa281a5e-7130-41f6-ab74-fe72e7a9a519",
    "title": "DSPACE_SUBJECT_Ø¹ÙÙÙ Ø¥Ø¬ØªÙØ§Ø¹ÙØ©",
    "description": "DSPACE_SUBJECT_Ø¹ÙÙÙ Ø¥Ø¬ØªÙØ§Ø¹ÙØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "717c28f4-4803-40bf-8fe1-7bc5b5d69cbd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367711",
          "isProtected": false,
          "id": "05a7d749-e68a-46e9-a2bf-82f43f02970d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "99f42266-8d1a-447e-9d04-a9ba387d119b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5d9942f9-1993-4f82-ac53-e5d5663814cc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø¹ÙÙÙ Ø¥Ø¬ØªÙØ§Ø¹ÙØ©âªâªâªâª $c 4a6fb057-66b5-43f1-bda2-b101f508bdfc",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f3d8108b-0370-4205-88fe-3cc31fa58afb",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00341",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "3e261f45-4af3-4db6-8c24-b062716650fd",
    "title": "DSPACE_SUBJECT_Ø¬ØºØ±Ø§ÙÙØ§",
    "description": "DSPACE_SUBJECT_Ø¬ØºØ±Ø§ÙÙØ§",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.7",
          "isProtected": false,
          "id": "b720d3ae-b0ae-4367-8ecf-bbed74585a90",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367710",
          "isProtected": false,
          "id": "2a5d4503-3156-4843-bea2-b2de13b1cecd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "17cb2cb9-c6fb-42b3-91ad-01e8944c43cf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "66617f58-951b-4c4c-8d4d-ed4146058316",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø¬ØºØ±Ø§ÙÙØ§âªâªâªâª $c 7c25e586-7638-4c13-9645-b3d6eb822a0a",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "49f6fd14-cb9e-416a-a396-9dfa86b2c59d",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00335",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "c3cc299f-adfc-484d-8bb8-f809814895ef",
    "title": "DSPACE_SUBJECT_Ø¹ÙÙÙ Ø¨Ø­ØªØ©",
    "description": "DSPACE_SUBJECT_Ø¹ÙÙÙ Ø¨Ø­ØªØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "3caf4f2b-bc55-466c-b444-67f1dc8ef5df",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367712",
          "isProtected": false,
          "id": "0a40ded9-0cf9-4f7e-89a5-3ab05e0f7619",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "0aee612a-4387-4be1-a42d-2df1a9ee5259",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2334f7e8-0c91-4ed2-ad9e-2ffee42250f9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø¹ÙÙÙ Ø¨Ø­ØªØ©âªâªâªâª $c 16589c20-6a2a-4731-8554-151faa1e9f8e",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a5d1cc99-5eb2-42d2-a682-328a8705844d",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00337",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "15643135-a566-49f2-a776-01a94d3483ca",
    "title": "DSPACE_SUBJECT_ÙÙÙÙ",
    "description": "DSPACE_SUBJECT_ÙÙÙÙ",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.1",
          "isProtected": false,
          "id": "aa904050-cc30-4ab8-84aa-5339a27a8545",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367716",
          "isProtected": false,
          "id": "c350fe32-b923-4593-acb3-cc3829ebada1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "491897e3-320d-43e0-ad83-6ef71a8da64f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "56b1df14-65df-4e9d-9eaa-d7a783e0641a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a ÙÙÙÙâªâªâªâª $c 8e62898f-3f50-42be-aace-ae3eca9117f1",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7f554813-17ef-42ae-b505-661ee2debba0",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00332",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "0ada8884-fb82-411d-84fd-fd91a70e6bc6",
    "title": "AUC Books Constant Template - AUC-TEMP-MNUSCRIPT-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.2",
          "isProtected": false,
          "id": "717d2cc4-e6a5-4a5a-ad21-d6288c5fa446",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6103297",
          "isProtected": false,
          "id": "fd2b62e3-0457-47cf-904e-0ef61aac4ea0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "t",
            "BLvl": "m",
            "Entered": "000\\0\\",
            "DtSt": "a",
            "Date1": "ra\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "2149d375-8060-420a-bc3b-4225899c3de2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "694e79b0-6b87-4505-b468-2231839461d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "36fac89c-7747-4a8d-9317-acbbf4698ebd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "be08d1d4-4e6b-410d-90a0-40b46d3549fc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3bd8af8b-9b97-4675-9688-899b38dcf6db",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "d7704527-2ed8-4b35-8259-5feea4fb82de",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "54bf9df0-cd38-4420-8e3e-9a3ae28e383a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "ddeb4c92-8127-4f0b-9b51-ab9a4180d85c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$c : $m :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "8111f570-4001-469a-93b3-9350ae4474ed",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1e4f4ca3-de7b-4784-8e43-701c37531cf6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 ÙØ®Ø·ÙØ·Ø©âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a2738bf5-308c-4208-ab60-e9d9ffd4867c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "612f522d-6d33-43db-a2ce-e7a8ca16c419",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5b066795-efb6-481c-8e87-c8bddfad9a0d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$a : $c : $d :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9ee9b0bf-0b21-405e-a2a5-9a48f31450c5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "351",
          "content": "$b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6d7b279b-54d9-454a-9754-55b3c6910dcb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "041c882a-fbe2-4259-8a73-1eb0d492e1d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a Ø¢Ø®Ø±Ù : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "99029be8-08a9-496b-92a7-a1e511b9c21a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a Ø£ÙÙÙ : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3e291d6b-33d1-4763-936f-5842b3447f79",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙÙØ§Ù Ø§ÙÙØ³Ø® : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "60030db6-d7eb-4789-a5a1-d8db01a4f349",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙØ³Ø® :âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c20e13ab-f185-4080-87d2-fa5160dd420e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "506",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "bb775b65-f0cb-4409-86a4-9af275cf88c5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "530",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4f9ab8f1-e5e7-4d46-bd7a-b52b2a408de5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "535",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "af3d29fe-a51d-43b3-ba85-a63db1af2397",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "540",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0485ca84-ea8f-4949-baab-f0c9d07c0d80",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "561",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "51c07be1-2b56-4115-a3f9-940dd4e4862e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "562",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "18984f4b-c02e-40a0-9221-bc9189232953",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "563",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "892f7882-09cb-4713-99be-5158e3505f7f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "583",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d6225086-b0a1-4b98-8c4b-7135792aaedd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "76ec99cd-d844-47b9-b41f-d14574b36920",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "93e8b40a-aa1e-47c3-a7a8-e38cafc1aa69",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "596450bd-063e-4785-929d-fe016590e529",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "a2164752-0c91-4e01-adb6-9dce6384f0f4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "7c9addb8-51ca-4120-b3c2-f895c651b647",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "76bf44fe-24d4-43b2-880a-f5e112426a1b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "58bdc76b-286f-4dee-96bf-f312d7bf0235",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "efce2f85-c8d5-4041-b46a-967e6b17be85",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01194",
        "status": "n",
        "type": "t",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00505",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "8e071384-370f-4631-b816-5a2eddbbd852",
    "title": "DAMAM_BOOK - KAC-ENG-BOOKS-2022",
    "description": "KAC-ARA-BOOKs-2015",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "449b507c-3dce-4001-8691-85675f38df42",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6771723",
          "isProtected": false,
          "id": "9b8083d5-489f-47e0-a4f2-7f24b72f66ac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "170322",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "eng",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "490c1b2c-cb38-43cd-9527-b10af6b1dbec",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b9086a2a-a47f-4c24-9b92-8344aff7fad8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "ef2b1b4e-47c6-482d-b265-69c538a265c0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a KAC $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ca1e7930-458a-4884-9ca5-cb340d669eb9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "9c98d7bc-9092-42c1-a5c5-dec25e534228",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "092",
          "content": "$a : $2 23",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "59f3d4ca-cf7c-4dd3-b80d-f681ac019439",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "099",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "eb4e6714-610c-4765-97c1-dfa0abd90b1c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "0fa71750-8c28-4a8b-92e1-45f81bc11e47",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "72326ce0-dbbf-467c-9e69-b19bc03759ce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "accf951a-efca-40dc-8d57-11a2878528dd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c :",
          "indicators": [
            "#",
            "1"
          ],
          "isProtected": false,
          "id": "645defef-777f-4985-82be-57426f7ee0e3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a pages : $b   $c cm",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f0a0eca4-3e92-4e2a-8bd3-0770e5d1810f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a text $b txt $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b9f68695-ce50-42eb-837e-4b800e59c80b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3bfd3928-8895-4ad4-be64-3d895b6eb493",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a volume $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e0c2a56e-789e-4554-978a-883947c4d69f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "c0390d09-d52c-4e95-8c6f-714e9066eaff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a3c1b295-2fda-48f1-9362-e8c116fbe673",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4ceb8010-c9de-474a-b78c-8fd1d762c966",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "505",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "dbcdc3e8-5350-4d67-a96a-a1fbd34d57e6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "520",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "33ae28d8-a2b1-4de5-8d60-01eb066f193e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "969eb82a-486a-48da-b91a-c3fd03896178",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "590",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0ec96805-5a93-435b-b183-74e30130d1c2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "5a28deab-6e92-4829-86d0-fe3f4bf7762a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "8707a258-7aef-4ec9-b756-90c4fc0e4890",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "08889b07-854b-43c7-8473-eaad72817e95",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a KAC $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "57c013f8-3c68-4050-8edb-b5ab32756f75",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a ARAMCO 2024-Batch $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d8f03f23-235e-45a7-a4f6-70a1feab4efb",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00911",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00397",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "d464e48b-edc6-4f60-8f32-2e7796e715ff",
    "title": "DSPACE_SUBJECT_ÙØµØµ ÙØ±ÙØ§ÙØ§Øª Ø¹Ø§Ù",
    "description": "DSPACE_SUBJECT_ÙØµØµ ÙØ±ÙØ§ÙØ§Øª Ø¹Ø§Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.9",
          "isProtected": false,
          "id": "8371fb15-0e68-4c40-a36f-1cd108dfa69d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367718",
          "isProtected": false,
          "id": "fb44c02b-1ade-4796-b05a-b5c6cfecf09a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "bdaef830-1dc5-454f-bdd0-e668d81c175d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "18093aef-016f-42fd-b0b8-e5386e376e14",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a ÙØµØµ ÙØ±ÙØ§ÙØ§Øª Ø¹Ø§ÙÙÙØ©âªâªâªâª $c c5edfa22-91ca-441c-84ba-b1205ec87ff1",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0b6c45df-3254-41e8-8f3d-f7339f301c69",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00346",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "92528b96-3e89-42a4-b270-b9e7cc996b73",
    "title": "DSPACE_SUBJECT_ÙØºØ§Øª",
    "description": "DSPACE_SUBJECT_ÙØºØ§Øª",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115025.9",
          "isProtected": false,
          "id": "5d5db16a-3a3a-45f4-ad80-956afea3b439",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367719",
          "isProtected": false,
          "id": "20cf1454-0825-4a0b-b082-7a230e7fa6bf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "b94bf13b-d954-4d85-99db-115f02990d03",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e9ac8f87-5d30-4e06-a7ce-39731e1fe96a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a ÙØºØ§Øªâªâªâªâª $c 16e52871-0c6a-45aa-bc70-6933e54f9bb6",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "34f89944-84dd-4888-9873-554d4827fbc3",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00332",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "a2dba863-f5cf-4cf0-a3e2-b4f63821f5dd",
    "title": "DAMAM_BOOK - KAC-ARA-DVD",
    "description": "KAC-ARA-BOOKs-2015",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.2",
          "isProtected": false,
          "id": "6ccfbae7-22af-4b2f-8178-0dca9ca3c341",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "4873218",
          "isProtected": false,
          "id": "fb41283e-5916-49da-bab2-b9cba0ef37b9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Videorecording",
            "Category": "v",
            "SMD": "d",
            "Color": "c",
            "Videorecording format": "v",
            "Sound on medium or separate": "a",
            "Medium for sound": "i",
            "Dimensions": "r",
            "Configuration of playback channels": "u"
          },
          "isProtected": false,
          "id": "daf89e37-cc58-4f9d-991b-c0c34fe1b4b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "g",
            "BLvl": "m",
            "Entered": "150209",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Time": [
              "|",
              "|",
              "|"
            ],
            "Audn": "\\",
            "GPub": "\\",
            "Form": "s",
            "TMat": "v",
            "Tech": "l"
          },
          "isProtected": false,
          "id": "c8d91b6c-b684-4a83-a6ce-34f8b3116c78",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "a47fba02-b9a5-4891-9a93-283ff65a6dca",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "028",
          "content": "$a :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "387c9e57-cbdf-492b-957d-ac642922b258",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a KAC $b ara",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "221eb47a-c1ea-47b9-82ed-8b91c799d193",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "8b196734-e5ea-4de3-9103-499a4ae27f8b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "092",
          "content": "$a : $2 23",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "680ed656-2523-41b8-8d13-9ff283a96f28",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "098",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "80d6970d-6346-432b-8a1b-69eafeac13f5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "dbb77483-ab07-4ea0-ac32-e6648e0f577d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $h [ØªØ³Ø¬ÙÙ ÙØ±Ø¦Ù] :âªâªâªâª $b / $c .",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "9c96a0dc-bd0f-4dc1-8992-5efc1a3e7a11",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "257",
          "content": "$a .",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "81133216-8c17-4b2f-a612-dbe22ab48c5e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "260",
          "content": "$a : $b Ø $c : $m .",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ae321445-9a91-4ca4-8e6e-d02c0236bad9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ÙØ±Øµ ÙØ±Ø¦Ù :âªâªâªâª $b ÙØ§.Ø Ø±ÙÙÙ Øâªâªâªâª $c 4 3/4 Ø¨Ù.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d73e47ba-ed12-44f2-923a-041f7d3e78b6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "306",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d807e65f-6e09-4919-8a0e-cdd951ea0504",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "09af5a13-731f-4056-b96d-777dca7cb1a3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙØ±Øµ ÙØ¯ÙØ¬.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e89fae4b-fa3a-478c-988f-da86d80d504e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a Ø¥ÙØªØ§Ø¬ : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c1bdcb34-a3bc-475b-aedc-8e87656f9930",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "7198f7f5-e612-47fe-a2fe-122843f44768",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bac17c56-bc68-4271-974a-eab4a89311d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a ÙØªØ·ÙØ¨Ø§Øª Ø§ÙØªØ´ØºÙÙ : DVD.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "195869db-41f7-480e-9d48-2cbe3dd32114",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v ÙØ³Ø§Ø¦Ù Ø³ÙØ¹ÙØ© Ø¨ØµØ±ÙØ©âªâªâªâª $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "e48832f4-e0cb-4d70-9aab-9b3beff82d6d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a KAC",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "22a627e9-6232-404a-8086-10ac2ba1e878",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00824",
        "status": "c",
        "type": "g",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00337",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "70fdf15d-da03-47be-a45d-99609de403e1",
    "title": "AUC Books Constant Template - MBRL-PERIODICALS ONLINE",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.2",
          "isProtected": false,
          "id": "fe92dd52-f093-4fc3-9fde-1341c62c0556",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6618540",
          "isProtected": false,
          "id": "d6cf7c4b-7584-4403-ac33-ca5de1da1f96",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Electronic resource",
            "Category": "c",
            "SMD": "r",
            "Color": "c",
            "Dimensions": "n",
            "Sound": "\\",
            "Image bit depth": "\\\\\\",
            "File formats": "u",
            "Quality assurance target(s)": "u",
            "Antecedent/ Source": "u",
            "Level of compression": "u",
            "Reformatting quality": "u"
          },
          "isProtected": false,
          "id": "9770d011-2ee3-4452-a518-e23f6fc3ff8d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "s",
            "Entered": "o\\\\\\\\\\",
            "DtSt": "0",
            "Date1": "00\\f",
            "Date2": "1ara",
            "Ctry": "\\c\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Freq": "\\",
            "Regl": "\\",
            "SrTp": "\\",
            "Orig": "\\",
            "Form": "\\",
            "EntW": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Alph": "\\",
            "S/L": "\\"
          },
          "isProtected": false,
          "id": "461f2986-9173-48c3-8edc-f7e2d935195b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "022",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "72873e47-fc98-471f-ad9a-8fd8ba43235d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6bb68c59-d941-4213-9f53-ccd46df1ffcf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "abad51fe-181b-4932-8f89-72c05e0acf08",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "cd67fdb2-c70d-473e-938b-3a86c96a83ca",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "9ecdf029-4a62-4083-b8c4-d1516ec8458c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "110",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "e30d3ece-9658-49a8-9cd0-27922abeb8bc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "abff3cda-fe34-4cd6-b209-4c2a0300fa3a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "732c8830-04a5-433a-b278-2158a3f6a6b3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "58b8b80f-6734-4beb-a330-d786b24db0e8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ÙÙØ±Ø¯ Ø¹ÙÙ Ø§ÙØ®Ø· Ø§ÙÙØ¨Ø§Ø´Ø± :âªâªâªâª $b Ø±ÙÙÙâªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1ced8790-42a6-4aad-b3f3-73abca81bf67",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "310",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "812ea71e-1e1e-4c9c-912f-f2b2752f2b34",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "321",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1401ed59-c32e-4ab6-b455-1cbb22a7edd7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "37b5893c-8c36-462a-a76c-58f081032b69",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a ÙÙØ¨ÙÙØªØ±âªâªâªâª $b c $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1be7e61c-42f9-49e5-ab82-2c67a50da421",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙÙØ±Ø¯ Ø¹ÙÙ Ø§ÙØ®Ø· Ø§ÙÙØ¨Ø§Ø´Ø±âªâªâªâª $b cr $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7fccecb7-6ac5-45a2-9836-afe3a598866a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a ÙÙÙ ÙØµÙâªâªâªâª $2 rdaft",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "44ccf3fa-6ce1-4c6f-a08e-00ca6dc12788",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "362",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "7762ec5a-c65b-4af6-9727-7a10c2ad8e87",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "726d7c4d-b628-4533-8888-ad442096e65f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e571c3c3-37a0-4266-9500-d5efaef62970",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "515",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b6cb3ab2-672b-45d1-b24f-bd220affe934",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "520",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "e205c506-bac1-453a-a6b0-ee21c9713cb7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "525",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "151ed83d-8ea6-4d6c-8adb-a61241e95c20",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a Ø·Ø±ÙÙØ© Ø§ÙÙØµÙÙ : Ø´Ø¨ÙØ© Ø§ÙØ¥ÙØªØ±ÙØª.âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "688df6b7-b260-443a-807c-2c9939379b7d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "555",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "97b430fe-f3c2-4d7d-8d65-34396501c05a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a ØªØ§Ø±ÙØ® Ø§ÙØ§Ø·ÙØ§Ø¹ : 15 / 9 / 2021.âªâªâªâª",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "24d589e6-9afc-4d28-a8d4-17ee86aeb827",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Ø§ÙÙØµÙ ÙØ£Ø®ÙØ° ÙÙ :âªâªâªâª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "53c8d8a8-9bd4-48c1-a38b-27272ba0bd08",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Ø¢Ø®Ø± Ø¹Ø¯Ø¯ ØªÙ ØªØ¯Ø§ÙÙÙ : âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "204b8e37-067b-468b-a9c4-62729a15bb08",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "735f2c4b-77c2-4668-94b5-729625fcf9c0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "84f08ad5-4495-4927-bb20-bc37b2569797",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "a06a1faa-289b-4a05-9187-8a3b1c1c895f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "2e71937e-1c80-4dee-afc9-60545621b98b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "37dfac53-f80f-4972-a4f7-3f35c65ae7b3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "6ef7be6a-da12-4632-9733-3be45970dc8e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "7f00b65a-4f7d-477c-8d1d-c64dc479248f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e Ø¬ÙØ© Ø¥ØµØ¯Ø§Ø±.âªâªâªâª",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "0cf440d6-e1b6-4b17-aa2a-b675f66cc65e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "40241a5e-895c-41a8-8635-208236cf6a07",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "fcdcf67b-3a83-4e69-aad1-481898aae06a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "770",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "253d4a95-9c03-49f6-aba8-45246bed3197",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "772",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "1d9d7ed6-a334-4a79-b06c-ebf78488ab43",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "780",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "ce139be9-f13a-41c6-9702-c9c15be5cd20",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "785",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "ef817cde-a8f2-43b0-a07e-57906ae947e1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "914d09e4-6333-47ba-b1d2-1fcd61921371",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "2617cdb8-dd51-40b9-aba5-fd7fc024d5ba",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01564",
        "status": "c",
        "type": "a",
        "level": "s",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00613",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "101bc268-266c-4732-8cbc-7dd1e2462297",
    "title": "AUC Books Constant Template - MBRL-PERIODICALS ENG ONLINE",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "76830c9b-e319-4d8c-aaec-ea669675845b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6618577",
          "isProtected": false,
          "id": "75d686de-c1c0-4ad9-911f-d28a3f224204",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Electronic resource",
            "Category": "c",
            "SMD": "r",
            "Color": "c",
            "Dimensions": "n",
            "Sound": "\\",
            "Image bit depth": "\\\\\\",
            "File formats": "u",
            "Quality assurance target(s)": "u",
            "Antecedent/ Source": "u",
            "Level of compression": "u",
            "Reformatting quality": "u"
          },
          "isProtected": false,
          "id": "c59383cc-6f93-4c4b-83a6-c1d1fb996e2c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "s",
            "Entered": "o\\\\\\\\\\",
            "DtSt": "0",
            "Date1": "00\\a",
            "Date2": "1eng",
            "Ctry": "\\c\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Freq": "\\",
            "Regl": "\\",
            "SrTp": "\\",
            "Orig": "\\",
            "Form": "\\",
            "EntW": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Alph": "\\",
            "S/L": "\\"
          },
          "isProtected": false,
          "id": "ce055f56-b44e-44dc-8ee0-e5692cf75477",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "022",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0b43201f-6f3f-4721-ba42-47f40d70a937",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "61d0abc2-ea69-4069-a8ee-6ddb1ac02ce2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5d842e44-ff9f-49d2-99f1-9601909c97a5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "9eb06b2a-b62d-4b86-a2c4-8c23258b5e76",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "110",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "d345fbfd-de34-45f8-af63-af5bc1c44d41",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "de3c5774-81ad-4408-89cb-7ef3a9dbb478",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "37784c30-30d8-4f71-afdf-00bd6eb156fd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a online resource : $b digital",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5c8c0a07-66b3-49c9-b3a4-cddf758031ba",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "310",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "68f278d3-a3aa-4bec-bd63-4485d54eaad2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "321",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d377755a-e4fa-4c56-9f21-bc23a1cb4062",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a text $b txt $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1297ece8-4b7f-4553-a930-d6606661a920",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a computer $b c $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "666e7c56-150c-4c58-a310-d2d4cf3411dc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a online resource $b cr $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c85ca9a7-b973-45bd-9151-91231f91f57e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a text file $2 rdaft",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "05591203-8c4b-42ec-8564-24439c23b541",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "362",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "12351dff-723c-46b0-99de-c717f2f176c3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "4088d340-d4a9-48b9-b3eb-60907d4c7ada",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "38bae691-1d45-45ce-9c52-c6224e7e9941",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "515",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f60ada34-f2c9-43dd-8d64-771438e39dee",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "520",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "b4483261-b210-44f2-b1a3-b174340fd638",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "525",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "dd3d98bd-09bd-4aa7-8185-440e93287b69",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a Mode of access : internet.",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5db1b828-d8f9-474c-b606-f382d44926d3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "555",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9c950cd6-39e7-4e7a-92c6-23e7e8044b10",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Date of viewing :",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "c96087f8-9bc6-4cc1-a805-0243fd42071e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Description based on :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "09311f92-026a-4787-8af6-034a63c3b78a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a Latest issue consulted : ",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "7def7a15-ebcd-4f1c-bfd1-7835f3341143",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "838bf18c-2511-4406-af3e-82245771e376",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "5398c619-2cc3-408f-bbad-6488862b13c4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "22040335-3e49-4d37-8ab6-b9483628160b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "a8b4d4a5-50ac-4c3c-8878-94baef3f030e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "bd976eac-f6c5-4bf4-9e79-680aec4d5b28",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "b400dd97-1855-41cd-bfd0-371d3fc9633c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "8e20aec9-4603-4eba-8d8d-2266839e23ce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e issuing body.",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "8ad65de9-7967-4fba-9ee6-b342adda3825",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "7ae5cc0f-7991-4dae-80aa-f6bd2fc49cac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "d3ab9fd6-1060-4bf4-95d4-4695aee17313",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "770",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "6072b026-50ae-4d91-80b4-81bd629ad5a4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "772",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "e9ed393a-fcb3-4387-8457-31d411653542",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "780",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "4555421e-1c54-4143-8691-cd3ddfc3e503",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "785",
          "content": "$a : $d : $t : $w : $x : $z :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "39093634-b25a-48dd-ab39-d85337bdceb3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "edd6feaa-1380-443f-b375-2754b015cd36",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "1a5dc4f0-65e2-40f4-84e6-d700d6086119",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01414",
        "status": "c",
        "type": "a",
        "level": "s",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00589",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "53d0b34a-3804-49ad-a519-09e5b2b4ddfa",
    "title": "DSPACE_TYPE_Ø±Ø³Ø§Ø¦Ù Ø¬Ø§ÙØ¹ÙØ©",
    "description": "DSPACE_TYPE_Ø±Ø³Ø§Ø¦Ù Ø¬Ø§ÙØ¹ÙØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "ec986913-db23-496e-b3d8-65dd0c1d274c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367695",
          "isProtected": false,
          "id": "0ad8b1ad-a89c-4738-b0d8-f918106539f3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "e2a70887-3560-4a9e-a92b-fb5a240c7036",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fd976842-580e-42d6-a9f2-bb1479a385a5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a Ø±Ø³Ø§Ø¦Ù Ø¬Ø§ÙØ¹ÙØ©âªâªâªâª $c d9ac78e5-3f42-4084-b2cd-118918802cba",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7d8c876f-eef5-47aa-88e2-9937a86226ae",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00340",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "2d4d2791-2a4a-4c92-8a76-f4f6930cf224",
    "title": "DSPACE_SUBJECT_Ø¹ÙÙÙ Ø³ÙØ§Ø³ÙØ©",
    "description": "DSPACE_SUBJECT_Ø¹ÙÙÙ Ø³ÙØ§Ø³ÙØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.3",
          "isProtected": false,
          "id": "844165c0-9ef5-463c-8bf1-d2e8f098457d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367714",
          "isProtected": false,
          "id": "bb7fbac9-f7c0-474c-8e20-dbd444d9ddd3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "fd49db7d-6377-4284-90d5-f63d9c7dcd91",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e4b561eb-bcb0-4795-9e94-09f53ce18037",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø¹ÙÙÙ Ø³ÙØ§Ø³ÙØ©âªâªâªâª $c 5a24b0c6-2f53-47fe-95ff-35947218c222",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c5b175e0-3bad-46d1-9311-ee0994a33a26",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00339",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "eea9341b-ac6d-49d9-bc81-2eea8a88bbe1",
    "title": "AUC Books Constant Template - AUC-TEMP-ELECTRONIC -PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "a947549c-f7f6-4c33-a9cd-63c53390912c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6438237",
          "isProtected": false,
          "id": "a8688abf-4a46-4e25-b3f0-82623b81f0d6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Electronic resource",
            "Category": "c"
          },
          "isProtected": false,
          "id": "82bd9afb-6637-4bc5-ac28-967ef2d2d253",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "m",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Audn": "\\",
            "Form": "\\",
            "File": "\\",
            "GPub": "\\"
          },
          "isProtected": false,
          "id": "67222fb3-c927-484d-94e0-8672186332dd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f0c04581-8896-4718-9a3d-29521c852012",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d8a07485-c62b-4276-b328-fd1a4db186ac",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "255599c7-bfa2-4b81-b4e4-8e98b864f0c5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8290f7d2-45bd-404c-952b-27dbded852fd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "3a259dd0-60ca-4fe3-a350-d1d1defaf2da",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "aae6a31d-1366-434d-a784-f56e51c31db8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "a356c142-c9ed-44aa-8665-8392e13ddd2f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "9fc7dc8b-f1f1-4650-a87d-9a62c66e0fc5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ab86417c-efd3-4d40-8122-daf163fb90a1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "093b8ada-56e2-4bb3-b719-54a10959ae9c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "03a2b45d-5509-4fff-87df-10b5fe7daee3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a : $b : $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b2fcf1ed-b319-4f68-afe7-1f5d8df6c48c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a ÙÙØ¨ÙÙØªØ±âª $b c $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "39d39971-9b2c-4af4-8cbe-60562bbbb0fa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a : $b : $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9d73350c-703b-4e41-9f52-d5199f7fc0f0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$a : $b : $g : $h : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "79d8c819-f426-4ab3-aecd-34c2ec4ae4d0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "345",
          "content": "$a : $b : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d796adef-82d6-428b-bda9-1e3921419f5d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a : $b : $c : $e : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ab61d436-edcf-4fea-81ea-d0cd7851ab7f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "380",
          "content": "$a :",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "5d08e4cf-d50f-463d-95b2-25871c2b7a18",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "3ce54fc6-ac69-4ea9-9ebf-06d97f6304dd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f23a240a-0328-4699-adab-fe3c6bb9eeff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "505",
          "content": "$a Ø§ÙÙØ­ØªÙÙØ§Øª : âª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "371b691d-f878-4fd8-b213-3102efa6ecc6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "95105e71-f958-4a81-a8dd-680150139dcf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "530",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "feb9c799-32ea-4c85-a2aa-126f5e8d2c2c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c3eecf71-5970-4cb2-bac7-05bdeae55813",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "588",
          "content": "$a :",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "0d993ae2-6ab6-4f4a-9b1d-e1ca8cc507aa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "1318d6ae-b533-4294-a520-f5fb87171d28",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "ebb07f0e-0f0f-43f2-ad59-178b44c0fccf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "32ab2998-3d0f-4dff-b927-50dc37711439",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "cc4926fe-13a4-4ecf-a8cc-a491a8d2a04a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "31726b80-873d-40fb-928f-a70b541f9dd5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "5750ebf8-3de4-411e-8bf1-3acf54591b72",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "255ba91d-65d5-4e28-b0c0-8bc305c09f39",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "dfd9478f-9643-4141-b3f8-1e31bd67b0f0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "7936a428-1564-4f1b-99e4-3d14f1945902",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "dc31c300-a7d2-4340-b8a6-7f731f62ea68",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "80ab55fd-7cd8-4b00-98df-927f035eaa7d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "851acd56-ff32-4afd-88be-f66e575e7c95",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "81e15108-a593-4112-82ba-ddc1109a7409",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01250",
        "status": "n",
        "type": "m",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00553",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "a2425e76-05b0-4dd0-bced-95cd13a37264",
    "title": "AUC Books Constant Template - AUC-TEMP-MUSIC-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "5d3a349b-b671-4045-a293-ef552fa61fe6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6103284",
          "isProtected": false,
          "id": "bcab8825-7bc8-4739-b82f-45e2246b6b68",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Sound recording",
            "Category": "s"
          },
          "isProtected": false,
          "id": "647d3ea3-245e-4975-8429-e91e05fccdff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "j",
            "BLvl": "m",
            "Entered": "ara\\c\\",
            "DtSt": "\\",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Comp": "\\\\",
            "FMus": "\\",
            "Part": "\\",
            "Audn": "\\",
            "Form": "\\",
            "AccM": [
              "\\",
              "\\",
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "LTxt": [
              "\\",
              "\\"
            ],
            "TrAr": "\\"
          },
          "isProtected": false,
          "id": "0a14526e-f211-469e-b7ef-94f43c25b992",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c77da22b-8991-42ec-a3a3-32059497a136",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "9a3d609a-3702-4760-bc0a-3a014c79bc05",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "63f5ce57-0e5b-4c81-b640-7b8764b2f302",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$d : $d : $h : $g : $m : $n :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "7594fe8a-b710-4ce2-b64a-33244f80ab16",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "baed30c1-20d9-4f67-961f-3f734aec7257",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "bbfe724d-c2e1-4d7e-95b0-435cbcb90830",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b2f0a9dd-3493-4dfa-9325-8d8954af2253",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "70e64539-26cd-4f6a-9a16-eaabbef09857",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "81f22b27-2829-4046-82f0-11b12833b32c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "bc81b2a6-ba4c-4846-a700-c6aac61c887f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5af02690-5bf4-4b5e-9e9c-7ecf04a0471e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "c0713cec-e6a0-41d1-9360-0db62f8b111c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "51e16273-bda8-4538-a930-4b853a404e07",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "306",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "573332b8-c21f-4d41-901f-1eca0ea2bc72",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a : $b : $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c019bcb9-7436-489e-92e9-da4cc0384206",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a : $b : $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ed1babd1-f3cb-44c2-aa78-7d48ff6a92cf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a : $b : $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "547a5626-8532-450d-936e-ac4a9f0bbf08",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$a : $b : $c : $d : $e : $g : $h : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cf7f1e73-8dfc-4db1-a032-21ca801e4807",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a : $b : $c : $d : $e : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e7ba187b-bf10-43d0-90f1-7ff3c6ea6873",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "1edc6d71-6bf3-4876-b8ba-b0f2cc9f36d6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a4c022bd-5edc-4051-996f-a02fba0f7da7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "505",
          "content": "$a Ø§ÙÙØ­ØªÙÙØ§Øª : âª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "0113d5fa-1d6e-4ca6-b3ce-bfb2feb0a8b2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2999f225-b453-4aef-a8d5-5301f278ba8b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "746c4138-5bf6-4f23-a5f9-f478bdd4b3e2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5f3ccd24-efcf-4991-b3eb-12ba34b06a85",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1bc85735-4f77-4a69-9852-1cae16856089",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "37301aa4-a3b6-44c6-b915-431e4fe3a512",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "6cb9a2d6-2c83-4ca7-89e2-f5c6ce310773",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "9abf48c0-b0a2-449b-8f35-908837d65ec2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "11a2339d-8b7d-40d0-b80f-0186859909b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "bb5be231-2383-4466-9edc-81ac0c8859d1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "acf9e232-e9b3-4962-8893-694f492c098d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "9163392a-7d88-4c94-b4bf-039eab57a826",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "c82220e2-fc1f-4f3d-b53f-53986835257e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "329e9dee-018c-4b99-ab9b-ce3b6eee3e75",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "488f49d5-12e6-4876-bd96-6a293886622a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "16bd6a3d-57e5-4018-a753-15f882e98172",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "d7826ee3-baaf-47ff-bee2-98ebef962824",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "eb115d46-4d83-43ba-8b45-b7a3ad019fcf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6dabd2b6-abe1-4b74-a0c7-2ff94bfb7b05",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01311",
        "status": "n",
        "type": "j",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00577",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "487c18c7-cf1d-447e-939b-6a395ac27c90",
    "title": "AUC Books Constant Template - AUC-TEMP-MAP-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "886842a9-a601-41d0-bcc2-8bc6aeaf525b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6105407",
          "isProtected": false,
          "id": "ff567be1-f022-4aa5-9a7c-238a14b38d5f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Map",
            "Category": "a"
          },
          "isProtected": false,
          "id": "470a6b83-ef57-49eb-86a3-e204ebf5f20d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "e",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Relf": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Proj": "\\\\",
            "CrTp": "\\",
            "GPub": "\\",
            "Form": "\\",
            "Indx": "\\",
            "SpFm": [
              "\\",
              "\\"
            ]
          },
          "isProtected": false,
          "id": "a790f723-167e-451e-9b6b-623f2ef89e27",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1af66ab3-974f-4825-af34-1cba92807a46",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "034",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "020b1d11-464e-43f0-9ee0-eebf20fdd7c4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ec8413e7-fe3c-4859-8e1e-7f063e8c8984",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "06babcc1-9e0e-469c-a31f-2cfa671137c9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "c6c627e9-01de-44ef-9320-20bf28341beb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f587036d-2571-4755-8e11-ddff7d3a8a76",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "110",
          "content": "$a : $e Ø±Ø³Ø§Ù Ø®Ø±Ø§Ø¦Ø·.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "d85f964f-d213-4ec0-9164-561b19ff5273",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "71725094-35ed-4f5e-87d4-7c17d2586cdb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "846522cb-ec4c-44a5-ab4b-5b16c28bed73",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5675d505-7d8c-4f37-8ec6-60fc832c3736",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "255",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7a8203fa-0634-4122-aa02-a1d586d5227e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "199da4c2-96c5-44cd-9e59-5427d3833b74",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9755cc7f-7c05-4e39-bd0d-08814c373f32",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a : $b : $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c7f424ea-69f7-498c-800f-a99194b702a4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a : $b : $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ddf4a6ba-69c2-437d-8080-de3ae5aa2ac1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a : $b : $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e9682e4c-aa5c-411e-a42e-bfa14c6c37d7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$a : $c : $d : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "898246d8-294d-450d-b1bf-2766246ea0cc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "482f541c-bb40-4992-8919-b3d020073683",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e417b2fb-6576-44cd-ae36-a1a5c2fa0e41",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "507",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cf2986a9-9d9f-4420-8537-1bc93ea1b3e0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "522",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "892d9650-d507-4f21-8bc9-69ece65e1eaf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "e82f0b27-9f44-4103-a154-72a0a67ed987",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "692733ed-d39e-467a-8094-5de9a69bb470",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "f2928bb2-47ed-4804-adc1-c9857f0c9a51",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "3b1dac06-35bf-4c44-b814-deadb488b98e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "7924119a-8c2e-493a-b476-89966799c78a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "42e6384b-39c6-40cd-b8d3-4bc4000cd764",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "5865fc51-0473-43c1-927c-a22e3fc222a8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "1671c3bc-781f-463b-be98-fa73630b47e1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "9c195cc9-c9e3-4878-a733-6ca1da703848",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7000b3ed-f447-4f2c-ace6-4d4d56567bc0",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01083",
        "status": "n",
        "type": "e",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00469",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "2c3bc87f-ba54-4fe8-bf39-53ecb01bd083",
    "title": "AUC Books Constant Template - AE-FUPHI-RDA",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.8",
          "isProtected": false,
          "id": "ea0a6e92-574a-4ea1-b811-ebde91db1760",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6974993",
          "isProtected": false,
          "id": "9349b9ef-35c2-41ed-80b4-6f125c447f5e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "250114",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "g",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "2f173f5e-c2d5-47bd-9111-bb1bc12d690a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4fc73951-be72-4581-9685-d0177d093501",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "f21921a5-1abc-4911-95b2-89dbba016866",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-Fuphi $b ara $c AE-Fuphi $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "68a57628-2c8c-4c5a-80fb-f92129f5aa8b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "5015716c-dba0-45ad-96b1-0023fa5bb5fb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a546dc7e-964e-4e4d-b26e-7852727d6c5a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "ea396e32-0905-4755-9e90-78d5f4a5b744",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b / $c .",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "69fa79ea-3f7a-4667-9821-9c7d9694e426",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "99f9cfbb-8e76-4f0b-b15d-2be1fa1cbb92",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b Ø $c : $m .",
          "indicators": [
            "#",
            "1"
          ],
          "isProtected": false,
          "id": "be740e85-125f-4dc9-b919-4d18ee3a8139",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ØµÙØ­Ø© :âª $b Øâª $c Ø³Ùâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "02f6b311-8cd0-4dc6-9865-90b519d1c0d7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâª $b txt $2 rdacontent $3 ÙØªØ§Ø¨âª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0a1e41ff-3687-4ff7-9ab7-2bf5f3a3b14c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d2e33af8-9e4e-4cca-9b32-59415d5c8501",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4e6ffe4f-f71c-4fbe-8b51-5eff8de7a4f3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "31b38540-3d63-41a1-ab6b-f8055186317f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ed414774-8d4f-4ab8-8951-e9a38e08903f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "ad6b1afb-6b75-4d12-ac8f-b673b3c36ce4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a Ø¨ÙØª Ø§ÙÙÙØ³ÙØ© 2024-Ø§ÙØ¯ÙØ¹Ø© 10âª $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "590cd7f1-4aa3-4e6b-9ff6-4c99ab84cfa3",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00764",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00289",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "28ef2977-a97f-4d19-8276-d096c3034b00",
    "title": "AUC Books Constant Template - MOC HERITAGE-RDA",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115713.7",
          "isProtected": false,
          "id": "2b9ff7db-73b7-464e-8df6-ed9d4f73715c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "7096954",
          "isProtected": false,
          "id": "2964d360-77d0-4dc1-a839-e7d37bf11aed",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "240818",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "g",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "6d443548-90f4-4851-b299-a069196e20df",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "024a4f52-b207-4678-a298-7ffbba147651",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "b8d7d9ed-2fdb-4b48-a810-da4e879d9e26",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiMOC $b ara $c SA-RiMOC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1a752138-2d9a-4095-b8a4-2bfc5314f81f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $b : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "b45f0b20-c527-43c7-ae6e-9967617fb65b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "f87286eb-21f9-4cad-9a0f-4b0ea11a85b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b / $c .",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "53f2aaf2-8d65-4f71-8636-402dc8a68596",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7df3d161-da9b-4b01-93a2-a8de3898be65",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b Ø $c : $m .",
          "indicators": [
            "#",
            "1"
          ],
          "isProtected": false,
          "id": "ba1f7241-7c96-41bb-8be9-1db7c7d24986",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ØµÙØ­Ø© :âª $b Øâª $c Ø³Ùâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1a07dd26-0e8b-49f8-a0ae-99697ea8324c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâª $b txt $2 rdacontent $3 ÙØªØ§Ø¨âª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7ce7aa4f-22e3-414d-b9f6-ce63af162946",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6b5c8972-7c34-442a-b981-2bbab9a99ab9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2a6bdec2-862e-4ff8-83a2-28f034a5cb33",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bf02086e-298e-4503-94b4-3c5d4ffbbc9f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b2c09231-451b-46a9-b286-1768d56a9347",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "03dcc45f-032c-4ff1-bfd0-2279b3bdbd68",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a ÙÙØ¦Ø© Ø§ÙØªØ±Ø§Ø«-Ø§ÙØ¯ÙØ¹Ø© 20âª $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7fdd8f55-2bae-48cb-a21a-71e6b8125779",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00741",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00277",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "b5929955-148f-4849-b6d8-0cb706b4793c",
    "title": "DSPACE_SUBJECT_Ø£Ø¯ÙØ§Ù",
    "description": "DSPACE_SUBJECT_Ø£Ø¯ÙØ§Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "cc9e5e5b-5be5-4207-86ad-f22712c38f28",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367706",
          "isProtected": false,
          "id": "26507f94-0b3b-48d0-b1c9-0513edecd91e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "8efe26fa-1666-402d-bd94-927f22b3e786",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "db7fed2b-7394-42c0-afe9-52beb6b2038b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø£Ø¯ÙØ§Ùâªâªâªâª $c da5e5c6b-7e9b-422b-9ead-d370057c623a",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0f420018-c310-4a2c-86bd-92b8ff52b834",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00333",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "a0a61e7d-f34d-469a-9e48-869e96fded24",
    "title": "DSPACE_TYPE_ÙØ³ÙÙÙØ§Øª ÙÙØ¬Ø³ÙØ§Øª",
    "description": "DSPACE_TYPE_ÙØ³ÙÙÙØ§Øª ÙÙØ¬Ø³ÙØ§Øª",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.2",
          "isProtected": false,
          "id": "a98500ec-1f7f-4bd0-8e8b-21c4f564b6d7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367686",
          "isProtected": false,
          "id": "78e59047-f64e-4022-b9fd-5d4897ea851e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "9ccdf662-776a-4d8e-ae31-5fd2f881d452",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "dce2f905-1663-4b11-9058-3cfeda9c2042",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a ÙØ³ÙÙÙØ§Øª ÙÙØ¬Ø³ÙØ§Øªâªâªâªâª $c ddb4ec4e-1e40-4367-8c30-eee95b5168bc",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a22febf0-f9bc-4dcb-8640-bd1d30480ed5",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00343",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "67f8bcb2-208b-4af5-8c7b-12a4d0fe44cc",
    "title": "DSPACE_SUBJECT_Ø£Ø¯Ø¨",
    "description": "DSPACE_SUBJECT_Ø£Ø¯Ø¨",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "fab41172-3bb6-48b2-8ed1-c862bd42dd3d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367704",
          "isProtected": false,
          "id": "951a0fdc-6bb6-4063-9f25-b2dad1088ba0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "e12c7f70-5cb6-4e32-a575-5857a536f966",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "af9e4f33-d300-43a0-9c15-02e690dfc72e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø£Ø¯Ø¨âªâªâªâª $c 1d58fb28-d771-4a48-b97d-a39c2b3f4d41",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a8cd86f1-5964-46fa-a496-d463ed820c35",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00331",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "f35a9f94-54f3-4e01-865b-d70812fb427b",
    "title": "DSPACE_TYPE_ÙØ«Ø§Ø¦Ù",
    "description": "DSPACE_TYPE_ÙØ«Ø§Ø¦Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "00e48d99-28fa-4292-8c88-e532bb85bc0a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367696",
          "isProtected": false,
          "id": "9f4fa885-b454-4499-82aa-4e8062ff3c5c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "14d75a6a-a434-4b5b-a33c-9ee7d51e725c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4e69eb73-2269-4262-9bfa-df8b8a266f9d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a ÙØ«Ø§Ø¦Ùâªâªâªâª $c 7dd8f99b-3488-4d7c-b5da-31e77ff0aa03",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bb24c212-93ee-46dd-a215-28b62c9a0836",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00333",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "c93ad684-40e3-451a-be08-65c59d7df67f",
    "title": "AUC Books Constant Template - AUC-TEMP-SOUND-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "3afee266-6571-4b4f-9c7f-a75f67ba097b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6103273",
          "isProtected": false,
          "id": "5b656535-9062-4a44-b354-75f7b18c81b0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Sound recording",
            "Category": "s"
          },
          "isProtected": false,
          "id": "d8377a95-986e-46e9-bdd0-00c7d371e889",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "i",
            "BLvl": "m",
            "Entered": "ara\\c\\",
            "DtSt": "\\",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Comp": "\\\\",
            "FMus": "\\",
            "Part": "\\",
            "Audn": "\\",
            "Form": "\\",
            "AccM": [
              "\\",
              "\\",
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "LTxt": [
              "\\",
              "\\"
            ],
            "TrAr": "\\"
          },
          "isProtected": false,
          "id": "e2bbd21a-24e1-4ec0-b086-5ba6829d2268",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "48b18520-7205-4f7f-a38d-d978d423077c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "3faab734-d620-4c01-bcee-4c9e34d55dc6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cbab6f19-503f-47f0-adf7-1ea53b393240",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$d : $d :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "83fc4f75-7b0f-4d0c-acbd-cf3ce3f44a5b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "27072d37-7bdd-46c9-a2b5-da1bbfc9d881",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "837e9f88-98dd-41be-9d0e-594a049e5030",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "00219a30-4e5d-4ce1-9cb9-b7fd9fc103ca",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "408a8f42-ea46-4384-8e92-9e01252d2d82",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "d1a0ac06-1363-4a6f-9358-6505541ed124",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "98c752d1-c147-437b-8aa9-41d57e6694f4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c3471666-94e4-4160-804e-95b7bc268d91",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "49e9fd66-3d65-4178-83f7-16c224285da0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1a0dbafe-6760-4d6f-b9a2-0324812c9651",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "306",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2ed1926e-bdd1-4369-96f9-ef52a8a24706",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a : $b : $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7bf57615-594f-4e31-ad84-1611cdb479df",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a : $b : $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1dceef09-9e8f-45d2-94a2-9ed2a492c566",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a : $b : $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "73fa22fb-bac8-4fbb-8c26-b2abc3d1cb48",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$a : $b : $c : $d : $e : $g : $h : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "82ac28f8-c930-4968-924e-78a58934d993",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a : $b : $c : $d : $e : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5de8b738-ee6e-4a64-94d0-2b8f86341cb8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "c47b7c66-b8d8-438f-b854-6e4673d6a433",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2d1ddc7d-e75c-4b7f-863c-1f29accd16f6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2b4a9350-bb27-46fb-b977-33c488cd142a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "505",
          "content": "$a Ø§ÙÙØ­ØªÙÙØ§Øª : âª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "160b4012-207e-4644-9611-67925462fae0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "47652ae2-9a10-4f1d-9989-8d2fef8d92b3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "5108854e-efab-4e73-8d90-b08f2907b6a5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6d79417f-af73-4586-a467-0d843c6c85ae",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fb9cb92f-165b-42ba-9238-ca75ff91c937",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "396accb0-8dca-4241-b31a-76cf56e5a0bf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "87317992-577e-4f48-9119-cb2f046ea220",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "e829a5bb-7ce7-4125-8ffd-30a37c65eb02",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "1094bc50-fec0-4695-b624-525df4ea3eee",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "818f2630-85d4-4eae-8753-bc840695f414",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "dc8164a7-a22c-46a9-9d35-4c24fe7f0d3c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "cbc3deaf-edaa-4f0a-b84a-41a425c7b04f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "baec15ab-21eb-4855-84a6-7fd2cc0b0df6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "0ba4590c-7494-4fc0-9c87-eee25a19fd77",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "49f4c9eb-80b6-4c52-b392-a64cd8b9226b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "b29d01b9-50c7-47c5-a175-c40c7816eec0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "14ef83c4-f143-4037-a83e-862f2e93b40e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "5eb6d02b-2012-4d5d-b0a3-4021e0dac399",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cca1c5b9-dd19-4051-9198-38274bbc6eed",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01317",
        "status": "n",
        "type": "i",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00589",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "3414a8fd-9f59-4178-8e29-89fd9808c56c",
    "title": "AUC Books Constant Template - MBRL-DVD-ENG-RDA",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115713.0",
          "isProtected": false,
          "id": "db278f62-2af9-4fce-91e6-833096342317",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6803593",
          "isProtected": false,
          "id": "f3077e49-6cfb-41c2-8950-b4661ce751ee",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "007",
          "content": {
            "$categoryName": "Videorecording",
            "Category": "v",
            "SMD": "d",
            "Color": "c",
            "Videorecording format": "v",
            "Sound on medium or separate": "a",
            "Medium for sound": "i",
            "Dimensions": "z",
            "Configuration of playback channels": "u"
          },
          "isProtected": false,
          "id": "b5993e53-cd7d-43ef-828b-95e37d692f02",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "g",
            "BLvl": "m",
            "Entered": "00\\mae",
            "DtSt": "n",
            "Date1": "g\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Time": [
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "GPub": "\\",
            "Form": "\\",
            "TMat": "\\",
            "Tech": "\\"
          },
          "isProtected": false,
          "id": "7e1585ec-3fb6-4206-be2d-1465e92a454a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9512520a-81ea-497e-805a-6ffd5d948964",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7101a316-48f2-4238-8d63-93a8e2955c16",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$a : $j : $p :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "9a42eca4-57d6-4452-ae18-078d1127fc20",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f5e4ab5a-36e1-458f-bfbb-df7a026a428d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "071062c5-2215-4ff8-97c2-58313a304fa5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "345ca8bd-6e7f-476f-8147-27cb135a9292",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "0c6a508c-8091-4116-aa65-71b9aa2dd4b4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6b808af4-cab3-4e5d-9fcd-3251123232ae",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "257",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e32b4021-4e37-4533-b3b3-cbca7da20bbe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "a5de260c-c9e2-4cdf-be3c-3a602dd9bf5e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a videodisc : $b sound ; $c 12 cm",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2f346070-5ba2-45db-b10c-7f574d9062c7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "306",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c524ad51-e6fa-448e-8033-abb15dbbc6dd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a two-dimensional moving image $b tdi $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a0913207-5a2d-4804-8ad7-a87ede6d0786",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a video $b v $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d7794e59-a418-4d93-8859-2292b1e4df7f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a videodisc $b vd $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c5784618-7cd9-4e1c-b66a-ed8b735f8751",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$a digital $2 rdatr",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "266b7eca-ef94-4d06-ae17-483211abc066",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$b optical $2 rdarm",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "79c2baeb-ea04-4090-9e22-d975300c3892",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bcb0b10f-e254-49c9-936d-2f3a599cf35e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$g : $2 rdacpc",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "857494a7-8f3c-48af-9e83-4169b23e8ba3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "344",
          "content": "$h : $2 rdaspc",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9fc79882-d2b9-4a2d-8dc5-f49bf735f1b0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "345",
          "content": "$b : $c : $d :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "da436706-11fd-4442-9e99-0d968ad48951",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "346",
          "content": "$a : $2 rdavf ",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0e50d386-095b-48df-8421-3cea9fda4002",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "346",
          "content": "$b : $2 rdabs",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4b82106f-81f1-4c7a-80fe-375efd2a0aad",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$a video file $2 rdaft",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bea14270-ffa0-4a76-9337-909b455de908",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$b DVD video $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "39d84234-aa6b-4d99-987a-209a24f0edaa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "347",
          "content": "$e : $2 rdare",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8239cb5e-2e68-41b8-96e5-311e6274feae",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "202afcc8-6b56-45fc-8ee5-5fd05cfcf141",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "505",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "d48b1260-739b-496b-9ea9-4c9e71b00007",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "508",
          "content": "$a Production : ",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e4f2af41-4839-40d0-a189-da274588bd74",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "511",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "eb827183-ef99-404d-88fa-a6943fb530fa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b54de7e6-b77e-4381-9c20-41b50bdfa4b3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "538",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "353301e8-b37f-4851-b915-96a2e14d07b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c63f0961-a91e-47f9-a441-cee056e07af2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "30adce71-04a4-422a-bb94-8e475e5489a9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "c0e213c3-e03a-4526-ab48-97c69bba3736",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "00cb2b81-0cf2-4a23-a86e-d8d6a0758ac2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "24b26279-b10e-40f6-b197-2bad2d5a05da",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "9bc7b050-8a96-4635-95be-0cee7635b63a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "e323976b-3bf7-4e40-a50d-ad950fae01cb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "ebaa6f7a-530e-46a4-a61e-c7a8caf00555",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "05becf46-c78c-409c-af13-fc6675e1fc95",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "defc3572-21b4-4b8d-a4e3-e24b66c962d7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "8073b1e4-ebed-4822-a6df-c1f7fdfae5d9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "fc7e590b-a406-4140-917f-ed45b7760115",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "8083b354-6a6e-4933-ab24-7f0858bed393",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fc2f5da8-5224-4cf7-ab67-4b05e9d7040a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a MBRL-DVD1 $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5ed8e43c-49ea-49ea-960e-a087d7030a2a",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01504",
        "status": "c",
        "type": "g",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00661",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "67d33fc9-40d9-495e-b695-c1f668e95a07",
    "title": "AUC Books Constant Template - AUC-TEMP-ARCHIVES-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.3",
          "isProtected": false,
          "id": "89efd4ea-4ba3-4300-bfd9-35adab58d100",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6106540",
          "isProtected": false,
          "id": "4a4b2e70-580d-42ef-aee8-35bdb898b0db",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "t",
            "BLvl": "m",
            "Entered": "000\\0\\",
            "DtSt": "a",
            "Date1": "ra\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "a6ed6298-1d7a-40c3-b954-e9cef83f0eb4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b2a26eb4-acb3-4c5b-9e5c-dc5e8c923228",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d4a85298-c005-4537-acaa-e8db2fc9c04e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "67938300-be86-41a0-aa13-8d662eb5da1f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ad1abde2-fc7e-4a58-8a32-631177ac5382",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "00fe64bc-b150-4841-9f2e-1d019b7f8995",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "43c0699c-cbf5-41bb-b8d6-78a8404eb324",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "821cc7a5-19b8-4c02-9def-ec9f8fcb850c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$c : $m :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "d7d9866d-d4f3-45ea-838d-b57e3a4b5f80",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "10fe7c06-ce2d-4b5a-8a13-78adfb12757d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 ÙØ«ÙÙØ© Ø£Ø±Ø´ÙÙÙØ©âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "86e08ead-f431-4584-844d-a3fe541ebcce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b1faf583-dace-48a4-a3fe-3148a5c31543",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "70d6a174-4e48-474b-afc4-d29386a28292",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$d :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e8073323-e2e5-4d4d-9eaa-56dadf48bfa2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "351",
          "content": "$b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ad49edfe-eab6-48cb-90d9-8b5579fde810",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "380",
          "content": "$a :",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "b59d53be-910c-4610-acd7-b543207417b4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8e0371b6-13be-4fae-9445-3db2420acbd6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "506",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "91ffc92c-48f6-47e0-8cd7-cfb88a42969e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "520",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e2811885-32aa-474d-9816-fd8d10d7675f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "530",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "983d93fe-3969-4973-9b2f-1322bc9ea9ce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "535",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "3a938551-7c90-4e07-9fdc-6a149cb56b4d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "540",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d867ade3-b1ed-460c-a8e0-7c99518a22be",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "544",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a4e34167-7db6-4d7d-8649-263243636064",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "545",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "45c88e3c-bdfe-4c98-8075-0c70683a5728",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "555",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "7b37cc11-0a39-42dc-a51a-31210b7a7679",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "562",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5e61a92c-d90c-43ec-aca2-cc5bb2b6fa74",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "581",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bbaacc35-0c31-4533-9c72-5bada93b8cf3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "583",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ecfd2e89-3355-4377-a4bc-d465992d5620",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "8deeed2d-0ab6-4304-84ca-155ac49c68a5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "1b05fdf6-371d-4bf9-bc04-894dcd6e23e0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "f7410d99-1806-4473-94d6-49580287eeb3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "51a794b6-f4e0-4503-bc83-cf4cfc545817",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "8e215e0c-bc91-481b-ae48-8716ba28c914",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "cbd5f120-0807-4e54-a123-9b03afd5572d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "cee570bc-386c-4496-af14-94fb9352baf1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "3157df04-958e-4c01-83a6-f5fcf2adae35",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "1734d0c1-881e-4aeb-b7b5-98d462a3d081",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "852",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2faf266e-ecd1-4cd8-80fb-170d99211ea5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "988a3615-9421-4fcc-b205-656dc1229671",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01217",
        "status": "n",
        "type": "t",
        "level": "m",
        "control": "a",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00541",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "d53fbd98-9728-4cd8-9db1-2088975bf919",
    "title": "AUC Books Constant Template - AUC-TEMP-MUSEUMS-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.4",
          "isProtected": false,
          "id": "7f50c5b0-1c4e-4b73-98f9-e58ec06d7099",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6106247",
          "isProtected": false,
          "id": "40ba9a04-860b-4b49-a3e5-37ec9448f503",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "r",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Time": [
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "GPub": "\\",
            "Form": "\\",
            "TMat": "\\",
            "Tech": "\\"
          },
          "isProtected": false,
          "id": "26c29ee6-3ab3-464d-ab5b-5aee89775749",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d15503ad-3eee-4db5-9c93-40eefd316c42",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "eb4fea15-1744-4b35-b262-287d4672e88f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "cfa8c235-12e9-4a20-a4d3-79bb7d5134ff",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6a46a6b9-f5fd-4f52-a6c2-40cbf492d73f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "bab3a11d-2388-4ce3-9f9c-9b6e9b28bdbc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "5b10d8af-e865-419e-b612-a6e20540484a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$c : $m :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "24d04471-9b63-4ea5-aca1-ba0ebb102785",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "3"
          ],
          "isProtected": false,
          "id": "ac92f184-2047-4577-ab5b-b0ac724124f6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ed1aaa5b-b5d8-4dd1-8822-3de5b328c5f9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a : $b : $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b06830eb-741b-4aee-a7a5-b3e801d0aa04",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a   $b : $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4777c950-dbd3-4b86-9a0e-5a39070f48df",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a : $b : $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c4fee09e-ce9d-40d5-a157-43df06fc5dc3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$a : $c : $d : $2 :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d9bad8be-eb33-4a3f-87fb-eaad3887706f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "380",
          "content": "$a :",
          "indicators": [
            "#",
            "\\"
          ],
          "isProtected": false,
          "id": "d6f34e00-9074-4be0-bcad-d09890340707",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "388",
          "content": "$a : $2 :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "a8e332b2-776d-4852-9008-8d14628cf2eb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b60ea317-cb20-4ff7-8822-e9f5a121b1d4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7037e758-ab30-4dac-86cc-3296afbf76e1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a Ø±ÙÙ Ø³Ø¬Ù Ø§ÙÙØ·Ø¹Ø© :âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "afd242f3-af6e-4e12-ac61-c8e6772818f3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙØ²Ù Ø§ÙÙØ·Ø¹Ø© : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "774e836f-76cf-496b-8e5e-e9d28eb58403",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "506",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "afa63ad1-54af-4ccf-b573-b5026a24bb17",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "510",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "1c6bdc91-c7ed-44c1-acaa-4cf871d2fc42",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "520",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4011c3e1-10b7-4e78-8446-bb21aedeb722",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "533",
          "content": "$a : $b : $c : $d : $e :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "33a36622-fea8-41b3-8472-bd4a723630b7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "534",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "baa582de-275e-4839-bc2c-b54a9cc60862",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "541",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "81cb7b56-af81-4aa9-86ae-a89357b24330",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "545",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8a31c165-21f8-43cf-8cf5-5074262d184c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3fb28db9-47c8-4530-8359-eb45a2363720",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "562",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bfceca12-88be-47b6-90fc-94b662ebb69b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "580",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f2cc23ab-13a4-4114-9670-1fb51f887868",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "583",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3e97d202-e541-4b2c-b13d-42fae38bcbe9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "585",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d0c18752-ce67-4ff0-8f8c-03c23ccc7944",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "586",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4de3d0d3-1add-4b80-9cab-9e38d5ff90f2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "b0e55bad-e345-4cf7-a5a0-0055210d68f4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "ce5da329-ec5c-4fe5-b35a-fa83888152a3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "6389200d-4895-491b-9126-f84b0a663d26",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "5bc89fd5-2015-407a-874c-8053d330d538",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "852",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f30805c2-6e2c-4146-8dc7-daca36ff955e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "856",
          "content": "$u :",
          "indicators": [
            "4",
            "\\"
          ],
          "isProtected": false,
          "id": "59e2d84c-4db1-44ba-bd51-6e937e904b7d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8d4a2c27-f6c5-4c39-8133-468a771e4190",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01193",
        "status": "n",
        "type": "r",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00553",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "10ecc322-59a2-4250-a27e-bab6b37c7ec4",
    "title": "AUC Books Constant Template - MBRL-MANUSCRPT-ENG-RDA",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "3dbebc0f-5a2d-4896-923c-f4ef003e8b9a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "7053470",
          "isProtected": false,
          "id": "9279c662-c171-4115-8543-73db633c6689",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "t",
            "BLvl": "m",
            "Entered": "000\\0\\",
            "DtSt": "e",
            "Date1": "ng\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "d399d3b6-c2cd-42e0-b369-b7a3ecb68c46",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "875799a5-c3db-43f8-920b-a1f9f02a9620",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cfaeb41e-f967-4071-8814-fc929169e9fb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "60956e86-5193-4a7d-8f75-1963e2630c69",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "b751458c-f2fa-440f-9195-fca66965a8b7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "c94526ad-1303-4fd3-88fc-32ef11abfe0e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "a006f24a-5c6f-4dd4-970a-172e214d6027",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "3c29b52b-a396-44c8-9901-6b6b2adeca18",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$c :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "3c0d4b8a-6724-4831-9df6-b03e92a2d916",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "efb1239a-276e-4a75-b5bb-5cb896c6d6f3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a text $b txt $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "500f1949-bfdc-41c9-9a8c-af22db85ca58",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ab2bb708-360e-47bf-a29e-332aefcb6c9d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a volume $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6ad1dbe8-8712-4cd3-a286-db362510540d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$a : $c : $d :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "621e8f3a-104c-438f-8c6a-5f3bb6b460eb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "351",
          "content": "$b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "9f0a3f11-34ce-4d8c-9a8b-7d48312680bb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f53f4926-287b-43e2-8cf0-de1449f711d6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "05e6c9eb-8a28-49c7-9357-0116c0a19fca",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "544e7648-571c-4bba-9de0-87268c33f557",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a3784c99-c4f6-4b29-b079-40e48ff96d69",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c750469a-8d39-4e6f-9cdc-35806d42aca0",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "506",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "1c4fa12a-4cd2-4f92-a12f-e78de21a54a8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "530",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "44109a22-985c-45ba-a98c-642d0bacb308",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "535",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "a3a84caf-d57d-45ad-9c58-a4ea16888070",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "540",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "127ec74b-0795-4f79-b83e-8bcf0d6c9e73",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "561",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "684f940f-0653-4aa9-8833-25aa1ddcdb92",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "562",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "45719e78-194d-44c4-ba29-cfbb777622ad",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "563",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "83cbefa5-3fd3-40f9-9359-35faffceefea",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "583",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "404a94d6-635a-449f-9607-72d74fc837d9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "608809dc-6573-4bdd-b286-8a9d7885a939",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "5d9f1595-960c-4153-b281-ef0c5dfd558b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "e5904bd2-4cfe-46ae-88ee-94f627361072",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a : $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f9328d92-8abb-48aa-be36-4a2920471bcc",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00966",
        "status": "c",
        "type": "t",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00457",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "e8fbec53-e73b-45c9-a521-4744454456d8",
    "title": "AUC Books Constant Template - AUC-TEMP-ANALYTIC-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.7",
          "isProtected": false,
          "id": "09e3b874-033d-4d7e-8958-403e8abf0739",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6101356",
          "isProtected": false,
          "id": "48a9cfda-b2ba-40f5-a8f7-18ce4537af4b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "a",
            "Entered": "000\\0\\",
            "DtSt": "a",
            "Date1": "ra\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "5e0772f8-ff3f-4de6-bd7c-858c05f79069",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e349789c-2642-47ec-8135-d92d4b256273",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "58b3f288-967c-4997-b0a1-7ddbc4ee1799",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "7a9bf583-fa3a-4621-9633-e49a0080c4a6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "df2514f1-f3ec-4448-a51d-45252d04afb7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "149e90e6-505d-4beb-8ded-3d1d492f0d6f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "d607f079-975e-43ee-ba39-000c24be3115",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "1e955606-d7c6-4d15-9d5c-23a688e26f0d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5d22c503-7e63-4dbb-84ba-753a66795220",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 Ø¹ÙÙ ØªØ­ÙÙÙÙâªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "81374d2e-958c-4b41-b2c5-798aae8c65b9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a2b2b2fb-8f4f-4c9a-8047-df2dcdfeb2cb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cd56e125-46df-4fda-ae63-e83b3a072ef4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1224767a-b2c5-46a1-955b-a7f28349e6be",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "580",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1bffd76f-2e29-48d8-b19c-ce8d220e3b15",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "b4a28858-2540-4a6b-9847-8549e38c46a2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "ae0560e7-6d28-4850-922b-c6363293cc38",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "81ca4827-4954-4675-ae57-0903ae116bd7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "dc2f8bb8-f7b5-461e-9658-1c663db86c89",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "9320c041-9d3a-4387-a71f-dfb7f814d4b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "08fb984e-3c3e-4f5a-a751-ffed382bd4e4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "8a2b8dbf-055d-45f4-96cc-24161a9efa9d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "7d6c0483-e01d-4968-979f-093219f4a112",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "36b6559c-3988-4705-ae68-0b3257da6505",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "cba076d5-d62c-4397-953f-cf317eecdd83",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "773",
          "content": "$a : $t : $b : $d : $h : $k : $z : $n : $w :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "b7a447f2-d9e3-41c0-903a-c8f7b14ea3bd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "774",
          "content": "$a : $t : $h : $w :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "e0164808-02d9-42f8-8daa-31777f8c5adf",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bccbeac6-6055-41ef-9433-e3b468445a81",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01040",
        "status": "n",
        "type": "a",
        "level": "a",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00397",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "99fe4bb4-d758-4f7b-b45f-a602cc0a42a0",
    "title": "DSPACE_TYPE_Ø®Ø±Ø§Ø¦Ø·",
    "description": "DSPACE_TYPE_Ø®Ø±Ø§Ø¦Ø·",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.2",
          "isProtected": false,
          "id": "63f2b65d-5e8d-4b17-9941-4bc24edd5a0f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367697",
          "isProtected": false,
          "id": "f0194422-1b01-400d-b8da-523390afe3aa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "c3dc63df-1fb7-4db4-90ca-28bf9f99eb0e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b6ac4253-1f31-47cd-93af-0195583a094e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a Ø®Ø±Ø§Ø¦Ø·âªâªâªâª $c 7810fe23-01a6-4ff4-8292-90e467142ee0",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bfcc5897-bb8d-4047-ac1d-81b93ecd0bcd",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00333",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "4644605c-5863-4692-88be-c319bc45bb11",
    "title": "DSPACE_TYPE_Ø¯ÙØ±ÙØ§Øª",
    "description": "DSPACE_TYPE_Ø¯ÙØ±ÙØ§Øª",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.3",
          "isProtected": false,
          "id": "8e65d480-d7eb-4568-b856-728251ceac5d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367701",
          "isProtected": false,
          "id": "5a5b0513-2cc1-401e-9b31-9849d204be83",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "4b2df85d-f5f8-4c2c-a4e9-8a855c312b9d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f965f27a-da10-4340-a97a-cda6b4bb0936",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a Ø¯ÙØ±ÙØ§Øªâªâªâªâª $c 5acab582-b136-4f46-99db-6019df0a0f23",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "6665f9dd-61a9-4136-b88a-bcee920f62e5",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00334",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "27b6e537-fc01-4462-8cb0-905cf10024a0",
    "title": "DSPACE_TYPE_ØµÙØ±",
    "description": "DSPACE_TYPE_ØµÙØ±",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.4",
          "isProtected": false,
          "id": "b9796f8e-b3b8-4940-b98d-e51deded4dfb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367703",
          "isProtected": false,
          "id": "c1f679f0-d49d-4a85-b29d-d4aca7c480a8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "f290fbed-ddc5-4841-9acf-768a53d8306e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e6f5af4f-7051-4ef1-9ff4-d41037e1f75f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a ØµÙØ±âªâªâªâª $c 64425106-6036-4481-bc43-d5f50f68109d",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1298ce58-c4e9-4c42-b6ef-e4ce18e244e1",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00331",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "b9ab58f5-229f-4d85-87a5-c2a569bf9972",
    "title": "DSPACE_TYPE_ÙØ®Ø·ÙØ·Ø§Øª",
    "description": "DSPACE_TYPE_ÙØ®Ø·ÙØ·Ø§Øª",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.3",
          "isProtected": false,
          "id": "a743f942-a7ac-430a-b767-958fb913ee8b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367678",
          "isProtected": false,
          "id": "e3ebc2d5-6038-46c1-84ec-8f75b46f34a9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "07e254be-5a92-4041-9699-b6ef0290e857",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "fe2bd5b9-92f4-4817-a0c4-0c5a3100410c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a ÙØ®Ø·ÙØ·Ø§Øªâªâªâªâª $c e9bbd504-aad8-4e6c-8cdf-e2dcf9ca7326",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "74355042-e55c-4e2f-8146-800d2882b5e4",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00335",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "48a6c6d0-a840-4ed9-b454-4ceea567cdb6",
    "title": "DSPACE_TYPE_Ø¨Ø­ÙØ«",
    "description": "DSPACE_TYPE_Ø¨Ø­ÙØ«",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.3",
          "isProtected": false,
          "id": "ee9eeca8-a421-4f52-91c0-08434112cb16",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367700",
          "isProtected": false,
          "id": "aecf4538-abe5-41f3-b8a1-dc3db9d5996d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "8956f45a-5fb1-4981-bdc7-8c7dea58277f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "01f6e3d6-524b-4fd8-8069-0eb56508d7ba",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "892",
          "content": "$a Ø¨Ø­ÙØ«âªâªâªâª $c 223cf1ee-f6b3-4542-b68c-f8e6b6766732",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "988bda61-ec57-46b2-859b-0312f466f152",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00332",
        "status": "n",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "a",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "f97e9953-1d45-4bf8-b937-7f757f29edb9",
    "title": "AUC -RDA-BOOKS - MBRL_RDA_BOOK",
    "description": "AUC -RDA-BOOKS",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.1",
          "isProtected": false,
          "id": "effb81e1-e906-442b-bb76-8404c5b3a097",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5944688",
          "isProtected": false,
          "id": "b873806b-ea00-4bff-a48f-e257a0724f41",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "200114",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "g",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "a8808c59-691b-440d-98a5-c3a1dbfb2740",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "eabdc6af-7c45-4d81-9ebb-631dfd3171e4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "64a8be25-465c-4357-92d7-024e61653a54",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "49f38a28-e179-41d2-b47f-d21e5ebaed9a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "209290bc-aced-424c-aab2-5fa447302307",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b / $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "057e8157-bbc7-46a2-97e9-2ff470e01f18",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7819d815-3848-4db2-9f89-62d13339bb31",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a  : $b Ø $c : $m :",
          "indicators": [
            "#",
            "1"
          ],
          "isProtected": false,
          "id": "4fa4a5f4-f8b5-4d39-a78c-2af4b3e101cb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a ØµÙØ­Ø© Øâªâªâªâª $c Ø³Ùâªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "224c81f9-584e-4b59-acbd-5197b9eb490b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 ÙØªØ§Ø¨âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d49e0223-f1ee-4dc1-91c0-a2829074f7b4",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4bacbbcc-b395-406e-aa01-d0c677d7d33d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4ecf71ee-da01-4e5a-b047-0d58faad6b88",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0e62144c-fc67-4916-986c-03a7b7c7127b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "24f0b36b-77dc-44fb-806e-d7ce653557b1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "e073c2d6-42da-465b-a533-e86c16b44500",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a : $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "267dd5ae-ce03-451f-8490-ff0317e62bf9",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00718",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00265",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "b9d532d0-bfd2-4daa-a237-3f7375bdd48e",
    "title": "DSPACE_SUBJECT_ÙØºØ© Ø¹Ø±Ø¨ÙØ©",
    "description": "DSPACE_SUBJECT_ÙØºØ© Ø¹Ø±Ø¨ÙØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.1",
          "isProtected": false,
          "id": "fa64454d-1e72-4603-8c0b-6ce8cc3e61e9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367720",
          "isProtected": false,
          "id": "39389d8d-874c-4592-b266-ada4ab1a7a2d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "106fe5b4-1f5f-4725-b4f5-93a8edbf8131",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c99aa4f2-3079-41e5-b151-07510b535514",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a ÙØºØ© Ø¹Ø±Ø¨ÙØ©âªâªâªâª $c 43346a4c-fddd-47af-a5c2-fd3082443db8",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "79cd3902-2d1f-4bc3-8035-cb0c75245947",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00337",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "67ec6177-81d6-4b85-9a2a-de216074ea2e",
    "title": "AUC Books Constant Template - MBRL-MANUSCRIPT-RDA",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115026.2",
          "isProtected": false,
          "id": "373da09d-743b-4b1e-a1a8-6884e7f98722",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "7052978",
          "isProtected": false,
          "id": "1b4b96e3-9f54-4eb5-a724-d1c5c7ea3c82",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "t",
            "BLvl": "m",
            "Entered": "000\\0\\",
            "DtSt": "a",
            "Date1": "ra\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "e1b86603-c1cd-41c6-a330-37ff60c0d84f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "024",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "5cbdc179-4a97-4519-b4e8-ef4434c8eadd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a9699241-60ab-4139-8c74-0a895498bae2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "3f75c542-fc0e-41ef-a4e5-b68faab2dcc7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "7bbd6206-24e8-4205-b09a-be64b90176e7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "c72391f7-1015-48d8-b804-eb24f436cd8f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âªâªâªâª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "a9ac38f2-d9ac-445d-ab01-bfb04ed78a3f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "d2c6a1a2-d037-4001-aacc-a8e67409c54a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "916d31ea-4d17-473d-983d-62d3320d8db9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$c : $m :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "14301146-7617-4d1e-bd76-3c3cb290d879",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "76202ffd-6384-49fd-9346-80680d4ce693",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµâªâªâªâª $b txt $2 rdacontent $3 ÙØ®Ø·ÙØ·Ø©âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b79059f9-ef72-4389-a72d-094136d464ce",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âªâªâªâª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ecadd6a6-4b3c-405b-a909-0e527071a15a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âªâªâªâª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5d82e140-1314-423c-86e9-15f9a9f55f13",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$a : $c : $d :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "08b5a147-a5ac-409f-ade6-f3c4b8390678",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "351",
          "content": "$b :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4b7c8d36-5ca7-4bcd-8083-34c4c1fea521",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f33fa88b-1499-4b27-ad7f-f771bf50e000",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a Ø¢Ø®Ø±Ù : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1345aec9-91d6-401c-9b5c-42242a37c984",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a Ø£ÙÙÙ : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0662391b-7f91-4bf2-83cc-38c6115542f9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙÙØ§Ù Ø§ÙÙØ³Ø® : âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "69fbd840-d6da-4ee7-8d9b-d8509da5eec9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a ÙØ³Ø® :âªâªâªâª",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "af8c0b26-7fef-448a-ae85-75f29eb606ab",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "506",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "5172193a-56c3-41bf-a060-acfc88c70070",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "530",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "78a6e930-cd96-4e44-94cd-9cc68d926896",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "535",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "e99f6718-128e-4e0f-b6ff-d087bab62c31",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "540",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "50df13f9-8624-4671-a538-12dbb51a9101",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "561",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1e695e10-207c-4eea-9d83-519af2c16e75",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "562",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b69c14af-ec5a-4c0d-8f7d-5e71382484e3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "563",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "70af05ad-d97f-476b-987a-062b1d9a3bfe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "583",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "66b6de99-17aa-42f3-9ed7-2bcca08823d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "49215305-06e8-4070-95b7-85c33fc3ac09",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "31b58267-9ede-401b-8297-2eded615c7d7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "913ba6b2-1a22-4e04-bd4e-111fc391572f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "f01dcbfb-7c34-4c26-b6e5-e8b7da2cade1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "83020c8a-4e6b-4de3-a710-e670506ff0f1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "61858b3e-1b9f-44c9-96e5-38e45577270a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "d639fa94-3493-412b-bd69-1878e4628c8d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "956",
          "content": "$a : $x :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c4ec3059-f3d6-41a9-9d00-8772d4595c18",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01204",
        "status": "c",
        "type": "t",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00517",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "3e2525b7-932f-4db1-855f-33144544da63",
    "title": "AUC Books Constant Template - MBRL BOOK ENGLISH",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.7",
          "isProtected": false,
          "id": "d652a09c-bd3c-498f-a3e1-528ba821a500",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6233363",
          "isProtected": false,
          "id": "6ce0891c-a464-4c89-bf29-a28362f99c71",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "000\\0\\",
            "DtSt": "e",
            "Date1": "ng\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "2d09b9a1-c69b-4f3f-abb0-f539a904fa0c",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a 0-6777-6244-5",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "80ef9c2d-9145-4c08-82db-a2d3553da1a1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a AE-DuMBRL $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "03560c54-0718-43d3-ad36-f7153bb47104",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$a : $h :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "060a512a-f635-4ed4-b09d-44b667a2ab55",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "43ebe3ab-65b5-486e-afc8-d1449189ef16",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "5f145e85-2e60-474b-ba42-8ff342d5ac5d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "8fbf28ce-cfad-4846-8503-175fb888f1d2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "fa31d297-244d-4c55-bc2a-0483147c294b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "bba339c1-2204-4dbe-b5e9-6073b68f343b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "cf3eb43b-a497-42a8-8af8-c22a91b6c356",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "ccf16c08-7663-426b-a7aa-46bf3f5b3774",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ab2be02b-f4ac-4bee-8a47-3ecb7b50ddf5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a text $b txt $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7ca4119a-5ae9-44dd-bc02-684088382ddd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "53889071-f1a2-4896-b2f5-dd36787d8eab",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a volume $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "617ae9cf-95d9-4cb8-a599-2d95adfb3750",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "2686aa1d-1251-4484-9bf6-9b05d1d52e04",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f7ac69bc-b9ec-4b3e-b4bb-fe0852228940",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2d7e5701-650e-40b2-ae9c-6d9f430eba27",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "505",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "b0ebc65f-fc2d-42e3-8807-2d5cddf73cbb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f30ec158-76bb-46cc-ba2e-a7d26317e9ba",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "55ef9a41-e37d-44b3-8c4d-c72f11ea29b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "6dd13d76-33e3-4a2e-954e-e1ded7355eb8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "b0343e72-7954-4c78-b677-ef377fb12d23",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "0474aa2c-7545-4371-9dbd-c105e2e26405",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "a3c8b412-a9bf-4122-8519-ea30d4885549",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "94d33faa-c73e-4905-ae93-73ca235da684",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "a3da856f-aba2-4b0a-ac4f-bb316022380a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "f3e18a5b-04c1-4e04-9af1-3334f925eb61",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "954728e2-351e-4771-b243-b90b0de83035",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "ad20d658-ae65-4415-a22b-78b2dc4afd85",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "fba25d66-4e28-4dc3-858b-c9688878718a",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01011",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00445",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "d297d416-67b6-4216-afef-cb2af81471a8",
    "title": "AUC Books Constant Template - AUC-TEMP-BLINDS-PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115713.0",
          "isProtected": false,
          "id": "9537b42f-209c-4b3b-9992-50b1e056b780",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "6738273",
          "isProtected": false,
          "id": "af98a9cc-68c8-4f0b-b6b5-2567af4cbc3e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "210405",
            "DtSt": "s",
            "Date1": "\\\\\\\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "ara",
            "MRec": "\\",
            "Srce": "c",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "f",
            "Form": "f",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "0",
            "Fest": "0",
            "Indx": "0",
            "LitF": "0",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "3bab1a7b-c190-4288-9186-5922d3007463",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ec538bec-6a1a-4503-8bd2-864362391f6b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b ara $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "bcc112d4-8e54-4e51-9bdf-952d7c466b33",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "02795228-a972-44a8-91f5-9e8372886bd8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $2 21 $q SA-RiAUC",
          "indicators": [
            "0",
            "4"
          ],
          "isProtected": false,
          "id": "0fe8d08f-4c95-4a13-94f5-17345df4639f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "090",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8a9808ca-1230-4811-a818-847c810cc226",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e ÙØ¤ÙÙ.âª",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "82cc6356-848f-434c-a849-4c8ecb89ed96",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "991effd8-e1d1-441c-962b-3883def3205e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "6e278fd2-ef61-4494-9575-5e2876b5a800",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "d9a80886-1596-472c-adbd-4d01f627080b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "85f1b753-2414-457a-8d2d-2f74335f8c74",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "c1fbc8be-a743-4b9b-91dc-83522fcb3839",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a ÙØµ ÙÙØ³Ùâª $b tct $2 rdacontent",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "a6894a00-cfec-4fa6-b0a8-af835728fb43",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a Ø¨Ø¯ÙÙ ÙØ³ÙØ·âª $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b90f296d-9ab4-48a7-b569-6d1df315a5fd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a ÙØ¬ÙØ¯âª $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e0714517-15f8-453f-84a0-7d9061920b3e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "340",
          "content": "$d ÙÙØ·Ø© ØµÙØ¨Ø©âª $2 rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5bf2a8ba-db36-4412-9c8d-d424fa717451",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "341",
          "content": "$a ÙÙØ³Ùâª $e Ø¨Ø±Ø§ÙÙâª $2 rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "aca557d9-0a75-4a29-a59c-eb2fbab85036",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "1824874a-06cd-4f27-b3cc-9b3b97ce0181",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "8a4295fa-b9ff-47a4-8b4f-b9774d2743da",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "506",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "156f5fed-39a2-4383-b9ca-c3f66aa27f99",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "520",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "ac0407b6-f05a-49bc-b3d1-f2661ff8b640",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "521",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "afcf6b2d-31c9-4483-9eb8-3cb61113fe63",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e631de01-6cee-4031-8ae2-0de5fe535413",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x : $2 aucnm",
          "indicators": [
            "1",
            "7"
          ],
          "isProtected": false,
          "id": "c3c04269-b8e1-43af-bcfe-4f37ee97b6e9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "4905c880-558a-45c0-9363-be3ccbb7dfdc",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c : $2 aucnm",
          "indicators": [
            "2",
            "7"
          ],
          "isProtected": false,
          "id": "0f960fbe-e9f1-4045-a5ff-3a4fbc19dd7a",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x : $2 aucut",
          "indicators": [
            "0",
            "7"
          ],
          "isProtected": false,
          "id": "e36a1b87-21de-432d-93dd-00ab734cbc44",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "179b4326-80d9-4ddf-88a4-ac89f74d02cb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a ÙØªØ¨ Ø§ÙÙÙÙÙÙÙÙâª $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "63884265-8b75-4bd5-bb73-0cd13409a406",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "a264be7a-b7c4-4127-bcef-34580d4a4d41",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "0f2f65ea-46b6-46d0-a0bb-b4b6ae29ad73",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "949",
          "content": "$a : $d : $i : $j : $n : $u :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2ac79f93-1453-4b33-b8d7-ce7d3a6f3388",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01110",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00457",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "97f87196-5cda-47a0-a3ad-94c2b13bd9ca",
    "title": "AUC Books Constant Template - AUC-ONLINE-ENGLISH PORTAL",
    "description": "Ø§ÙØªÙØ¬Ø§Ù Ø§ÙØ«Ø§Ø¨ØªØ© ÙØªØ³Ø¬ÙÙØ§Øª Ø§ÙÙÙØ±Ø³ Ø§ÙØ¹Ø±Ø¨Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115712.8",
          "isProtected": false,
          "id": "cde3bc9e-dac7-4c26-80aa-d4facfd29df9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "7156510",
          "isProtected": false,
          "id": "4f02cae5-9858-469f-bed8-15eb42ec56ee",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "000\\0\\",
            "DtSt": "e",
            "Date1": "ng\\c",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "2455ab6d-dfe7-47db-9608-9d2cb02c58f6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "020",
          "content": "$a ",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "147e0e6b-858d-47ec-b7b9-71c3896ffd64",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "040",
          "content": "$a SA-RiAUC $b eng $c SA-RiAUC $e rda",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "61026467-20a8-4a77-8536-561243edbf45",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "041",
          "content": "$a : $h :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "1452271f-7e8b-4f3d-bff7-d08dca4d0dd9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "043",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "e80f2c9a-5135-4974-b6c7-427d6477437e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "050",
          "content": "$a : $b :",
          "indicators": [
            "\\",
            "4"
          ],
          "isProtected": false,
          "id": "54da16fb-ffda-4647-953c-e9c1f9dddadb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "082",
          "content": "$a : $b : $q SA-RiAUC",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "7ef631e4-0234-426a-80d9-eb36646298f1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "100",
          "content": "$a : $d : $e author.",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "9ca8d985-34d7-42b6-a9b3-82dc06c00914",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "0f0c62bf-fa6f-48c2-8186-6bdd0e9d3177",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "246",
          "content": "$a : $b :",
          "indicators": [
            "3",
            "\\"
          ],
          "isProtected": false,
          "id": "cc526cc6-02b4-47f7-a940-b47afb139d6d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "250",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "b1a837fd-dd10-4312-81dd-ed5e1edb992f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "264",
          "content": "$a : $b : $c : $m :",
          "indicators": [
            "\\",
            "1"
          ],
          "isProtected": false,
          "id": "a241f16b-275c-4fe2-8e3f-260c19883ef8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "300",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "5e62cc08-df7b-4dff-9c6e-abb7d8a1c3f5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "336",
          "content": "$a text $b txt $2 rdacontent $3 book",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2019766a-3805-417f-9565-7132d0e5b193",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "337",
          "content": "$a unmediated $b n $2 rdamedia",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "7f38804f-c1b4-4a87-87e1-85f97520a3fa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "338",
          "content": "$a volume $b nc $2 rdacarrier",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "1e10daba-de05-41db-afd3-3237dc97a538",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "490",
          "content": "$a :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "9d1a403d-4729-40e6-a5d4-3b9ca91e9aa2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "500",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f62b5945-3146-4f7a-bea3-694abea6d4d9",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "504",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "40785f41-6147-4806-8a37-43b7de15bad8",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "505",
          "content": "$a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "c5e88d2c-649e-4314-97bc-2dfca523b6f7",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "546",
          "content": "$a :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "f69623c3-1f6c-47ce-8f87-4d2233d15ac2",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "600",
          "content": "$a : $d : $x :",
          "indicators": [
            "1",
            "0"
          ],
          "isProtected": false,
          "id": "019fe48f-c644-4e8d-b4ec-3485404fbe52",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "610",
          "content": "$a : $b : $x :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "081568e1-f784-422f-b5fd-55167038336b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "611",
          "content": "$a : $n : $d : $c :",
          "indicators": [
            "2",
            "0"
          ],
          "isProtected": false,
          "id": "8aa2f128-8428-4726-95f7-444b9b1b14b5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "630",
          "content": "$a : $x :",
          "indicators": [
            "0",
            "0"
          ],
          "isProtected": false,
          "id": "3c930766-dc7d-4bb7-b4a0-dff891d7754f",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "6bd983ad-2473-4b46-b17c-66faf4fb7e87",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "650",
          "content": "$a : $x : $y : $z : $v : $2 aucsh",
          "indicators": [
            "\\",
            "7"
          ],
          "isProtected": false,
          "id": "3b8ed04f-b3ef-4ce7-9d5a-ccee234a9562",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "651",
          "content": "$a : $x : $y : $v :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "722f507e-d0d3-49cc-ab93-990b96c031d5",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "700",
          "content": "$i : $a : $q : $d : $e :",
          "indicators": [
            "1",
            "\\"
          ],
          "isProtected": false,
          "id": "42bbf542-5478-4ffa-b84b-6cddb7ab2726",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "710",
          "content": "$i : $a : $b : $e :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "8133c38d-8281-45d7-904e-8178ccd41cfa",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "711",
          "content": "$i : $a : $n : $d : $c :",
          "indicators": [
            "2",
            "\\"
          ],
          "isProtected": false,
          "id": "0ff1bd85-7a7d-4b2b-9316-8bb836f6018d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "730",
          "content": "$i : $a :",
          "indicators": [
            "0",
            "\\"
          ],
          "isProtected": false,
          "id": "a64afeaa-a2a0-4b4e-ab34-e3e49868ecfe",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "830",
          "content": "$a :",
          "indicators": [
            "\\",
            "0"
          ],
          "isProtected": false,
          "id": "cbeb16aa-cbf7-4962-8407-9abbc25413f6",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "01084",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00469",
        "encoding": "1",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "9e6b7378-6869-47f6-b222-2404e13c49f4",
    "title": "DSPACE_SUBJECT_Ø¹ÙÙÙ ØªØ·Ø¨ÙÙÙØ©",
    "description": "DSPACE_SUBJECT_Ø¹ÙÙÙ ØªØ·Ø¨ÙÙÙØ©",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.7",
          "isProtected": false,
          "id": "5c7a0a4d-be8e-43ac-b05c-0a42a990756d",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367713",
          "isProtected": false,
          "id": "98715eef-8d47-4cc5-8b9b-81a446108feb",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "780395d2-0230-46c1-a6e2-7f653923c561",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "44916ffa-d3fb-4b67-9a1c-b258b6a1fcb1",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a Ø¹ÙÙÙ ØªØ·Ø¨ÙÙÙØ©âªâªâªâª $c 7845b636-4335-4fd9-936c-c6eeb54da11a",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "15432248-d0e2-47eb-ae38-93f847c3fdd1",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00340",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "2940d137-ac46-4277-874c-2e46e419ceac",
    "title": "DSPACE_SUBJECT_ÙÙØ³ÙØ© ÙØ¹ÙÙ Ø§ÙÙÙ",
    "description": "DSPACE_SUBJECT_ÙÙØ³ÙØ© ÙØ¹ÙÙ Ø§ÙÙÙ",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.5",
          "isProtected": false,
          "id": "8266bbc3-1e3b-45fe-8458-42cbf61c37c6",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367715",
          "isProtected": false,
          "id": "4ca441a3-d6c5-40b7-87ec-eebb735dd7cd",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "b3966237-4f68-44cf-ad34-58ea5ed98ee3",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "4c2ed47b-75e4-4c85-a539-ccf4a6a23074",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a ÙÙØ³ÙØ© ÙØ¹ÙÙ Ø§ÙÙÙØ³âªâªâªâª $c 4a43b92b-bfde-43d4-a3ef-4cad96a901e3",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2c7055e9-95e6-447c-b9b0-065b8cb4bfad",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00344",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  },
  {
    "module": "MARC_EDITOR",
    "id": "c64873c7-9b6d-4ae6-9f31-92f33d9f7383",
    "title": "DSPACE_SUBJECT_ØªØ§Ø±ÙØ® ÙØªØ±Ø§Ø¬Ù",
    "description": "DSPACE_SUBJECT_ØªØ§Ø±ÙØ® ÙØªØ±Ø§Ø¬Ù",
    "content": {
      "fields": [
        {
          "tag": "005",
          "content": "20250505115024.7",
          "isProtected": false,
          "id": "708f161e-19cb-4a91-b386-7abf5a2f3186",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "002",
          "content": "5367709",
          "isProtected": false,
          "id": "4039f1d0-9bbb-41ab-b814-b23a5a832c8e",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "008",
          "content": {
            "Type": "a",
            "BLvl": "m",
            "Entered": "00\\\\\\a",
            "DtSt": "r",
            "Date1": "a\\c\\",
            "Date2": "\\\\\\\\",
            "Ctry": "\\\\\\",
            "Lang": "\\\\\\",
            "MRec": "\\",
            "Srce": "\\",
            "Ills": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "Audn": "\\",
            "Form": "\\",
            "Cont": [
              "\\",
              "\\",
              "\\",
              "\\"
            ],
            "GPub": "\\",
            "Conf": "\\",
            "Fest": "\\",
            "Indx": "\\",
            "LitF": "\\",
            "Biog": "\\"
          },
          "isProtected": false,
          "id": "a8652962-025a-4cae-9a5a-0af2a7cc2645",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "245",
          "content": "$a : $b : $c :",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "2f222ffe-eb23-478d-b8d1-ecb603c7c64b",
          "_isDeleted": false,
          "_isLinked": false
        },
        {
          "tag": "893",
          "content": "$a ØªØ§Ø±ÙØ® ÙØªØ±Ø§Ø¬Ùâªâªâªâª $c 20183525-3b5e-4657-9dbf-1cac269120a3",
          "indicators": [
            "\\",
            "\\"
          ],
          "isProtected": false,
          "id": "0eb0dbd8-c595-4dc5-8ba6-5ea987a1f387",
          "_isDeleted": false,
          "_isLinked": false
        }
      ],
      "leader": {
        "length": "00340",
        "status": "c",
        "type": "a",
        "level": "m",
        "control": "\\",
        "scheme": "a",
        "indicator_count": "2",
        "sub_count": "2",
        "base_address_data": "00109",
        "encoding": "\\",
        "form": "i",
        "resource": "\\",
        "portion_length": "4",
        "start_portion_length": "5",
        "implement_portion_length": "0",
        "undefined": "0"
      }
    }
  }
]'''
MARC_TEMPLATE_DEFINITIONS = json.loads(MARC_TEMPLATES_JSON)

MARC_TEMPLATE_MODULE_CONFIG = {
    "MARC_EDITOR": {
        "list_config": "recordTemplates",
        "content_config": "recordTemplatesContent"
    },
    "MARC_AUTHORITY_EDITOR": {
        "list_config": "recordAuthorityTemplates",
        "content_config": "recordAuthorityTemplatesContent"
    },
}

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

DEFAULT_TIMEOUT = 60

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

    templates_by_module = {}
    for template_def in MARC_TEMPLATE_DEFINITIONS:
        module = template_def.get("module")
        if not module:
            continue
        templates_by_module.setdefault(module, []).append(template_def)

    created_templates = set()
    updated_templates = set()

    for module, templates in templates_by_module.items():
        module_config = MARC_TEMPLATE_MODULE_CONFIG.get(module)
        if not module_config:
            logging.warning("No MARC template config mapping found for module %s", module)
            continue

        list_config = module_config["list_config"]
        content_config = module_config["content_config"]

        list_query = (
            f"{okapi}/configurations/entries?query=(module=={module} and "
            f"configName=={list_config})"
        )

        try:
            list_resp = requests.get(list_query, headers=headers)
        except Exception as exc:
            logging.error("Failed to fetch %s templates list: %s", module, exc)
            return False, f"{module} list fetch failed: {exc}"

        if list_resp.status_code != 200:
            logging.error(
                "Cannot fetch %s templates: %s - %s",
                module,
                list_resp.status_code,
                list_resp.text[:200]
            )
            return False, f"{module} HTTP {list_resp.status_code}"

        list_data = list_resp.json()
        list_entries = list_data.get("configs") or []
        list_entry_id = None
        existing_templates = []
        if list_entries:
            list_entry = list_entries[0]
            list_entry_id = list_entry.get("id")
            try:
                existing_templates = json.loads(list_entry.get("value") or "[]")
            except json.JSONDecodeError:
                existing_templates = []

        desired_meta = {}
        for template_def in templates:
            template_id = template_def.get("id")
            if not template_id:
                continue
            meta = {"id": template_id}
            title = template_def.get("title")
            description = template_def.get("description")
            if title is not None:
                meta["title"] = title
            if description is not None:
                meta["description"] = description
            desired_meta[template_id] = meta

        updated_meta_list = []
        handled_ids = set()
        meta_changed = False

        for existing_meta in existing_templates:
            template_id = existing_meta.get("id")
            if template_id in desired_meta:
                desired_entry = desired_meta[template_id]
                if existing_meta != desired_entry:
                    meta_changed = True
                    updated_meta_list.append(desired_entry)
                    display_name = desired_entry.get("title") or template_id
                    updated_templates.add(f"{module}:{display_name}")
                else:
                    updated_meta_list.append(existing_meta)
                handled_ids.add(template_id)
            else:
                updated_meta_list.append(existing_meta)

        for template_id, meta in desired_meta.items():
            if template_id not in handled_ids:
                meta_changed = True
                updated_meta_list.append(meta)
                display_name = meta.get("title") or template_id
                created_templates.add(f"{module}:{display_name}")

        if meta_changed:
            templates_payload = {
                "module": module,
                "configName": list_config,
                "enabled": True,
                "value": json.dumps(updated_meta_list, ensure_ascii=False)
            }

            if list_entry_id:
                await async_request(
                    "PUT",
                    f"{okapi}/configurations/entries/{list_entry_id}",
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

        for template_def in templates:
            template_id = template_def.get("id")
            if not template_id:
                continue

            content_query = (
                f"{okapi}/configurations/entries?query=(module=={module} and "
                f"configName=={content_config} and code=={template_id})"
            )

            try:
                content_resp = requests.get(content_query, headers=headers)
            except Exception as exc:
                logging.error(
                    "Failed to fetch %s template content %s: %s",
                    module,
                    template_id,
                    exc
                )
                return False, f"{module}:{template_id} content fetch failed: {exc}"

            if content_resp.status_code != 200:
                logging.error(
                    "Cannot fetch %s template content %s: %s - %s",
                    module,
                    template_id,
                    content_resp.status_code,
                    content_resp.text[:200]
                )
                return False, f"{module}:{template_id} HTTP {content_resp.status_code}"

            existing_configs = content_resp.json().get('configs') or []
            payload = {
                "module": module,
                "configName": content_config,
                "code": template_id,
                "enabled": True,
                "value": json.dumps(template_def.get('content') or {}, ensure_ascii=False)
            }

            display_name = template_def.get("title") or template_id

            if existing_configs:
                config_id = existing_configs[0].get('id')
                try:
                    existing_value = json.loads(existing_configs[0].get('value') or '{}')
                except json.JSONDecodeError:
                    existing_value = {}

                if existing_value != (template_def.get('content') or {}):
                    await async_request(
                        "PUT",
                        f"{okapi}/configurations/entries/{config_id}",
                        headers=headers,
                        data=json.dumps(payload)
                    )
                    updated_templates.add(f"{module}:{display_name}")
                continue

            await async_request(
                "POST",
                f"{okapi}/configurations/entries",
                headers=headers,
                data=json.dumps(payload)
            )
            created_templates.add(f"{module}:{display_name}")

    if created_templates or updated_templates:
        created_only = sorted(created_templates)
        updated_only = sorted(updated_templates - created_templates)
        messages = []
        if created_only:
            messages.append(f"Created {len(created_only)}: {', '.join(created_only)}")
        if updated_only:
            messages.append(f"Updated {len(updated_only)}: {', '.join(updated_only)}")
        return True, " | ".join(messages)

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
        types_response = requests.get(instance_types_url, headers=headers, timeout=DEFAULT_TIMEOUT)
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
    
    response = requests.post(url, headers=headers, json=data, timeout=DEFAULT_TIMEOUT)
    
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
                    query_response = requests.get(query_url, headers=headers, timeout=DEFAULT_TIMEOUT)
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


def fetch_marc_templates_status():
    tenant, okapi, token = _get_connection_details()
    if not tenant:
        return False, {"error": "Missing tenant info"}

    headers = {"x-okapi-tenant": tenant, "x-okapi-token": token}
    status = {}
    overall_success = True

    templates_by_module = {}
    for template in MARC_TEMPLATE_DEFINITIONS:
        module = template.get("module")
        if not module:
            continue
        templates_by_module.setdefault(module, 0)
        templates_by_module[module] += 1

    for module, module_cfg in MARC_TEMPLATE_MODULE_CONFIG.items():
        list_query = (
            f"{okapi}/configurations/entries?query=(module=={module} and "
            f"configName=={module_cfg['list_config']})"
        )

        try:
            resp = requests.get(list_query, headers=headers)
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

        import html
        escaped_log = html.escape(output_log)

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
                <pre>{escaped_log}</pre>
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