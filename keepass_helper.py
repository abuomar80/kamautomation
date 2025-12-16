"""
KeePass Password Management Helper

This module provides functions to save user credentials to KeePass databases.
- Per-tenant databases (tenant_name.kdbx)
- Master password from encrypted environment variable
- Automatic database creation and group organization
"""

import os
from typing import Dict, Optional, Tuple
from pathlib import Path
from pykeepass import PyKeePass
from pykeepass.exceptions import CredentialsError
import logging
import yaml
from yaml import SafeLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_keepass_master_password() -> Optional[str]:
    """
    Get KeePass master password from authentication.yaml file.
    Supports plain text, base64 encoded, and encrypted passwords.
    Automatically uses cookie.key as encryption_key if not specified.
    
    Returns:
        Master password string or None if not set
    """
    try:
        auth_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'authentication.yaml')
        
        if not os.path.exists(auth_file_path):
            logger.warning("authentication.yaml file not found")
            return None
        
        with open(auth_file_path, 'r') as file:
            config = yaml.load(file, Loader=SafeLoader)
        
        # Read keepass config
        keepass_config = config.get('keepass', {})
        password = keepass_config.get('master_password')
        encryption_key = keepass_config.get('encryption_key')
        is_encoded = keepass_config.get('encoded', False)
        
        # If no encryption_key in keepass section, use cookie key
        if not encryption_key:
            encryption_key = config.get('cookie', {}).get('key')
        
        if not password:
            logger.warning("KeePass master_password not found in authentication.yaml")
            return None
        
        # If marked as base64 encoded, decode it
        if is_encoded:
            try:
                import base64
                password = base64.b64decode(password.encode()).decode()
                logger.info("Successfully decoded KeePass password (base64)")
                return password
            except Exception as e:
                logger.error(f"Failed to decode KeePass password: {e}")
                return None
        
        # If encrypted (contains ':' separator) and encryption_key available, decrypt it
        if encryption_key and ':' in password:
            try:
                from encrypt_keepass_password import decrypt_password
                password = decrypt_password(password, encryption_key)
                logger.info("Successfully decrypted KeePass password")
            except Exception as e:
                logger.error(f"Failed to decrypt KeePass password: {e}")
                return None
        
        return password
        
    except Exception as e:
        logger.error(f"Error reading KeePass password from authentication.yaml: {e}")
        return None


def get_database_path(tenant: str, base_dir: str = None) -> str:
    """
    Get the path to the KeePass database for a specific tenant.
    Can use custom path from authentication.yaml or default to local directory.
    Automatically detects user's OneDrive path for team collaboration.
    Supports both per-tenant databases and a single shared database file.
    
    Args:
        tenant: Tenant name
        base_dir: Base directory for databases (default: from config or application directory)
    
    Returns:
        Full path to the .kdbx file
    """
    # Try to read custom database path from authentication.yaml
    database_file = None
    if base_dir is None:
        try:
            auth_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'authentication.yaml')
            if os.path.exists(auth_file_path):
                with open(auth_file_path, 'r') as file:
                    config = yaml.load(file, Loader=SafeLoader)
                    keepass_config = config.get('keepass', {})
                    custom_db_path = keepass_config.get('database_path')
                    database_file = keepass_config.get('database_file')  # Specific database filename
                    
                    if custom_db_path:
                        # Expand environment variables (e.g., %USERPROFILE%, %KEEPASS_DB_PATH%)
                        custom_db_path = os.path.expandvars(custom_db_path)
                        
                        # Auto-detect OneDrive path if using OneDrive
                        if '{onedrive}' in custom_db_path.lower():
                            onedrive_path = find_onedrive_folder()
                            if onedrive_path:
                                custom_db_path = custom_db_path.replace('{onedrive}', onedrive_path)
                                custom_db_path = custom_db_path.replace('{OneDrive}', onedrive_path)
                                logger.info(f"Auto-detected OneDrive path: {onedrive_path}")
                        
                        base_dir = custom_db_path
                        logger.info(f"Using custom database path: {base_dir}")
        except Exception as e:
            logger.warning(f"Could not read custom database path: {e}")
    
    # Default to application directory if no custom path
    if base_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_dir = os.path.join(base_dir, 'keepass_databases')
    else:
        db_dir = base_dir
    
    # Create directory if it doesn't exist
    os.makedirs(db_dir, exist_ok=True)
    
    # Use specific database file if configured, otherwise create per-tenant files
    if database_file:
        db_filename = database_file
        logger.info(f"Using shared database file: {db_filename}")
    else:
        # Sanitize tenant name for filename
        safe_tenant = "".join(c for c in tenant if c.isalnum() or c in ('_', '-')).lower()
        db_filename = f"{safe_tenant}.kdbx"
        logger.info(f"Using per-tenant database file: {db_filename}")
    
    return os.path.join(db_dir, db_filename)


def find_onedrive_folder() -> Optional[str]:
    """
    Auto-detect the user's OneDrive - Naseej for Technology folder path.
    Works for all team members regardless of their username.
    
    Returns:
        Path to OneDrive folder or None if not found
    """
    try:
        user_profile = os.path.expandvars('%USERPROFILE%')
        
        # Common OneDrive paths to check (in priority order)
        potential_paths = [
            os.path.join(user_profile, 'OneDrive - Naseej for Technology'),
            os.path.join(user_profile, 'OneDrive - Naseej'),
            os.path.join(user_profile, 'Naseej'),
            os.path.join(user_profile, 'OneDrive'),
        ]
        
        for path in potential_paths:
            if os.path.exists(path):
                logger.info(f"Found OneDrive folder: {path}")
                return path
        
        logger.warning("Could not auto-detect OneDrive folder")
        return None
        
    except Exception as e:
        logger.error(f"Error detecting OneDrive folder: {e}")
        return None


def init_keepass_db(db_path: str, master_password: str) -> PyKeePass:
    """
    Initialize or create a KeePass database.
    
    Args:
        db_path: Path to the .kdbx file
        master_password: Master password for the database
    
    Returns:
        PyKeePass instance
    
    Raises:
        CredentialsError: If password is incorrect
        Exception: If database cannot be created or opened
    """
    try:
        logger.info(f"Initializing KeePass database at: {db_path}")
        
        # Ensure the directory exists before creating the database
        db_dir = os.path.dirname(db_path)
        logger.info(f"Database directory: {db_dir}")
        
        if db_dir and not os.path.exists(db_dir):
            logger.info(f"Creating directory: {db_dir}")
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"Directory created successfully")
        else:
            logger.info(f"Directory already exists: {db_dir}")
        
        # Check if we can write to the directory
        try:
            test_file = os.path.join(db_dir, '.keepass_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logger.info("Directory is writable")
        except Exception as e:
            logger.error(f"Directory is not writable: {e}")
            raise Exception(f"Cannot write to directory {db_dir}: {e}")
        
        if os.path.exists(db_path):
            # Open existing database
            logger.info(f"Opening existing database")
            kp = PyKeePass(db_path, password=master_password)
            logger.info(f"Opened existing KeePass database: {db_path}")
        else:
            # Create new database
            logger.info(f"Creating new database")
            kp = PyKeePass(db_path, password=master_password, keyfile=None)
            logger.info(f"Database object created, saving...")
            kp.save()
            logger.info(f"Created new KeePass database: {db_path}")
        
        return kp
    except CredentialsError as e:
        logger.error(f"Incorrect password for KeePass database: {db_path}")
        raise
    except Exception as e:
        logger.error(f"Error initializing KeePass database: {e}", exc_info=True)
        raise


def ensure_group_structure(kp: PyKeePass, tenant: str) -> object:
    """
    Ensure the proper group structure exists in the database.
    
    Structure:
        Root
        └── Tenants
            └── {tenant_name}
                └── Users
    
    Args:
        kp: PyKeePass instance
        tenant: Tenant name
    
    Returns:
        The "Users" group for the tenant
    """
    # Find or create "Tenants" group
    tenants_group = kp.find_groups(name='Tenants', first=True)
    if not tenants_group:
        tenants_group = kp.add_group(kp.root_group, 'Tenants')
        logger.info("Created 'Tenants' group")
    
    # Find or create tenant-specific group
    tenant_group = kp.find_groups(name=tenant, first=True)
    if not tenant_group:
        tenant_group = kp.add_group(tenants_group, tenant)
        logger.info(f"Created '{tenant}' group")
    
    # Find or create "Users" subgroup
    users_group = None
    for subgroup in tenant_group.subgroups:
        if subgroup.name == 'Users':
            users_group = subgroup
            break
    
    if not users_group:
        users_group = kp.add_group(tenant_group, 'Users')
        logger.info(f"Created 'Users' group under '{tenant}'")
    
    return users_group


def save_credentials_to_keepass(
    username: str,
    password: str,
    tenant: str,
    title: str = None,
    notes: str = None,
    url: str = None,
    master_password: str = None
) -> Tuple[bool, Optional[str]]:
    """
    Save user credentials to the tenant's KeePass database.
    
    Args:
        username: Username to save
        password: Password to save
        tenant: Tenant name (determines which database to use)
        title: Optional entry title (defaults to username)
        notes: Optional notes for the entry
        url: Optional URL for the entry
        master_password: Optional master password (uses env var if not provided)
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        # Get master password
        if master_password is None:
            master_password = get_keepass_master_password()
        
        if not master_password:
            return False, "KeePass master password not configured (set KEEPASS_MASTER_PASSWORD environment variable)"
        
        # Get database path
        db_path = get_database_path(tenant)
        
        # Initialize database
        kp = init_keepass_db(db_path, master_password)
        
        # Ensure group structure exists
        users_group = ensure_group_structure(kp, tenant)
        
        # Check if entry already exists
        existing_entry = kp.find_entries(username=username, group=users_group, first=True)
        
        if existing_entry:
            # Update existing entry
            existing_entry.password = password
            if title:
                existing_entry.title = title
            if notes:
                existing_entry.notes = notes
            if url:
                existing_entry.url = url
            logger.info(f"Updated existing entry for user '{username}' in tenant '{tenant}'")
        else:
            # Create new entry
            entry_title = title or username
            kp.add_entry(
                users_group,
                title=entry_title,
                username=username,
                password=password,
                notes=notes or "",
                url=url or ""
            )
            logger.info(f"Created new entry for user '{username}' in tenant '{tenant}'")
        
        # Save database
        kp.save()
        
        return True, None
        
    except CredentialsError:
        error_msg = "Invalid KeePass master password"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error saving to KeePass: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_keepass_config() -> Dict[str, any]:
    """
    Get KeePass configuration.
    
    Returns:
        Dictionary with configuration:
        - enabled: Whether KeePass integration is enabled
        - master_password: Master password from environment
        - has_password: Boolean indicating if password is configured
    """
    master_password = get_keepass_master_password()
    
    return {
        'enabled': master_password is not None,
        'master_password': master_password,
        'has_password': master_password is not None
    }


def test_keepass_connection(tenant: str = "test") -> Tuple[bool, Optional[str]]:
    """
    Test KeePass database connection and configuration.
    
    Args:
        tenant: Tenant name to test with (default: 'test')
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        master_password = get_keepass_master_password()
        if not master_password:
            return False, "KEEPASS_MASTER_PASSWORD environment variable not set"
        
        db_path = get_database_path(tenant)
        
        # Try to initialize database
        kp = init_keepass_db(db_path, master_password)
        
        # Test group creation
        ensure_group_structure(kp, tenant)
        
        # Count entries
        entry_count = len(kp.entries)
        
        return True, f"Connection successful! Database: {db_path}, Entries: {entry_count}"
        
    except CredentialsError:
        return False, "Invalid master password"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"
