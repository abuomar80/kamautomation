"""
Excel Template Generator for Advanced Configuration
This module creates a downloadable Excel template with all required sheets and columns
"""
import pandas as pd
import streamlit as st
from io import BytesIO

def generate_excel_template():
    """
    Generates an Excel template file with all required sheets and sample data
    Returns: BytesIO object containing the Excel file
    """
    # Create an Excel writer object
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        
        # Sheet 1: Material_Types
        material_types_df = pd.DataFrame({
            'Legacy System': ['Example Legacy Type 1', 'Example Legacy Type 2'],
            'Description': ['Description for type 1', 'Description for type 2'],
            'Medad': ['Book', 'Journal']
        })
        material_types_df.to_excel(writer, sheet_name='Material_Types', index=False)
        
        # Sheet 2: Statistical_Codes
        statistical_codes_df = pd.DataFrame({
            'Medad Statistical Type': ['Collection', 'Branch'],
            'Medad Statistical Code': ['REF', 'MAIN']
        })
        statistical_codes_df.to_excel(writer, sheet_name='Statistical_Codes', index=False)
        
        # Sheet 3: Item_status
        # Note: Item_status sheet may not be actively used, but it's required
        item_status_df = pd.DataFrame({
            'Status': ['Available', 'Checked out', 'On order'],
            'Code': ['Available', 'Checked out', 'On order']
        })
        item_status_df.to_excel(writer, sheet_name='Item_status', index=False)
        
        # Sheet 4: User_groups
        # User groups only need: Legacy System (optional), Description (optional, defaults to Medad), Medad (required - Patron group name)
        # Departments are separate and loaded from Department sheet
        user_groups_df = pd.DataFrame({
            'Legacy System': ['Example Legacy Group 1', 'Example Legacy Group 2', 'Example Legacy Group 3'],
            'Description': ['Faculty members', 'Students', 'Staff members'],
            'Medad': ['Faculty', 'Student', 'Staff']
        })
        user_groups_df.to_excel(writer, sheet_name='User_groups', index=False)
        
        # Sheet 5: Location
        location_df = pd.DataFrame({
            'ServicePoints name': ['Main Library Desk', 'Reference Desk'],
            'ServicePoints Codes': ['MLD', 'REF'],
            'InstitutionsName': ['Main Institution', 'Main Institution'],
            'InstitutionsCodes': ['MI', 'MI'],
            'CampusNames': ['Main Campus', 'Main Campus'],
            'CampusCodes': ['MC', 'MC'],
            'LibrariesName': ['Main Library', 'Main Library'],
            'LibrariesCodes': ['ML', 'ML'],
            'LocationsName': ['Main Library Desk', 'Reference Desk'],
            'LocationsCodes': ['MLD', 'REF']
        })
        location_df.to_excel(writer, sheet_name='Location', index=False)
        
        # Sheet 6: Calendar
        calendar_df = pd.DataFrame({
            'ServicePoints name': ['Main Library Desk'],
            'start': ['09:00'],
            'end': ['17:00']
        })
        calendar_df.to_excel(writer, sheet_name='Calendar', index=False)
        
        # Sheet 7: Calendar Exceptions
        calendar_exceptions_df = pd.DataFrame({
            'ServicePoints name': ['Main Library Desk'],
            'name': ['New Year Holiday'],
            'startDate': ['2024-01-01'],
            'endDate': ['2024-01-01'],
            'allDay': [True]
        })
        calendar_exceptions_df.to_excel(writer, sheet_name='Calendar Exceptions', index=False)
        
        # Sheet 8: Department (optional - departments can also be defined in User_groups sheet)
        # This sheet is kept for backward compatibility but departments in User_groups will be created automatically
        department_df = pd.DataFrame({
            'Name': ['Main Department', 'Reference Department'],
            'Code': ['MAIN', 'REF']
        })
        department_df.to_excel(writer, sheet_name='Department', index=False)
        
        # Sheet 9: FeeFineOwner
        # Service Points should be entered as labels (names), not UUIDs
        # Use "ALL" to assign to all service points
        fee_fine_owner_df = pd.DataFrame({
            'Service Points': ['Main Library Desk', 'ALL'],
            'Owner': ['1', '2']
        })
        fee_fine_owner_df.to_excel(writer, sheet_name='FeeFineOwner', index=False)
        
        # Sheet 10: FeeFine
        # owner should reference the owner value from FeeFineOwner sheet
        # feeFineType: type identifier (string)
        # amountWithoutVat: numeric amount
        # vat: VAT rate (optional, numeric)
        # automatic: boolean (true/false)
        # id: optional UUID (leave empty to auto-generate)
        fee_fine_df = pd.DataFrame({
            'feeFineType': ['1', '2'],
            'amountWithoutVat': [5.0, 10.0],
            'vat': [0.05, 0.10],
            'owner': ['1', '2'],
            'automatic': [False, True],
            'id': ['', '']  # Leave empty to auto-generate
        })
        fee_fine_df.to_excel(writer, sheet_name='FeeFine', index=False)
        
        # Sheet 11: Waives
        # nameReason: reason for waiving (required)
        # id: optional UUID (leave empty to auto-generate)
        # Each row creates one waive record
        waives_df = pd.DataFrame({
            'nameReason': ['Manager Approval', 'Lost Item Found'],
            'id': ['', '']  # Leave empty to auto-generate
        })
        waives_df.to_excel(writer, sheet_name='Waives', index=False)
        
        # Sheet 12: PaymentMethods
        # nameMethod: payment method name (required)
        # allowedRefundMethod: boolean (optional, default: false)
        # owner: references Owner from FeeFineOwner sheet (required)
        # id: optional UUID (leave empty to auto-generate)
        # Each row creates one payment method record
        payment_methods_df = pd.DataFrame({
            'nameMethod': ['cash', 'credit card'],
            'allowedRefundMethod': [False, True],
            'owner': ['1', '2'],
            'id': ['', '']  # Leave empty to auto-generate
        })
        payment_methods_df.to_excel(writer, sheet_name='PaymentMethods', index=False)
        
        # Sheet 13: Refunds
        # nameReason: reason for refund (required)
        # id: optional UUID (leave empty to auto-generate)
        # Each row creates one refund record
        refunds_df = pd.DataFrame({
            'nameReason': ['error', 'duplicate payment'],
            'id': ['', '']  # Leave empty to auto-generate
        })
        refunds_df.to_excel(writer, sheet_name='Refunds', index=False)
        
        # Sheet 14: LoanPolicies
        # Complex structure with nested objects for loansPolicy and renewalsPolicy
        # name: policy name (required)
        # description: policy description (optional)
        # loanable: boolean (true/false, default: true)
        # renewable: boolean (true/false, default: true)
        # profileId: loan profile ID (e.g., "Rolling", default: "Rolling")
        # periodDuration: loan period duration in days/weeks/months (numeric)
        # periodIntervalId: period interval ("Days", "Weeks", "Months")
        # closedLibraryDueDateManagementId: closed library due date management (e.g., "END_OF_THE_NEXT_OPEN_DAY")
        # gracePeriodDuration: grace period duration (numeric)
        # gracePeriodIntervalId: grace period interval ("Days", "Weeks", "Months")
        # itemLimit: maximum number of items (numeric, as string)
        # numberAllowed: number of renewals allowed (numeric, as string)
        # renewFromId: renewal from date ("CURRENT_DUE_DATE" or "SYSTEM_DATE")
        # id: optional UUID (leave empty to auto-generate)
        loan_policies_df = pd.DataFrame({
            'name': ['Standard Loan Policy', 'Short Term Loan Policy'],
            'description': ['Standard loan policy for regular items', 'Short term loan policy for high-demand items'],
            'loanable': [True, True],
            'renewable': [True, True],
            'profileId': ['Rolling', 'Rolling'],
            'periodDuration': [15, 7],
            'periodIntervalId': ['Days', 'Days'],
            'closedLibraryDueDateManagementId': ['END_OF_THE_NEXT_OPEN_DAY', 'END_OF_THE_NEXT_OPEN_DAY'],
            'gracePeriodDuration': [3, 1],
            'gracePeriodIntervalId': ['Days', 'Days'],
            'itemLimit': ['5', '3'],
            'numberAllowed': ['3', '1'],
            'renewFromId': ['CURRENT_DUE_DATE', 'CURRENT_DUE_DATE'],
            'id': ['', '']  # Leave empty to auto-generate
        })
        loan_policies_df.to_excel(writer, sheet_name='LoanPolicies', index=False)
    
    output.seek(0)
    return output

def download_template_button():
    """
    Creates a download button in Streamlit for the Excel template
    Generates a fresh template with all 14 sheets including:
    Material_Types, Statistical_Codes, Item_status, User_groups, Location, 
    Calendar, Calendar Exceptions, Department, FeeFineOwner, FeeFine, 
    Waives, PaymentMethods, Refunds, LoanPolicies
    """
    # Generate fresh template each time (no caching)
    template_file = generate_excel_template()
    # Get the bytes data - this ensures we're not passing a cached BytesIO object
    template_bytes = template_file.getvalue()
    
    # Add version to filename to help with browser caching issues
    import datetime
    version = datetime.datetime.now().strftime("%Y%m%d")
    
    st.download_button(
        label="📥 Download Excel Template (14 Sheets)",
        data=template_bytes,
        file_name=f"Advanced_Configuration_Template_v{version}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Download the Excel template with all 14 required sheets including Waives, PaymentMethods, Refunds, and LoanPolicies"
    )
