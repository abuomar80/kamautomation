"""
Backup script to create a full backup of the codebase before testing
"""
import os
import shutil
from datetime import datetime
import json

def create_backup():
    """Create a timestamped backup of all code files"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backup_pre_cypress_{timestamp}"
    
    # Files and directories to backup
    items_to_backup = [
        # Main Python files
        "Homepage.py",
        "legacy_session_state.py",
        "extras.py",
        "clone_functions.py",
        "permissions.py",
        "Upload.py",
        "template_generator.py",
        
        # Configuration modules
        "Material_types.py",
        "Statistical_Codes.py",
        "Location.py",
        "Service_points.py",
        "Department.py",
        "Calendar.py",
        "Column_Configuration.py",
        "user_group.py",
        "Smtp.py",
        "Notices.py",
        
        # Fee/Fine modules
        "FeeFineOwner.py",
        "FeeFine.py",
        "Waives.py",
        "PaymentMethods.py",
        "Refunds.py",
        "LoanPolicies.py",
        
        # Other modules
        "z3950.py",
        "UserImport.py",
        "Tenant_Backup.py",
        "Clean_Marc.py",
        
        # Pages directory
        "pages",
        
        # Configuration files
        "requirements.txt",
        "runtime.txt",
        "style.css",
        "authentication.yaml.example",
        
        # Documentation
        "README.md",
        "QUICK_START.md",
        "PROJECT_STRUCTURE.md",
        "CONFIGURATION_TEMPLATE.md",
        
        # Images
        "medad_logo_eng.png",
        "Medad_logo.jpg",
    ]
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    print(f"📦 Creating backup in: {backup_dir}")
    
    backed_up = []
    skipped = []
    errors = []
    
    for item in items_to_backup:
        try:
            source_path = item
            dest_path = os.path.join(backup_dir, item)
            
            if os.path.isfile(source_path):
                # Create directory structure if needed
                os.makedirs(os.path.dirname(dest_path) if os.path.dirname(dest_path) else backup_dir, exist_ok=True)
                shutil.copy2(source_path, dest_path)
                backed_up.append(f"✅ {item}")
            elif os.path.isdir(source_path):
                # Copy entire directory
                dest_dir = os.path.join(backup_dir, os.path.basename(source_path))
                if os.path.exists(dest_dir):
                    shutil.rmtree(dest_dir)
                shutil.copytree(source_path, dest_dir, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git'))
                backed_up.append(f"✅ {item}/ (directory)")
            else:
                skipped.append(f"⚠️  {item} (not found)")
        except Exception as e:
            errors.append(f"❌ {item}: {str(e)}")
    
    # Create backup manifest
    manifest = {
        "backup_timestamp": timestamp,
        "backup_directory": backup_dir,
        "backed_up_items": len(backed_up),
        "skipped_items": len(skipped),
        "errors": len(errors),
        "files": backed_up,
        "skipped": skipped,
        "error_list": errors
    }
    
    manifest_path = os.path.join(backup_dir, "backup_manifest.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*60)
    print("📋 BACKUP SUMMARY")
    print("="*60)
    print(f"Backup Directory: {backup_dir}")
    print(f"✅ Backed up: {len(backed_up)} items")
    if skipped:
        print(f"⚠️  Skipped: {len(skipped)} items")
    if errors:
        print(f"❌ Errors: {len(errors)} items")
    print("="*60)
    
    if skipped:
        print("\n⚠️  Skipped items:")
        for item in skipped:
            print(f"  {item}")
    
    if errors:
        print("\n❌ Errors:")
        for item in errors:
            print(f"  {item}")
    
    print(f"\n✅ Backup complete! Manifest saved to: {manifest_path}")
    return backup_dir

if __name__ == "__main__":
    backup_dir = create_backup()
    print(f"\n💡 To restore from backup, copy files from: {backup_dir}")

