# Project Structure

This document describes the structure of the FOLIO Automation Tool codebase.

## 📁 Directory Structure

```
automation-main/
│
├── 📄 Homepage.py                    # Main entry point - authentication & navigation
├── 📄 authentication.yaml            # User authentication config (NOT in git)
├── 📄 authentication.yaml.example    # Template for authentication config
├── 📄 requirements.txt               # Python dependencies
├── 📄 README.md                      # Main documentation
├── 📄 QUICK_START.md                 # Quick start guide
├── 📄 CONFIGURATION_TEMPLATE.md      # Excel template guide
├── 📄 PROJECT_STRUCTURE.md           # This file
│
├── 📁 pages/                         # Streamlit page modules
│   ├── 0_✅Tenant.py                 # Tenant connection (single/dual/backup)
│   ├── 1_⚙️️Basic_Configuration.py    # Basic tenant setup automation
│   ├── 2_🛠️️Advanced_configuration.py # Advanced config (Excel-based)
│   ├── 3_🖥️Sip2_Configuration.py     # SIP2 protocol setup
│   ├── 4_👥Default_Users.py          # Default user creation
│   ├── 8_👤Users Import.py           # Bulk user import
│   ├── 9_📙Circulation Loans.py      # Loan transaction import
│   ├── 10_💵Fines.py                 # Fine policy management
│   ├── 12_♻️Marc Splitter.py        # MARC file splitting
│   ├── 13_⛔Add permission.py        # Permission assignment
│   └── 14_🗝️Z39.50.py               # Z39.50 configuration
│
├── 📁 drivers/                       # Browser drivers
│   └── chromedriver.exe              # ChromeDriver for Selenium
│
├── 📁 images/                        # Images and assets
│   └── naseej.png                    # Logo/icon
│
├── 📁 Core Modules/                  # Core functionality
│   ├── clone_functions.py            # Tenant cloning functions
│   ├── extras.py                     # Utility functions & async helpers
│   ├── legacy_session_state.py        # Streamlit compatibility layer
│   └── Tenant_Backup.py              # Backup functionality
│
├── 📁 Configuration Modules/         # Configuration management
│   ├── Material_types.py             # Material type management
│   ├── Location.py                    # Location hierarchy management
│   ├── Department.py                 # Department management
│   ├── Service_points.py            # Service point creation
│   ├── Statistical_Codes.py          # Statistical code management
│   ├── Column_Configuration.py       # Column mapping
│   ├── Calendar.py                   # Calendar & exception management
│   ├── user_group.py                 # User group management
│   └── Smtp.py                       # SMTP configuration
│
├── 📁 Integration Modules/           # External integrations
│   ├── z3950.py                      # Z39.50 utilities
│   └── permissions.py                # Permission definitions
│
├── 📁 MARC Processing/               # MARC record operations
│   ├── 11_🧹Marc Cleaner.py          # MARC cleaning utility
│   ├── Clean_Marc.py                 # MARC validation
│   └── Upload.py                     # File upload handler
│
├── 📁 Circulation & Notices/         # Circulation features
│   ├── Notices.py                    # Notice template management
│   └── (pages/9_📙Circulation Loans.py referenced above)
│
└── 📄 style.css                      # Custom CSS styles
```

---

## 🔑 Key Files Explained

### Entry Point
- **`Homepage.py`**: Main application entry point
  - Handles authentication
  - Routes to different modules
  - Manages session state

### Core Functions
- **`clone_functions.py`**: Essential functions for tenant cloning
  - `moveSettings()`: Generic settings migration
  - `movelocations()`: Location hierarchy migration
  - `movecircpolicies()`: Circulation policy migration
  - `movecircrules()`: Circulation rules migration

- **`extras.py`**: Utility functions
  - Async API request helpers
  - Default configuration functions
  - Test record creation
  - ID lookup functions

- **`legacy_session_state.py`**: Compatibility layer
  - Fixes Streamlit session state issues
  - Handles widget key conflicts

### Configuration Files
- **`authentication.yaml`**: User authentication (excluded from git)
- **`requirements.txt`**: Python package dependencies

---

## 📊 Data Flow

### Typical User Flow:
```
1. Homepage.py
   ↓
2. Authentication (streamlit-authenticator)
   ↓
3. Select Operation (Login/Clone/Backup)
   ↓
4. pages/0_✅Tenant.py (Tenant Connection)
   ↓
5. Navigate to Feature Page
   ↓
6. Feature Module (e.g., pages/1_⚙️️Basic_Configuration.py)
   ↓
7. Core Functions (extras.py, clone_functions.py, etc.)
   ↓
8. FOLIO Okapi API
```

### Clone Operation Flow:
```
1. Connect to Master Tenant
   ↓
2. Connect to Clone Tenant
   ↓
3. Select Settings to Clone
   ↓
4. clone_functions.py processes each setting
   ↓
5. GET from Master Tenant
   ↓
6. POST/PUT to Clone Tenant
   ↓
7. Error Handling (fallback to PUT if POST fails)
```

---

## 🧩 Module Dependencies

### Core Dependencies:
- `streamlit`: Web framework
- `streamlit-authenticator`: Authentication
- `requests`: HTTP requests
- `aiohttp`: Async HTTP requests
- `pandas`: Data manipulation
- `openpyxl`: Excel file handling
- `pymarc`: MARC record processing
- `selenium`: Browser automation (for some features)

### Internal Dependencies:
- Most pages depend on `legacy_session_state.py`
- Clone functions used by `pages/0_✅Tenant.py`
- `extras.py` used by basic configuration
- Utility modules used by advanced configuration

---

## 🔄 Session State Management

The application uses Streamlit's session state to manage:
- `allow_tenant`: Tenant connection status
- `token`: Authentication token
- `tenant`: Tenant name
- `okapi`: Okapi URL
- `username_tenant`: Tenant username
- `profiling`: Uploaded Excel data
- Various feature-specific states

See `legacy_session_state.py` for compatibility handling.

---

## 🎨 Page Organization

Pages are organized with emoji prefixes for easy identification:
- ✅ Tenant operations
- ⚙️ Basic configuration
- 🛠️ Advanced configuration
- 🖥️ SIP2
- 👥 Users
- 📙 Circulation
- 💵 Fines
- 🧹 Cleaning tools
- ♻️ Splitting tools
- ⛔ Permissions
- 🗝️ Z39.50

---

## 📝 Code Style

- Python 3.8+ compatible
- Functions organized by feature
- Async functions for concurrent operations
- Error handling with fallbacks
- Session state for data persistence
- Streamlit widgets for UI

---

## 🔐 Security Considerations

- Authentication credentials in `authentication.yaml` (not in git)
- Session-based token storage (not persisted)
- No hardcoded credentials
- HTTPS for all API calls
- Input validation on uploads

---

## 🚀 Adding New Features

When adding new features:

1. Create page in `pages/` directory
2. Follow naming convention: `N_📝Feature Name.py`
3. Use `legacy_session_state()` at top
4. Check `st.session_state.allow_tenant` before API calls
5. Add to sidebar navigation if needed
6. Update documentation

---

## 📞 Maintenance Notes

- Update ChromeDriver when Chrome updates
- Keep `requirements.txt` up to date
- Test with multiple tenant environments
- Verify API endpoint changes in FOLIO updates
- Review session state usage for memory issues

---

**Last Updated**: 2024

