# Quick Start Guide

This guide will help you get the FOLIO Automation Tool up and running quickly.

## 🚀 5-Minute Setup

### Step 1: Install Python (if not already installed)
- Download Python 3.8+ from [python.org](https://www.python.org/downloads/)
- During installation, check "Add Python to PATH"

### Step 2: Clone or Navigate to Project
```bash
cd automation-main
```

### Step 3: Create Virtual Environment
```bash
python -m venv venv

# Activate it:
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate
```

### Step 4: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 5: Set Up Authentication

**Option A: Use Default Credentials (for testing)**
The `authentication.yaml` file already has a default user configured. You can use:
- Username: `kam`
- Password: (contact team for password)

**Option B: Add Your Own User**

1. Generate a password hash:
```python
python
>>> import streamlit_authenticator as stauth
>>> hashed_passwords = stauth.Hasher(['your_password']).generate()
>>> print(hashed_passwords[0])
```

2. Edit `authentication.yaml`:
```yaml
credentials:
  usernames:
    your_username:
      email: your.email@example.com
      name: Your Name
      password: $2b$12$...  # Paste the hash here
```

### Step 6: Run the Application
```bash
streamlit run Homepage.py
```

The application will open in your browser at `http://localhost:8501`

---

## 📋 First-Time Usage

### 1. Login
- Enter your username and password
- Click "Login"

### 2. Connect to a Tenant
- Click **"Login to Tenant"**
- Fill in:
  - **Tenant Username**: Your FOLIO username
  - **Tenant Password**: Your FOLIO password
  - **Tenant Name**: Your tenant ID
  - **Okapi URL**: Select from dropdown (e.g., `https://okapi.medad.com`)
- Click **"Connect"**
- Wait for success message ✅

### 3. Basic Configuration
- Click **"Basic Configuration"** in the sidebar
- Enter **Client URL** (e.g., `https://medad.ils.com`)
- Select **Timezone** and **Currency**
- Click **"Start"** to begin automated configuration
- Wait for completion (may take 1-2 minutes)

---

## 📊 Excel Template Structure

For Advanced Configuration, create an Excel file with these sheets:

### Sheet 1: Material Types
| name | source |
|------|--------|
| Book | System |
| Journal | System |

### Sheet 2: Statistical Codes
**Statistical Code Types:**
| name | source |
|------|--------|
| Collection | System |

**Statistical Codes:**
| code | name | statisticalCodeTypeId |
|------|------|----------------------|
| REF | Reference | [UUID] |

### Sheet 3: User Groups
| group | desc | expirationOffsetInDays |
|------|------|----------------------|
| Faculty | Faculty members | 365 |

### Sheet 4: Locations
(Complex - see Location.py for structure)

### Sheet 5: Departments
| name | code |
|------|------|
| Main | main |

### Sheet 6: Calendar
(See Calendar.py for structure)

### Sheet 7: Exceptions
(See Calendar.py for structure)

---

## 🎯 Common Tasks

### Import Users
1. Go to **"Users Import"** page
2. Upload Excel file with user data
3. Map columns (username, barcode, personal.firstName, etc.)
4. Click **"Import Users"**

### Clone Tenant Settings
1. On homepage, click **"Clone Existing Tenant"**
2. Connect to **Master Tenant** (source)
3. Connect to **Clone Tenant** (destination)
4. Select which settings to clone (checkboxes)
5. Click **"Clone it"**

### Backup Tenant
1. On homepage, click **"Backup Tenant"**
2. Connect to tenant
3. Click **"Download Backup"**
4. Save the JSON file

### Import Circulation Loans
1. Go to **"Circulation Loans"** page
2. Upload Excel with columns: BARCODE, P_BARCODE, LOAN_DATE, DUE_DATE, SERVICE_POINT_ID
3. Review preview
4. Click **"Import Loans"**

---

## ⚠️ Important Notes

- **Always test in a non-production environment first**
- **Backup tenant before making major changes**
- **Verify Excel column names match exactly**
- **Date format must be: dd-mm-yyyy**
- **UUIDs are case-sensitive**

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't connect to tenant | Check Okapi URL, tenant name, and credentials |
| Import fails | Verify Excel column names and data types |
| "Module not found" error | Run `pip install -r requirements.txt` |
| Port 8501 already in use | Run `streamlit run Homepage.py --server.port 8502` |
| ChromeDriver error | Update ChromeDriver in `drivers/` folder |

---

## 📞 Need Help?

- Check the main [README.md](README.md) for detailed documentation
- Contact KAM Support Team: kam@naseej.com
- Review error messages carefully - they usually indicate the issue

---

**Happy Automating! 🎉**

