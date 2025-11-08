import itertools
import json
from collections import defaultdict
from pathlib import Path

from permissions import (
    Acquisition,
    admins,
    apiperm,
    cataloging,
    circ,
    fullperms,
    search,
    sip,
    sipperm,
)

DOC_PERMISSION_LISTS = [
    fullperms,
    apiperm,
    sipperm,
    circ,
    Acquisition,
    cataloging,
    admins,
    search,
    sip,
]


def load_tenant_permissions(perms_path: Path) -> set[str]:
    with perms_path.open(encoding="utf-8") as file:
        data = json.load(file)

    tenant_permissions: set[str] = set()
    for entry in data.get("permissions", []):
        permission_name = entry.get("permissionName")
        if permission_name:
            tenant_permissions.add(permission_name)

        sub_permissions = entry.get("subPermissions") or []
        for sub_permission in sub_permissions:
            if sub_permission:
                tenant_permissions.add(sub_permission)

    return tenant_permissions


def collect_doc_permissions() -> set[str]:
    doc_permissions = itertools.chain.from_iterable(DOC_PERMISSION_LISTS)
    return {permission for permission in doc_permissions if permission}


def build_permission_sets(doc_permissions: set[str], tenant_permissions: set[str]):
    matched_permissions = doc_permissions & tenant_permissions

    grouped_permissions: dict[str, list[str]] = defaultdict(list)
    for permission in sorted(matched_permissions):
        prefix = permission.split(".", 1)[0] if "." in permission else permission
        grouped_permissions[prefix].append(permission)

    permission_sets = []
    for prefix, sub_permissions in sorted(grouped_permissions.items()):
        permission_sets.append(
            {
                "permissionName": f"docs.{prefix}",
                "displayName": f"Docs - {prefix}",
                "mutable": True,
                "subPermissions": sub_permissions,
            }
        )

    permission_sets.append(
        {
            "permissionName": "Naseej",
            "displayName": "Naseej",
            "mutable": True,
            "subPermissions": sorted(tenant_permissions),
        }
    )

    return permission_sets, matched_permissions


def main():
    perms_path = Path("perms.json")
    output_path = Path("docs_permission_sets.json")

    tenant_permissions = load_tenant_permissions(perms_path)
    doc_permissions = collect_doc_permissions()

    permission_sets, matched_permissions = build_permission_sets(
        doc_permissions, tenant_permissions
    )

    output = {
        "generated_from": "permissions.py doc lists",
        "matching_tenant_permissions": len(matched_permissions),
        "tenant_permissions_total": len(tenant_permissions),
        "permission_sets": permission_sets,
    }

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print(
        f"Wrote {len(permission_sets)} permission sets "
        f"with {len(matched_permissions)} matched permissions "
        f"to {output_path}"
    )


if __name__ == "__main__":
    main()

