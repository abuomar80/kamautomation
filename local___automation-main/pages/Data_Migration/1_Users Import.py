import streamlit as st
import pandas as pd
import asyncio
import tempfile
import os
import json
import logging
import time
import sys
from io import StringIO
from pathlib import Path

# Data Migration Page - Requires separate login
st.set_page_config(
    page_title="Users Import", layout="wide", initial_sidebar_state="expanded"
)

# Import folioclient first (should be in system Python path)
try:
    from folioclient import FolioClient
except ImportError as e:
    st.error(f"❌ Missing `folioclient` package. Please install: `pip install folioclient`")
    st.error(f"**Error:** `{str(e)}`")
    st.info("💡 Run in terminal: `pip install folioclient`")
    st.stop()

# Import UserImporter from root directory
# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from UserImport import UserImporter
except ImportError as e:
    st.error(f"❌ Could not import UserImporter from UserImport.py")
    st.error(f"**Error:** `{str(e)}`")
    st.info(f"💡 Make sure UserImport.py exists in: `{project_root}`")
    st.stop()

# Import login form after other imports
from data_migration_login import render_login_form

# Render login form and get connection status
connected, okapi_url, tenant_id, token, headers, username, password = render_login_form(page_key_prefix="users")


# -----------------------
# CSV → JSONL converter
# -----------------------
def csv_to_jsonl(df: pd.DataFrame, outfile: str):
    CONTACT_MAP = {
        "001": "001", "mail": "001",
        "002": "002", "email": "002",
        "003": "003", "text": "003",
        "004": "004", "phone": "004",
        "005": "005", "mobile": "005"
    }

    def as_bool(v, default=False):
        if pd.isna(v): return default
        s = str(v).strip().lower()
        if s in {"true", "yes", "1"}: return True
        if s in {"false", "no", "0"}: return False
        return default

    def split_list(v):
        return [] if pd.isna(v) else [x.strip() for x in str(v).split(";") if x.strip()]

    def contact_code(v, default="002"):
        if pd.isna(v) or str(v).strip() == "":
            return default
        return CONTACT_MAP.get(str(v).strip().lower(), default)

    def clean_nans(obj):
        if isinstance(obj, dict):
            return {k: clean_nans(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [clean_nans(x) for x in obj]
        elif isinstance(obj, float) and pd.isna(obj):
            return None
        return obj

    with open(outfile, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            user = {
                "username": row.get("username"),
                "barcode": row.get("barcode"),
                "active": as_bool(row.get("active"), True),
                "type": row.get("type") or "patron",
                "patronGroup": row.get("patronGroup") or "patron",
                "externalSystemId": row.get("externalSystemId") or row.get("username"),
                "departments": [],
                "personal": {
                    "firstName": row.get("firstName") or "",
                    "lastName": row.get("lastName") or "",
                    "email": row.get("email"),
                    "phone": row.get("phone"),
                    "addresses": [],
                    "preferredContactTypeId": contact_code(row.get("preferredContactType")),
                },
                "requestPreference": {
                    "holdShelf": as_bool(row.get("holdShelf"), True),
                    "delivery": as_bool(row.get("delivery"), False),
                    "fulfillment": row.get("fulfillment") or "Hold Shelf",
                }
            }

            if not pd.isna(row.get("countryId")) or not pd.isna(row.get("addressLine1")):
                user["personal"]["addresses"].append({
                    "countryId": row.get("countryId") or "",
                    "addressLine1": row.get("addressLine1") or "",
                    "addressLine2": row.get("addressLine2") or "",
                    "city": row.get("city") or "",
                    "region": row.get("region") or "",
                    "postalCode": row.get("postalCode") or "",
                    "addressTypeId": row.get("addressTypeId") or "Home",
                    "primaryAddress": True,
                })

            spu = {}
            if not pd.isna(row.get("servicePoints")) and str(row.get("servicePoints")).strip():
                spu["servicePointsIds"] = split_list(row.get("servicePoints"))
            if not pd.isna(row.get("defaultServicePoint")) and str(row.get("defaultServicePoint")).strip():
                spu["defaultServicePointId"] = str(row.get("defaultServicePoint")).strip()
            if spu:
                user["servicePointsUser"] = spu

            user = clean_nans(user)
            f.write(json.dumps(user, ensure_ascii=False) + "\n")


# -----------------------
# Main UI
# -----------------------
if __name__ == "__main__":
    st.title("📚 Medad User Import")
    
    st.markdown("""**This App is used to load users to Medad ILS.**

    The app supports importing users from CSV or JSONL files with advanced features:
    - ✅ Automatic user matching and updates
    - ✅ Batch processing with progress tracking
    - ✅ Field protection (preserve existing values)
    - ✅ Service point assignment
    - ✅ Request preferences management
    - ✅ Support for CSV and JSONL formats
    """, unsafe_allow_html=True)

    if not connected:
        st.info("👆 Please login to your tenant above to access the Users Import tool.")
        st.stop()

    st.divider()

    tab1, tab2 = st.tabs(["👤 User Import", "📄 Instructions & CSV Template"])

    # ---------- TAB 1: Import ----------
    with tab1:
        # Get username from login form session state
        username = st.session_state.get("users_username", "")
        
        # Get password - we need to get it from the form state if available
        # Since password is not stored, we'll need to handle authentication differently
        # For now, we'll use the FolioClient which will authenticate with the token
        # But we need username and password for FolioClient initialization
        
        st.caption(f"Connected to tenant: **{tenant_id}** | Okapi URL: **{okapi_url}**")
        
        file = st.file_uploader("Upload CSV or JSONL file", type=["csv", "jsonl", "xlsx"])
        match_key = st.selectbox("User match key", ["externalSystemId", "username", "email"], 
                                help="Field used to match existing users for updates")
        
        # Fields to protect multiselect
        available_fields_to_protect = [
            "barcode",
            "type",
            "patronGroup",
            "departments",
            "externalSystemId",
            "personal.firstName",
            "personal.middleName",
            "personal.lastName",
            "personal.preferredFirstName",
            "personal.email",
            "personal.phone",
            "personal.dateOfBirth",
            "personal.gender",
            "personal.addresses",
            "servicePointsUser.servicePointsIds",
            "servicePointsUser.defaultServicePointId",
            "requestPreference.holdShelf",
            "requestPreference.delivery",
            "requestPreference.fulfillment",
        ]

        default_protected_fields = [
            "personal.preferredFirstName",
            "personal.email",
            "personal.phone",
            "personal.addresses",
            "barcode",
        ]

        protect_selection = st.multiselect(
            "Fields to protect (preserve existing values on update):",
            options=available_fields_to_protect,
            default=default_protected_fields,
            help="Select the user fields that should NOT be overwritten during import updates.",
        )

        # Convert the list to comma-separated string for compatibility with importer
        protect = ",".join(protect_selection)
        batch = st.number_input("Batch size", 50, 1000, 250, step=50, 
                              help="Number of users to process in each batch")
        debug_logs = st.checkbox("Show detailed debug logs (per user / batch)", value=False)

        # Stop button flag
        if "cancel_import" not in st.session_state:
            st.session_state.cancel_import = False

        def stop_import():
            st.session_state.cancel_import = True
            st.warning("🛑 Import cancellation requested... please wait.")

        if file:
            suffix = file.name.split(".")[-1].lower()
            tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix="." + suffix).name
            with open(tmp_in, "wb") as f:
                f.write(file.read())

            if suffix == "csv":
                df = pd.read_csv(tmp_in)
                st.dataframe(df.head(10), use_container_width=True)
                tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl").name
                csv_to_jsonl(df, tmp_out)
                st.success("✅ CSV converted to JSONL")
            elif suffix == "xlsx":
                df = pd.read_excel(tmp_in)
                st.dataframe(df.head(10), use_container_width=True)
                tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".jsonl").name
                csv_to_jsonl(df, tmp_out)
                st.success("✅ Excel converted to JSONL")
            else:
                tmp_out = tmp_in

            # --------------- Run Import ---------------
            if st.button("🚀 Run User Import", type="primary"):
                st.session_state.cancel_import = False
                st.info("Starting import... please wait.")
                log_area = st.empty()
                progress_bar = st.progress(0)
                counter_area = st.empty()
                download_placeholder = st.empty()

                # Stop import button
                st.button("🛑 Stop Import", on_click=stop_import)

                # Buffer to hold log content
                log_buffer = StringIO()

                class StreamlitProgressHandler(logging.Handler):
                    def __init__(self, log_area, progress_bar, counter_area, total_lines):
                        super().__init__()
                        self.log_area = log_area
                        self.progress_bar = progress_bar
                        self.counter_area = counter_area
                        self.total_lines = total_lines or 1
                        self.lines = []
                        self.created = self.updated = self.failed = 0

                    def emit(self, record):
                        msg = self.format(record)
                        self.lines.append(msg)
                        log_buffer.write(msg + "\n")
                        text = "\n".join(self.lines[-80:])
                        self.log_area.markdown(f"```bash\n{text}\n```")
                        if "Users created" in msg and "updated" in msg:
                            try:
                                self.created = int(msg.split("Users created:")[1].split("-")[0].strip())
                                self.updated = int(msg.split("Users updated:")[1].split("-")[0].strip())
                                self.failed = int(msg.split("Users failed:")[1].strip())
                            except Exception:
                                pass
                            processed = self.created + self.updated + self.failed
                            percent = min(processed / self.total_lines, 1.0)
                            self.progress_bar.progress(percent)
                            self.counter_area.markdown(
                                f"📦 **Processed:** {processed:,}/{self.total_lines:,} users  \n"
                                f"✅ **Created:** {self.created:,}  🔄 **Updated:** {self.updated:,}  ❌ **Failed:** {self.failed:,}"
                            )

                async def run_with_cancel_support():
                    total_lines = sum(1 for _ in open(tmp_out, encoding="utf-8"))
                    handler = StreamlitProgressHandler(log_area, progress_bar, counter_area, total_lines)
                    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
                    logger = logging.getLogger("UserImport")
                    logger.setLevel(logging.DEBUG if debug_logs else logging.INFO)
                    logger.addHandler(handler)

                    # Get username and password from login form
                    if not username or not password:
                        logger.error("Username or password missing. Please reconnect using the login form above.")
                        return None
                    
                    # Create FolioClient with credentials
                    client = FolioClient(okapi_url, tenant_id, username, password)
                    
                    importer = UserImporter(
                        folio_client=client,
                        library_name="Streamlit Import",
                        batch_size=batch,
                        limit_simultaneous_requests=asyncio.Semaphore(10),
                        user_file_path=Path(tmp_out),
                        user_match_key=match_key,
                        only_update_present_fields=False,
                        default_preferred_contact_type="002",
                        fields_to_protect=protect.split(",") if protect else [],
                        no_progress=True,
                        gateway_url=okapi_url,  # Pass gateway_url separately since FolioClient doesn't expose it
                    )

                    error_file_path = Path(tempfile.gettempdir()) / f"user_import_errors_{int(time.time())}.txt"
                    await importer.setup(error_file_path)

                    try:
                        # Use TaskGroup for Python 3.11+, fallback to gather for older versions
                        # Check Python version - TaskGroup and except* require Python 3.11+
                        python_version = sys.version_info[:2]
                        use_taskgroup = python_version >= (3, 11) and hasattr(asyncio, 'TaskGroup')
                        
                        if use_taskgroup:
                            # Python 3.11+ with TaskGroup - use ExceptionGroup handling
                            try:
                                async with asyncio.TaskGroup() as tg:
                                    task = tg.create_task(importer.do_import())
                                    while not task.done():
                                        if st.session_state.cancel_import:
                                            task.cancel()
                                            raise asyncio.CancelledError
                                        await asyncio.sleep(0.5)
                            except BaseExceptionGroup as eg:  # ExceptionGroup (Python 3.11+)
                                # ExceptionGroup contains multiple exceptions - extract and display all
                                import traceback
                                error_details = []
                                for exc in eg.exceptions:
                                    error_msg = str(exc)
                                    error_details.append(error_msg)
                                    # Log full traceback for the first exception
                                    if len(error_details) == 1:
                                        tb_str = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                                        logger.error(f"❌ Import failed with exception:\n{tb_str}")
                                if len(error_details) > 1:
                                    logger.error(f"❌ Import failed with {len(error_details)} exceptions:")
                                    for i, err in enumerate(error_details, 1):
                                        logger.error(f"  Exception {i}: {err}")
                                # Re-raise as regular exception to be caught by outer handler
                                raise Exception(f"Import failed: {error_details[0] if error_details else 'Unknown error'}")
                        else:
                            # Python < 3.11 without TaskGroup
                            task = asyncio.create_task(importer.do_import())
                            while not task.done():
                                if st.session_state.cancel_import:
                                    task.cancel()
                                    raise asyncio.CancelledError
                                await asyncio.sleep(0.5)
                            await task
                            
                    except asyncio.CancelledError:
                        logger.warning("🛑 Import cancelled by user.")
                    except Exception as e:
                        # Catch all exceptions - check if it's an ExceptionGroup (for Python 3.11+ fallback)
                        import traceback
                        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
                        # Check if it's an ExceptionGroup and extract details
                        if hasattr(e, 'exceptions') and isinstance(e.exceptions, tuple):
                            logger.error(f"❌ Import failed with {len(e.exceptions)} exception(s):")
                            for i, exc in enumerate(e.exceptions, 1):
                                logger.error(f"  Exception {i}: {exc}")
                                if i == 1:  # Show full traceback for first exception
                                    logger.error(f"  Traceback:\n{tb_str}")
                        else:
                            logger.error(f"❌ Import failed: {e}\n{tb_str}")
                    finally:
                        await importer.close()
                        logger.removeHandler(handler)
                    
                    log_path = Path(tempfile.gettempdir()) / f"user_import_{int(time.time())}.log"
                    with open(log_path, "w", encoding="utf-8") as f:
                        f.write(log_buffer.getvalue())
                    
                    # Generate CSV results
                    csv_results = importer.get_results_csv()
                    csv_path = Path(tempfile.gettempdir()) / f"user_import_results_{int(time.time())}.csv"
                    with open(csv_path, "w", encoding="utf-8") as f:
                        f.write(csv_results)
                    
                    return log_path, error_file_path, csv_path

                try:
                    result = asyncio.run(run_with_cancel_support())
                    if result:
                        log_file_path, error_file_path, csv_path = result
                        progress_bar.progress(1.0)
                        if st.session_state.cancel_import:
                            counter_area.warning("🟠 Import stopped by user.")
                        else:
                            counter_area.success("✅ Import completed successfully!")

                        # Download buttons - CSV, log, and error files
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if csv_path.exists():
                                with open(csv_path, "r", encoding="utf-8") as f:
                                    st.download_button(
                                        "📊 Download Results (CSV)",
                                        f.read(),
                                        file_name=os.path.basename(csv_path),
                                        mime="text/csv",
                                        type="primary"
                                    )
                        with col2:
                            if log_file_path.exists():
                                with open(log_file_path, "r", encoding="utf-8") as f:
                                    st.download_button(
                                        "📄 Download Import Log",
                                        f.read(),
                                        file_name=os.path.basename(log_file_path),
                                        mime="text/plain",
                                    )
                        with col3:
                            if error_file_path.exists() and error_file_path.stat().st_size > 0:
                                with open(error_file_path, "r", encoding="utf-8") as f:
                                    st.download_button(
                                        "⚠️ Download Error Log",
                                        f.read(),
                                        file_name=os.path.basename(error_file_path),
                                        mime="text/plain",
                                    )
                except Exception as e:
                    counter_area.error(f"❌ Import failed: {e}")
                    st.exception(e)

    # ---------- TAB 2: Instructions ----------
    with tab2:
        st.header("📘 How to Prepare Your CSV File for User Import")
        st.markdown("""
        Each **row** represents one user. The header must contain the following columns:

        | Column | Description | Required |
        |--------|--------------|----------|
        | `username` | Unique username in Medad ILS | ✅ |
        | `externalSystemId` | Unique externalSystemId (defaults to username if not provided) | ⚪ |
        | `barcode` | User barcode (must be unique) | ✅ |
        | `active` | true/false | ⚪ |
        | `type` | User type (usually `patron`) | ⚪ |
        | `patronGroup` | Patron group code (can be name or UUID) | ✅ |
        | `firstName` | User's first name | ⚪ |
        | `lastName` | User's last name | ⚪ |
        | `email` | Email address | ⚪ |
        | `phone` | Phone number | ⚪ |
        | `countryId` | 2-letter country code | ⚪ |
        | `addressLine1` | Address line | ⚪ |
        | `city` | City name | ⚪ |
        | `postalCode` | Postal/ZIP code | ⚪ |
        | `addressTypeId` | Address type (e.g., `Home`) | ⚪ |
        | `preferredContactType` | One of: mail, email, text, phone, mobile | ⚪ |
        | `servicePoints` | Semicolon-separated service point codes (e.g., `cd1;cd2`) | ⚪ |
        | `defaultServicePoint` | Default service point code | ⚪ |
        | `holdShelf` | true/false | ⚪ |
        | `delivery` | true/false | ⚪ |
        | `fulfillment` | e.g., "Hold Shelf" | ⚪ |

        **Notes:**
        - The app will automatically match users by the selected match key (default: externalSystemId)
        - If a match is found, the user will be updated (respecting protected fields)
        - If no match is found, a new user will be created
        - Patron groups, departments, and service points can be specified by code/name or UUID
        """)

        example_df = pd.DataFrame([{
            "username": "jdoe",
            "barcode": "12345",
            "active": True,
            "type": "patron",
            "patronGroup": "staff",
            "firstName": "John",
            "lastName": "Doe",
            "email": "jdoe@example.com",
            "phone": "555-1234",
            "countryId": "US",
            "addressLine1": "123 Main St",
            "city": "Springfield",
            "postalCode": "12345",
            "addressTypeId": "Home",
            "preferredContactType": "email",
            "servicePoints": "cd1;cd2",
            "defaultServicePoint": "cd1",
            "holdShelf": True,
            "delivery": False,
            "fulfillment": "Hold Shelf"
        }])

        csv_bytes = example_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️ Download CSV Template",
            data=csv_bytes,
            file_name="user_import_template.csv",
            mime="text/csv",
        )
