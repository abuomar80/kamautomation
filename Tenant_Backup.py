import requests
import json
from legacy_session_state import legacy_session_state

legacy_session_state()


def backup(headers, okapi):
    ends = ['/groups?limit=1000', '/service-points?limit=100',
            '/fixed-due-date-schedule-storage/fixed-due-date-schedules?limit=1000', '/loan-types?limit=500',
            '/loan-policy-storage/loan-policies?limit=100',
            '/fixed-due-date-schedule-storage/fixed-due-date-schedules?limit=100',
            '/request-policy-storage/request-policies?limit=100', '/overdue-fines-policies?limit=100',
            '/lost-item-fees-policies?limit=100', '/templates?query=active==true&limit=100',
            '/patron-notice-policy-storage/patron-notice-policies?limit=100', '/staff-slips-storage/staff-slips',
            '/circulation/rules', '/configurations/entries?limit=500',
            '/calendar/periods?limit=1000', '/alternative-title-types?limit=1000', '/classification-types?limit=1000',
            '/contributor-types?limit=1000', '/instance-formats?limit=1000', '/instance-note-types?limit=1000',
            '/instance-statuses?limit=1000', '/modes-of-issuance?limit=1000', '/nature-of-content-terms?limit=1000',
            '/identifier-types?limit=1000', '/instance-types?limit=1000', '/holdings-note-types?limit=1000',
            '/holdings-sources?limit=1000', '/holdings-types?limit=1000', '/ill-policies?limit=1000',
            '/item-note-types?limit=1000', '/loan-types?limit=1000', '/material-types?limit=1000']
    keys = ['usergroups', 'servicepoints']
    allResults = []
    for endpoint in ends:
        urlGet = f"{okapi}{endpoint}"
        try:
            responseVar = requests.get(urlGet, headers=headers, timeout=30)
        except requests.RequestException as exc:
            allResults.append(
                {
                    "endpoint": endpoint,
                    "status": "request_failed",
                    "error": str(exc),
                }
            )
            continue

        if responseVar.status_code != 200:
            allResults.append(
                {
                    "endpoint": endpoint,
                    "status": responseVar.status_code,
                    "error": responseVar.text,
                }
            )
            continue

        try:
            responseJson = responseVar.json()
        except json.JSONDecodeError:
            allResults.append(
                {
                    "endpoint": endpoint,
                    "status": responseVar.status_code,
                    "error": "Invalid JSON in response",
                    "raw": responseVar.text,
                }
            )
            continue

        allResults.append(
            {
                "endpoint": endpoint,
                "status": responseVar.status_code,
                "data": responseJson,
            }
        )

    # for b in allResults:
    #     if 'metadata' in b:
    #         del (b['metadata'])

    return json.dumps(allResults, sort_keys=False, indent=4)

