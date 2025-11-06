# FOLIO Library Management System Automation Tool

A comprehensive Streamlit-based automation tool designed for managing and configuring FOLIO Library Management System tenants. This tool provides an intuitive web interface for automating repetitive tasks, tenant configuration, data migration, and bulk operations within the FOLIO ecosystem.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Module Descriptions](#module-descriptions)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)
- [Security Notes](#security-notes)
- [Contributing](#contributing)
- [Support](#support)

---

## 🎯 Overview

This automation tool simplifies the management of FOLIO tenants by providing a unified interface for:

- **Tenant Configuration**: Automated setup of new FOLIO tenants with standardized configurations
- **Tenant Cloning**: Copy settings and configurations from one tenant to another
- **Data Migration**: Bulk import of users, materials, locations, and other entities
- **Configuration Management**: Manage material types, locations, service points, calendars, and more
- **MARC Record Processing**: Clean, split, and process MARC bibliographic records
- **Backup and Restore**: Create backups of tenant configurations for disaster recovery

## ✨ Features

### 🔐 Authentication & Tenant Management
- **Secure Login System**: Streamlit-authenticator based authentication
- **Multi-Tenant Support**: Connect to multiple FOLIO environments
- **Tenant Backup**: Export tenant configurations as JSON files
- **Tenant Cloning**: Copy settings between tenants (production, staging, etc.)

### ⚙️ Basic Configuration
Automated setup of essential tenant settings:
- Locale settings (timezone, currency)
- Email/SMTP configuration
- Default job profiles for MARC import
- Alternative title types
- Departments
- Circulation settings
- Loan history configuration
- Export profiles

### 🛠️ Advanced Configuration
Comprehensive configuration management through Excel upload:
- **Material Types**: Bulk creation and management
- **Statistical Codes**: Statistical code types and codes
- **User Groups**: Patron group configuration
- **Location Hierarchy**: Institutions, campuses, libraries, and locations
- **Departments**: Department management
- **Calendar**: Opening hours and calendar periods
- **Exceptions**: Calendar exceptions for holidays
- **Column Configuration**: Custom field mappings

### 👥 User Management
- **User Import**: Bulk import users from Excel files
- **Default Users**: Create default system users with predefined permissions
- **Permission Management**: Assign permissions to users (Full, API, SIP2, Admin, etc.)
- **User Updates**: Update existing users based on username matching

### 📚 Inventory & Circulation
- **Material Types**: Manage item material types
- **Loan Types**: Configure circulation loan types
- **Circulation Loans Import**: Import existing loan transactions
- **Circulation Rules**: Clone and manage circulation rules
- **Loan Policies**: Loan, request, and overdue fine policies
- **Notice Templates**: Email and SMS notice templates

### 🌐 Integration & Protocols
- **SIP2 Configuration**: Self-Service Integration Protocol setup
- **Z39.50 Configuration**: Configure Z39.50 search targets
- **SMTP Configuration**: Email server settings

### 📄 MARC Record Operations
- **MARC Cleaner**: Clean and fix MARC records
- **MARC Splitter**: Split large MARC files by tag
- **MARC Processing**: Validate and process bibliographic records

### 💰 Fines & Fees
- Overdue fine policies
- Lost item fee policies
- Fine configuration and management

### 🔧 Additional Tools
- **Service Points**: Create and manage service points
- **Column Configuration**: Custom field mappings
- **Calendar Management**: Opening hours and exceptions

---

## 📦 Prerequisites

Before installing and running this tool, ensure you have:

- **Python 3.8+** installed
- **Chrome Browser** (for Selenium automation)
- **ChromeDriver** (included in `drivers/` directory)
- Access to FOLIO Okapi API endpoints
- Valid FOLIO tenant credentials
- Network access to FOLIO servers

---

## 🚀 Installation

### Step 1: Clone the Repository

```bash
git clone https://github.com/ahmedawada/automation.git
cd automation
```

### Step 2: Create Virtual Environment (Recommended)

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Authentication

Edit `authentication.yaml` to set up user credentials:

```yaml
credentials:
  usernames:
    your_username:
      email: your.email@example.com
      name: Your Name
      password: $2b$12$...  # Hashed password using bcrypt
```

**To generate a password hash:**
```python
import streamlit_authenticator as stauth
stauth.Hasher(['your_password']).generate()
```

### Step 5: Run the Application

```bash
streamlit run Homepage.py
```

The application will start on `http://localhost:8501` by default.

---

## ⚙️ Configuration

### Supported Okapi Environments

The tool supports multiple FOLIO environments:
- Production: `https://okapi.medad.com`
- UAE Production: `https://okapi-uae.ils.medad.com`
- Staging: `https://okapi.medadstg.com`
- QA: `https://okapi.qa.medad.com`
- And more (see tenant connection pages)

### Authentication Configuration

Update `authentication.yaml` with:
- Usernames and passwords (bcrypt hashed)
- Cookie settings (name, key, expiry days)
- Pre-authorized emails (optional)

---

## 📖 Usage Guide

### 1. Login & Tenant Connection

1. Navigate to the homepage
2. Enter your username and password
3. Select an operation:
   - **Login to Tenant**: Connect to a single tenant for configuration
   - **Clone Existing Tenant**: Copy settings from one tenant to another
   - **Backup Tenant**: Export tenant configuration

4. Enter tenant credentials:
   - Tenant name
   - Username
   - Password
   - Okapi URL

5. Click **Connect** to authenticate

### 2. Basic Configuration

After connecting to a tenant:

1. Navigate to **Basic Configuration**
2. Enter the **Client URL** (e.g., `https://medad.ils.com`)
3. Select **Timezone** and **Currency**
4. Click **Start** to begin automated configuration

This will configure:
- SMTP settings
- MARC job profiles
- Alternative title types
- Departments
- Locale settings
- Circulation defaults
- Export profiles

### 3. Advanced Configuration

1. Navigate to **Advanced Configuration**
2. Upload an Excel file with the following sheets:
   - Material Types
   - Statistical Codes
   - User Groups
   - Locations
   - Departments
   - Calendar
   - Exceptions
   - Column Configuration

3. Review the uploaded data in each tab
4. Click **Submit** to create the configurations

### 4. Tenant Cloning

To copy settings from one tenant to another:

1. Select **Clone Existing Tenant** on homepage
2. Connect to **Master Tenant** (source)
3. Connect to **Clone Tenant** (destination)
4. Select which settings to clone:
   - ✅ Patron Groups
   - ✅ Service Points
   - ✅ Fixed Due Dates
   - ✅ Location Hierarchy
   - ✅ Loan Types
   - ✅ Loan/Request Policy
   - ✅ Overdue/Lost Policy
   - ✅ Notice Templates
   - ✅ Staff Slips
   - ✅ Circulation Rules

5. Click **Clone it** to start the process

### 5. User Import

1. Navigate to **Users Import**
2. Upload an Excel file with user data
3. Map columns to FOLIO user fields:
   - username, barcode, patronGroup
   - personal.firstName, personal.lastName
   - personal.email, personal.phone
   - addresses, departments, etc.

4. Review the preview
5. Click **Import Users** to process

**Note**: The tool will update existing users (matched by username) or create new ones.

### 6. Circulation Loans Import

1. Navigate to **Circulation Loans**
2. Upload Excel file with columns:
   - **BARCODE**: Item barcode
   - **P_BARCODE**: Patron barcode
   - **LOAN_DATE**: Loan date (dd-mm-yyyy)
   - **DUE_DATE**: Due date (dd-mm-yyyy)
   - **SERVICE_POINT_ID**: Service point UUID

3. Review the preview
4. Click **Import Loans** to process

### 7. MARC Operations

#### MARC Cleaner
1. Navigate to **Marc Cleaner**
2. Upload a MARC file
3. Tool will clean and fix common MARC issues
4. Download the cleaned file

#### MARC Splitter
1. Navigate to **Marc Splitter**
2. Upload a MARC file
3. Enter the tag to split by (e.g., 001, 245)
4. Tool will create separate files for each unique tag value

### 8. Backup Tenant

1. Select **Backup Tenant** on homepage
2. Connect to the tenant
3. Click **Download Backup** to export all configurations

The backup includes:
- Patron groups
- Service points
- Loan types and policies
- Locations
- Notices
- Circulation rules
- Calendar periods
- And more...

---

## 📚 Module Descriptions

### Core Modules

#### `Homepage.py`
Main entry point with authentication and navigation to tenant operations.

#### `pages/0_✅Tenant.py`
Tenant connection interface supporting:
- Single tenant connection
- Dual tenant connection (for cloning)
- Tenant backup

#### `pages/1_⚙️️Basic_Configuration.py`
Automated basic tenant setup including locale, SMTP, and default configurations.

#### `pages/2_🛠️️Advanced_configuration.py`
Advanced configuration management with Excel-based bulk operations.

#### `clone_functions.py`
Core functions for cloning settings between tenants:
- `moveSettings()`: Generic settings migration
- `movelocations()`: Location hierarchy migration
- `movecircpolicies()`: Circulation policy migration
- `movecircrules()`: Circulation rules migration

#### `extras.py`
Utility functions for:
- Async API requests
- Default configurations
- Test record creation
- Helper functions for IDs

### Feature Modules

#### User Management
- `pages/4_👥Default_Users.py`: Create default users
- `pages/8_👤Users Import.py`: Bulk user import
- `pages/13_⛔Add permission.py`: Permission management
- `user_group.py`: User group management

#### Configuration
- `Material_types.py`: Material type management
- `Location.py`: Location hierarchy management
- `Department.py`: Department management
- `Service_points.py`: Service point creation
- `Statistical_Codes.py`: Statistical code management
- `Column_Configuration.py`: Column mapping

#### Integration
- `pages/3_🖥️Sip2_Configuration.py`: SIP2 protocol setup
- `pages/14_🗝️Z39.50.py`: Z39.50 configuration
- `Smtp.py`: SMTP server configuration

#### Circulation
- `pages/9_📙Circulation Loans.py`: Loan transaction import
- `pages/10_💵Fines.py`: Fine policy management
- `Notices.py`: Notice template configuration

#### MARC Processing
- `11_🧹Marc Cleaner.py`: MARC record cleaning
- `pages/12_♻️Marc Splitter.py`: MARC file splitting
- `Clean_Marc.py`: MARC validation utilities

#### Utilities
- `Tenant_Backup.py`: Backup functionality
- `Calendar.py`: Calendar and exception management
- `permissions.py`: Permission definitions
- `legacy_session_state.py`: Streamlit compatibility

---

## 🌐 API Endpoints

The tool interacts with FOLIO Okapi API endpoints. Key endpoints include:

### Authentication
- `POST /authn/login` - Authenticate user

### Configuration
- `GET/POST /configurations/entries` - Configuration entries
- `GET /calendar/periods` - Calendar periods

### Users & Groups
- `GET/POST /users` - User management
- `GET/POST /groups` - Patron groups
- `GET/POST /departments` - Departments
- `POST /perms/users` - User permissions

### Inventory
- `GET/POST /material-types` - Material types
- `GET/POST /loan-types` - Loan types
- `GET/POST /locations` - Locations
- `GET/POST /service-points` - Service points

### Circulation
- `GET/POST /loan-policy-storage/loan-policies` - Loan policies
- `GET/POST /overdue-fines-policies` - Overdue policies
- `GET/POST /circulation/rules` - Circulation rules
- `POST /circulation/check-out-by-barcode` - Check out items

### MARC & Records
- `GET/POST /records-editor/records` - MARC records
- `GET/POST /inventory/instances` - Instance records
- `GET/POST /holdings-storage/holdings` - Holdings records
- `GET/POST /inventory/items` - Item records

### Other
- `GET/POST /templates` - Notice templates
- `GET/POST /alternative-title-types` - Alternative titles
- `GET/POST /staff-slips-storage/staff-slips` - Staff slips

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Authentication Failed
**Problem**: Cannot connect to tenant
**Solution**:
- Verify Okapi URL is correct
- Check tenant name spelling
- Ensure username/password are correct
- Verify network connectivity to Okapi server

#### 2. Import Errors
**Problem**: Excel import fails
**Solution**:
- Verify column names match predefined columns
- Check data types (dates, UUIDs, etc.)
- Ensure required fields are not empty
- Review Excel file format (.xlsx recommended)

#### 3. API Timeout Errors
**Problem**: Requests timing out
**Solution**:
- Check network connection
- Verify Okapi server is accessible
- For large imports, consider breaking into smaller batches
- Check server logs for issues

#### 4. Permission Errors
**Problem**: Operations fail due to permissions
**Solution**:
- Ensure user has required FOLIO permissions
- Check tenant permissions are correctly assigned
- Verify user role has necessary API access

#### 5. ChromeDriver Issues
**Problem**: Selenium errors
**Solution**:
- Ensure ChromeDriver version matches Chrome browser
- Update ChromeDriver if Chrome was updated
- Check `drivers/` directory contains chromedriver.exe

### Debug Mode

Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

---

## 🔒 Security Notes

### Important Security Considerations

1. **Password Storage**: 
   - Passwords in `authentication.yaml` are bcrypt hashed
   - Never commit plain-text passwords
   - Use strong passwords for authentication

2. **Tenant Credentials**:
   - Tenant credentials are stored in session state
   - Credentials are not persisted to disk
   - Clear session after use

3. **API Tokens**:
   - Tokens are stored in session state temporarily
   - Tokens expire based on FOLIO settings
   - Do not log or expose tokens

4. **File Uploads**:
   - Validate all uploaded files
   - Check file sizes and formats
   - Scan for malicious content

5. **Network Security**:
   - Use HTTPS for all Okapi connections
   - Verify SSL certificates
   - Use secure networks when accessing

6. **Access Control**:
   - Restrict access to the application
   - Use strong authentication
   - Limit pre-authorized emails

---

## 🤝 Contributing

### Adding New Features

1. Create feature branch: `git checkout -b feature/new-feature`
2. Follow existing code structure
3. Add appropriate error handling
4. Update documentation
5. Test thoroughly
6. Submit pull request

### Code Style

- Follow PEP 8 Python style guide
- Use type hints where possible
- Add docstrings to functions
- Maintain consistency with existing code

### Testing

- Test with different tenant environments
- Verify with sample data
- Check error handling
- Test edge cases

---

## 📞 Support

For issues, questions, or contributions:

- **Internal Team**: Contact KAM Support Team
- **Email**: kam@naseej.com
- **Repository**: Check internal documentation

### Getting Help

When reporting issues, please include:
- Error messages
- Steps to reproduce
- Tenant environment details
- Log files (if available)
- Screenshots (if applicable)

---

## 📝 Changelog

### Current Version
- Full tenant configuration automation
- Tenant cloning functionality
- User bulk import
- MARC processing tools
- Advanced configuration management
- Calendar and exception handling
- Permission management
- SIP2 and Z39.50 configuration

---

## 📄 License

Internal tool for KAM Team use only.

---

## 🙏 Acknowledgments

Developed for and by the KAM Support Team to streamline FOLIO tenant management and reduce manual configuration time.

---

**Last Updated**: 2025
**Version**: 1.0
**Maintained by**: KAM Support Team
**Repository**: [https://github.com/ahmedawada/automation](https://github.com/ahmedawada/automation)

