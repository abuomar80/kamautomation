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
    
    output.seek(0)
    return output

def download_template_button():
    """
    Creates a download button in Streamlit for the Excel template
    """
    template_file = generate_excel_template()
    st.download_button(
        label="📥 Download Excel Template",
        data=template_file,
        file_name="Advanced_Configuration_Template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Download the Excel template with all required sheets and sample columns"
    )
