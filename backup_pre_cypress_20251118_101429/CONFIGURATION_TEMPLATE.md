# Configuration Templates Guide

This document provides templates and examples for configuring various aspects of FOLIO tenants using the automation tool.

## 📊 Excel Template Structure

When using **Advanced Configuration**, create an Excel workbook with the following sheets:

---

## 1. Material Types Sheet

**Columns:**
- `name` (required): Material type name
- `source` (optional): Source (default: "System")

**Example:**
```
name        | source
------------|--------
Book        | System
Journal     | System
DVD         | System
E-Book      | System
```

---

## 2. Statistical Codes Sheet

### Statistical Code Types

**Columns:**
- `name` (required): Code type name
- `source` (optional): Source (default: "System")

**Example:**
```
name           | source
---------------|--------
Collection     | System
Branch         | System
Subject        | System
```

### Statistical Codes

**Columns:**
- `code` (required): Statistical code
- `name` (required): Code name
- `statisticalCodeTypeId` (required): UUID of the code type

**Example:**
```
code | name                    | statisticalCodeTypeId
-----|-------------------------|----------------------
REF  | Reference Collection    | [UUID from code type]
CIRC | Circulating Collection  | [UUID from code type]
```

**Note:** You must create Statistical Code Types first, then use their UUIDs in the Codes sheet.

---

## 3. User Groups Sheet

**Columns:**
- `group` (required): User group name
- `desc` (optional): Description
- `expirationOffsetInDays` (optional): Expiration offset in days

**Example:**
```
group     | desc              | expirationOffsetInDays
----------|-------------------|-----------------------
Faculty   | Faculty members   | 365
Student   | Students          | 180
Staff     | Staff members     | 365
Undergrad | Undergraduate     | 120
Grad      | Graduate          | 365
```

---

## 4. Location Hierarchy Sheet

**Structure:**
Create locations in hierarchical order: Institution → Campus → Library → Location

**Columns (for each level):**
- `name` (required): Location name
- `code` (required): Location code
- `institutionId` (required for Campus/Library/Location): UUID of parent institution
- `campusId` (required for Library/Location): UUID of parent campus
- `libraryId` (required for Location): UUID of parent library
- `servicePointId` (optional for Location): Primary service point UUID
- `displayName` (optional): Display name

**Example Structure:**

### Institutions
```
name     | code
---------|--------
Main Lib | MAIN
```

### Campuses
```
name          | code | institutionId
--------------|------|--------------
Central       | CENT | [Institution UUID]
```

### Libraries
```
name         | code | campusId
-------------|------|----------
Main Library | MAIN | [Campus UUID]
```

### Locations
```
name          | code | libraryId          | servicePointId | displayName
--------------|------|-------------------|----------------|------------
Stacks        | STK  | [Library UUID]     | [SP UUID]      | Stacks
Reference     | REF  | [Library UUID]     | [SP UUID]      | Reference
```

**Important:** Create locations in this order:
1. Institutions
2. Campuses (link to Institution)
3. Libraries (link to Campus)
4. Locations (link to Library)

---

## 5. Departments Sheet

**Columns:**
- `name` (required): Department name
- `code` (optional): Department code

**Example:**
```
name          | code
--------------|------
Main          | main
IT            | it
Acquisitions  | acq
Cataloging    | cat
```

---

## 6. Calendar Sheet

**Columns:**
- `servicePointId` (required): Service point UUID
- `startDate` (required): Start date (YYYY-MM-DD)
- `endDate` (required): End date (YYYY-MM-DD)
- `name` (required): Calendar period name

**Example:**
```
servicePointId        | startDate   | endDate     | name
----------------------|-------------|-------------|-------------
[Service Point UUID]  | 2024-01-01  | 2024-12-31  | Academic Year 2024
```

---

## 7. Calendar Exceptions Sheet

**Columns:**
- `servicePointId` (required): Service point UUID
- `name` (required): Exception name
- `startDate` (required): Start date (YYYY-MM-DD)
- `endDate` (required): End date (YYYY-MM-DD)
- `allDay` (optional): true/false
- `openings` (optional): Opening hours JSON array

**Example:**
```
servicePointId        | name            | startDate   | endDate     | allDay
----------------------|-----------------|-------------|-------------|-------
[Service Point UUID]  | New Year Holiday| 2024-01-01  | 2024-01-01  | true
```

---

## 8. Column Configuration Sheet

For custom field mappings (advanced use).

**Columns:**
- `fieldName`: Custom field name
- `label`: Display label
- `type`: Field type
- `required`: true/false

---

## 👥 User Import Template

For **Users Import**, create an Excel file with these columns:

**Required Columns:**
- `username`: Unique username
- `personal.firstName`: First name
- `personal.lastName`: Last name
- `patronGroup`: Patron group UUID

**Common Columns:**
- `barcode`: User barcode
- `personal.email`: Email address
- `personal.phone`: Phone number
- `personal.dateOfBirth`: Date of birth (YYYY-MM-DD)
- `personal.addresses.addressLine1`: Address line 1
- `personal.addresses.city`: City
- `personal.addresses.postalCode`: Postal code
- `departments`: Department UUID (comma-separated for multiple)
- `expirationDate`: Account expiration date (YYYY-MM-DD)

**Example:**
```
username | personal.firstName | personal.lastName | patronGroup          | barcode   | personal.email
---------|-------------------|-------------------|---------------------|-----------|------------------
john.doe | John              | Doe               | [Patron Group UUID] | 123456789 | john@example.com
jane.smith| Jane             | Smith             | [Patron Group UUID] | 987654321 | jane@example.com
```

---

## 📙 Circulation Loans Import Template

For **Circulation Loans Import**, create an Excel file with these exact columns:

**Required Columns:**
- `BARCODE`: Item barcode
- `P_BARCODE`: Patron barcode (username can also be used)
- `LOAN_DATE`: Loan date (format: **dd-mm-yyyy**)
- `DUE_DATE`: Due date (format: **dd-mm-yyyy**)
- `SERVICE_POINT_ID`: Service point UUID

**Example:**
```
BARCODE    | P_BARCODE  | LOAN_DATE   | DUE_DATE    | SERVICE_POINT_ID
-----------|------------|-------------|-------------|------------------
1234567890 | 987654321  | 01-01-2024  | 15-01-2024  | [Service Point UUID]
2345678901 | 876543210  | 02-01-2024  | 16-01-2024  | [Service Point UUID]
```

**Important Notes:**
- Date format must be exactly **dd-mm-yyyy** (e.g., 15-01-2024)
- Item and patron must exist in FOLIO
- Service point must exist and be valid UUID
- Items must be available for checkout (not already checked out)

---

## 🔑 UUID Lookup

Many templates require UUIDs. Here's how to find them:

### In FOLIO UI:
1. Navigate to the settings page (e.g., Settings → Users → Patron Groups)
2. Open the record you need
3. Check the browser URL - it contains the UUID
4. Or use browser developer tools to inspect the API call

### Using API:
```bash
# Example: Get patron groups
curl -X GET "https://okapi.medad.com/groups?limit=1000" \
  -H "x-okapi-tenant: your_tenant" \
  -H "x-okapi-token: your_token"
```

### In This Tool:
- After connecting to tenant, use the various pages to view and copy UUIDs
- The tool displays UUIDs in the interface when viewing entities

---

## ✅ Validation Checklist

Before importing, verify:

- [ ] All required columns are present
- [ ] Column names match exactly (case-sensitive)
- [ ] UUIDs are valid and exist in FOLIO
- [ ] Date formats are correct (dd-mm-yyyy for loans, YYYY-MM-DD for calendars)
- [ ] No empty required fields
- [ ] Excel file is .xlsx format
- [ ] Data types are correct (numbers, text, dates)

---

## 🎯 Best Practices

1. **Start Small**: Test with 5-10 records before bulk import
2. **Backup First**: Always backup tenant before major imports
3. **Verify Data**: Review Excel data before importing
4. **Check Relationships**: Ensure parent records exist (e.g., Institution before Campus)
5. **Use Valid UUIDs**: Double-check all UUIDs are correct
6. **Date Formats**: Pay special attention to date formats
7. **Test Environment**: Test in non-production first

---

## 📞 Support

If you encounter issues with templates:
1. Check error messages carefully
2. Verify column names match exactly
3. Review the examples in this document
4. Contact KAM Support Team: kam@naseej.com

---

**Last Updated**: 2024

