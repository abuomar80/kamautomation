from datetime import date
import streamlit as st
import requests as re
import pandas as pd
import json
from Upload import upload
from legacy_session_state import legacy_session_state

legacy_session_state()

# Initialize tenant-related session state variables if not set
# Check both widget-bound keys and copied keys (from form submission)
# Use .get() to safely check and initialize values
if not st.session_state.get('tenant'):
    st.session_state['tenant'] = st.session_state.get('tenant_name', '')
if not st.session_state.get('okapi'):
    st.session_state['okapi'] = st.session_state.get('okapi_url', '')
if not st.session_state.get('token'):
    st.session_state['token'] = st.session_state.get('token', '')

# Initialize endpoints
services_endpoint = "/service-points"
calendar_endpoint = "/calendar/calendars"

if st.session_state.get('allow_tenant'):
    # Try widget-bound keys first, then fallback to copied keys
    okapi_url = st.session_state.get('okapi') or st.session_state.get('okapi_url')
    tenant_id = st.session_state.get('tenant') or st.session_state.get('tenant_name')
    token = st.session_state.get('token')
    
    if okapi_url and tenant_id and token:
        headers = {"x-okapi-tenant": f"{tenant_id}", "x-okapi-token": f"{token}"}
    else:
        headers = None
else:
    headers = None
    okapi_url = None

def calendar():
    if not headers:
        st.error("⚠️ Tenant connection information is missing. Please go back to Tenant page and connect again.")
        return
    
    File = upload('Calendar')
    df = pd.DataFrame(File)
    todays_date = date.today()
    days = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    
    st.subheader("Calendar Configuration")
    st.caption("Select days and times, then create calendar for all service points in the system")
    
    checkbox_statusses = []
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Select Days:**")
        for day in days:
            checkbox_statusses.append(st.checkbox(day, key=day))
    
    with col2:
        st.write("**Operating Hours:**")
        # Get start and end times from first row, or use defaults
        default_start = df.iloc[0]['start'] if not df.empty and 'start' in df.columns else '09:00'
        default_end = df.iloc[0]['end'] if not df.empty and 'end' in df.columns else '17:00'
        
        start_time = st.text_input("Start Time (HH:MM)", value=default_start, key='cal_start_time')
        end_time = st.text_input("End Time (HH:MM)", value=default_end, key='cal_end_time')
    
    # Calendar name
    cal_name = st.text_input("Calendar Name", value=f"Default Calendar {todays_date.year}", key='cal_name')
    
    # Date range
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date", value=todays_date, key='cal_start_date')
    with col2:
        end_date = st.date_input("End Date", value=date(todays_date.year + 1, 12, 31), key='cal_end_date')
    
    create_cal_btn = st.button('Create Calendar for All Service Points', type='primary')
    
    if create_cal_btn:
        # Get selected days
        selected_days = []
        for i, day in enumerate(days):
            if checkbox_statusses[i]:
                selected_days.append(day)
        
        if not selected_days:
            st.warning("⚠️ Please select at least one day!")
            return
        
        if not start_time or not end_time:
            st.warning("⚠️ Please enter start and end times!")
            return
        
        # Get all service points in the system
        try:
            with st.spinner('Fetching all service points...'):
                sp_response = re.get(f'{okapi_url}{services_endpoint}?limit=1000', headers=headers)
                sp_response.raise_for_status()
                service_points_data = sp_response.json()
                all_service_points = service_points_data.get('servicepoints', [])
                
                if not all_service_points:
                    st.warning("No service points found in the system.")
                    return
                
                # Extract service point IDs
                service_point_ids = [sp['id'] for sp in all_service_points]
                service_point_names = [sp['name'] for sp in all_service_points]
                
                st.info(f"📋 Found {len(service_point_ids)} service point(s): {', '.join(service_point_names[:5])}{'...' if len(service_point_names) > 5 else ''}")
        
        except re.exceptions.HTTPError as e:
            st.error(f"Failed to fetch service points: {e.response.status_code}")
            if e.response.text:
                try:
                    error_detail = e.response.json()
                    st.error(f"Error: {error_detail}")
                except:
                    st.error(f"Error: {e.response.text[:200]}")
            return
        except Exception as e:
            st.error(f"Error fetching service points: {str(e)}")
            return
        
        # Build normalHours array (one entry per selected day)
        normal_hours = []
        for day in selected_days:
            normal_hours.append({
                "startDay": day,
                "startTime": start_time,
                "endDay": day,
                "endTime": end_time
            })
        
        # Create calendar data
        calendar_data = {
            "id": None,
            "name": cal_name,
            "startDate": str(start_date),
            "endDate": str(end_date),
            "assignments": service_point_ids,  # Assign to all service points
            "normalHours": normal_hours,
            "exceptions": []
        }
        
        # Create calendar
        try:
            with st.spinner(f'Creating calendar "{cal_name}" for {len(service_point_ids)} service point(s)...'):
                # Use json parameter to automatically set Content-Type header
                create_cal = re.post(
                    f'{okapi_url}{calendar_endpoint}',
                    json=calendar_data,  # Use json parameter instead of data=json.dumps()
                    headers=headers
                )
                create_cal.raise_for_status()
                
                # Check response
                if create_cal.status_code in [200, 201]:
                    st.success(f"✅ Calendar '{cal_name}' created successfully for {len(service_point_ids)} service point(s)!")
                    st.info(f"📅 **Calendar Details:**\n- Days: {', '.join(selected_days)}\n- Hours: {start_time} - {end_time}\n- Period: {start_date} to {end_date}\n- Service Points: {len(service_point_ids)}")
                else:
                    st.warning(f"Unexpected response: {create_cal.status_code}")
                    
        except re.exceptions.HTTPError as e:
            st.error(f"Failed to create calendar: {e.response.status_code}")
            if e.response.text:
                try:
                    error_detail = e.response.json()
                    st.error(f"Error: {error_detail}")
                except:
                    st.error(f"Error: {e.response.text[:500]}")
        except Exception as e:
            st.error(f"Error creating calendar: {str(e)}")




    # calendar_endpoint = "/calendar/periods/d8b94015-c108-4f18-89ce-c00d4f7b7fc0/period"
    #
    # service_points = re.get(st.session_state.okapi+services_endpoint, headers=headers).json()
    # todays_date = date.today()
    # days = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY']
    # df = pd.DataFrame(days, columns=['Day'])
    # builder = GridOptionsBuilder.from_dataframe(df)
    # builder.configure_selection(selection_mode='multiple', use_checkbox=True, header_checkbox=True)
    # builder.configure_pagination(enabled=True)
    # list = ['1:00', '2:00', '3:00']
    # # times = time_interval(24, 60, 15)
    #
    # builder.configure_column('Opening Time', editable=True, index=times.index("00:00"), cellEditor='agSelectCellEditor', cellEditorParams={'values': times}, singleClickEdit=True)
    # builder.configure_column('Closing Time', editable=True, index=times.index("00:00"), cellEditor='agSelectCellEditor',cellEditorParams={'values': times}, singleClickEdit=True)
    # go = builder.build()
    # grid_return = AgGrid(df, editable=True, theme='balham', gridOptions=go)
    #
    # selected_rows = grid_return['selected_rows']
    #
    # if bool(selected_rows):
    #     selection = pd.DataFrame(selected_rows)
    #     selection.fillna("00:00", inplace=True)
    #     createCal = st.button('Update Calendar')
    #     st.write(selection)
    #     if createCal:
    #         working_days = []
    #         working = []
    #         hours = []
    #         open_hours = []
    #         closed_hours = []
    #         # FLAG TO CHECK IF TIMES ARE CHOSEN
    #         check_opening_chosen = 0
    #         check_closing_chosen = 0
    #
    #         row_num = selection.shape[0]
    #         # IF TIMES NOT SELECTED
    #         if ('Opening Time' not in selection):
    #             for j in range(0, selection.shape[0]):
    #                 open_hours.append("00:00")
    #             check_opening_chosen = 1
    #
    #         if ('Closing Time' not in selection):
    #             for j in range(0, selection.shape[0]):
    #                 closed_hours.append("00:00")
    #             check_closing_chosen = 1
    #
    #         counter = 0
    #         for index, row in selection.iterrows():
    #             if check_opening_chosen == 0:
    #                 open_hours = row['Opening Time']
    #             if check_closing_chosen == 0:
    #                 closed_hours = row['Closing Time']
    #             working_days.append(row['Day'])
    #             working.append({"day": row['Day']})
    #             hours.append({"startTime": open_hours[counter], "endTime": closed_hours[counter]})
    #             counter = counter + 1
    #         # st.write(working)
    #         # st.write(hours)
    #         data = {
    #             "name": "ra",
    #             "startDate": str(todays_date),
    #             "endDate": str(todays_date.replace(year=todays_date.year + 50)),
    #             "openingDays": [],
    #             "servicePointId": "d8b94015-c108-4f18-89ce-c00d4f7b7fc0",
    #             "id": "166b6783-29b2-4782-8cc9-6301ab81ae31"
    #         }
    #         for i in range(0, counter):
    #             data["openingDays"].append({"weekdays": working[i], "openingDay": {"openingHour": [hours[i]],
    #                                                                                "allDay": False, "open": True}})
    #         st.write(json.dumps(data))
    #         c = 1
    #         for x in service_points['servicepoints']:
    #             # st.write(c)
    #             service_id = x['id']
    #             # st.write(service_id)
    #             c = c+1
    # https: // okapi - g42.medad.com/calendar/periods/e82a8ea3-0db6-4da4-b67d-6e9efd2d8738/period
    # {
    #     "name": "test",
    #     "startDate": "2023-03-15",
    #     "endDate": "2023-03-15",
    #     "openingDays": [
    #         {
    #             "weekdays": {
    #                 "day": "SUNDAY"
    #             },
    #             "openingDay": {
    #                 "openingHour": [
    #                     {
    #                         "startTime": "00:00",
    #                         "endTime": "02:30"
    #                     }
    #                 ],
    #                 "allDay": false,
    #                 "open": true
    #             }
    #         },
    #         {
    #             "weekdays": {
    #                 "day": "MONDAY"
    #             },
    #             "openingDay": {
    #                 "openingHour": [
    #                     {
    #                         "startTime": "00:00",
    #                         "endTime": "02:30"
    #                     }
    #                 ],
    #                 "allDay": false,
    #                 "open": true
    #             }
    #         },
    #         {
    #             "weekdays": {
    #                 "day": "TUESDAY"
    #             },
    #             "openingDay": {
    #                 "openingHour": [
    #                     {
    #                         "startTime": "00:00",
    #                         "endTime": "02:00"
    #                     }
    #                 ],
    #                 "allDay": false,
    #                 "open": true
    #             }
    #         }
    #     ],
    #     "servicePointId": "e82a8ea3-0db6-4da4-b67d-6e9efd2d8738",
    #     "id": "68ca0415-3452-47a7-818f-0c09da6e07c1"
    # }

    # from_time = st.time_input('Opening at: ', datetime.time(8, 0))
    # st.write('Library open from ', from_time)
    #
    # close_time = st.time_input('Closes at: ', datetime.time(20, 0))
    # st.write('Library closes ', close_time)


    # else:
    #     st.warning('Please create locations first.')

def exceptions():
    # Get tenant connection details with fallbacks
    tenant = st.session_state.get("tenant") or st.session_state.get("tenant_name")
    token = st.session_state.get("token")
    okapi = st.session_state.get("okapi") or st.session_state.get("okapi_url")

    if not all([tenant, token, okapi]):
        st.error("⚠️ Tenant connection information is missing. Please connect to a tenant first.")
        st.info("Go to the Tenant page, enter connection details, click Connect, then return here.")
        return
    
    headers = {"x-okapi-tenant": f"{tenant}", "x-okapi-token": f"{token}"}
    services_endpoint = "/service-points"
    
    file = upload('Calendar Exceptions')
    df = pd.DataFrame(file)
    for index, row in df.iterrows():
        # st.write(row['ServicePoints name'])
        service_points = re.get(
            okapi + services_endpoint + f'?query=(name=={row["ServicePoints name"]})',
            headers=headers).json()
        if not service_points['servicepoints']:
            # IF THE SERVICE POINT DOES NOT EXIST
            st.warning(f' Service point ({row["ServicePoints name"]}) does not exist.')

        else:
            # IF SERVICE POINT FOUND, TAKE ID
            service_id = service_points['servicepoints'][0]['id']
            # 'https://okapi.medadstg.com/calendar/periods/1b9f5ef4-3450-48a2-afdc-f2ca9e02805f/period'
            # {
            #     "servicePointId": "1b9f5ef4-3450-48a2-afdc-f2ca9e02805f",
            #     "name": "test",
            #     "startDate": "2023-05-14",
            #     "endDate": "2023-05-14",
            #     "openingDays": [
            #         {
            #             "openingDay": {
            #                 "openingHour": [
            #                     {
            #                         "startTime": "19:10",
            #                         "endTime": "21:10"
            #                     }
            #                 ],
            #                 "allDay": null,
            #                 "open": true
            #             }
            #         }
            #     ],
            #     "id": "0e7c1080-b2f9-428a-8b27-9d7fa5fa4aae"
            # }

