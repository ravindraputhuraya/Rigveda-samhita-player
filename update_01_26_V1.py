#!/usr/bin/env python3
"""
Rigveda JSON Updater - Smart Version Chain Manager
Cross-platform updater for Windows, Linux, and macOS
"""

import os
import sys
import zipfile
import shutil
import glob
import re
from datetime import datetime
from pathlib import Path

# ============================================================================
# DEBUG MODE: Set to True to see detailed error messages
# ============================================================================
DEBUG_MODE = False

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{'=' * 77}{Colors.ENDC}")
    print(f"{Colors.BOLD}{text.center(77)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{'=' * 77}{Colors.ENDC}\n")

def print_success(text):
    print(f"{Colors.GREEN}  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}  {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.YELLOW}  {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.BLUE}  {text}{Colors.ENDC}")

def scan_update_files():
    """Scan for update*.zip files"""
    update_files = sorted(glob.glob("update*.zip"))
    return update_files

def extract_version(filename):
    """Extract version from filename (update_01_26_V3.zip -> V3)"""
    # Remove .zip extension
    name = filename.replace('.zip', '')
    # Split by underscore and get last token
    tokens = name.split('_')
    if tokens:
        return tokens[-1]
    return None

def find_latest_mandala(mandala_num):
    """Find the latest version of a specific Mandala"""
    # Check for base R2 file
    base_file = f"M{mandala_num}_R2.zip"
    latest_file = None
    
    if os.path.exists(base_file):
        latest_file = base_file
    
    # Check for versioned files
    pattern = f"M{mandala_num}_R2_V*.zip"
    versioned_files = glob.glob(pattern)
    
    if versioned_files:
        # Sort to get the last one (alphabetically, which works for V1, V2, V3...)
        versioned_files.sort()
        latest_file = versioned_files[-1]
    
    return latest_file

def log_message(log_file, message):
    """Append message to log file"""
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')

def extract_zip(zip_path, extract_to):
    """Extract a ZIP file"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        print_error(f"Failed to extract {zip_path}: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return False

def create_zip(source_dir, output_path):
    """Create a ZIP file from a directory"""
    try:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(source_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, source_dir)
                    zipf.write(file_path, arcname)
        return True
    except Exception as e:
        print_error(f"Failed to create {output_path}: {e}")
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        return False

def process_mandala(mandala_num, source_zip, update_package, target_version, log_file):
    """Process a single Mandala update"""
    output_zip = f"M{mandala_num}_R2_{target_version}.zip"
    mandala_folder = f"M{mandala_num}"
    
    print(f"Processing M{mandala_num}: {source_zip} --> {output_zip}")
    
    # Create backup of source file
    backup_file = f"{source_zip}.backup"
    try:
        print_info(f"Creating backup: {backup_file}")
        shutil.copy2(source_zip, backup_file)
        print_success("Backup created successfully")
    except Exception as e:
        print_warning(f"Could not create backup: {e}")
    
    # Check if output already exists
    if os.path.exists(output_zip):
        print_warning(f"{output_zip} already exists. Skipping.")
        log_message(log_file, f"  - SKIPPED: {source_zip} (output already exists)")
        return False
    
    # Create temporary directories
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix='rigveda_update_')
    update_temp = tempfile.mkdtemp(prefix='rigveda_update_src_')
    
    try:
        # Extract source ZIP
        print_info(f"Extracting source: {source_zip}...")
        if not extract_zip(source_zip, temp_dir):
            log_message(log_file, f"  - FAILED: {source_zip} (extraction error)")
            return False
        
        # Extract update package
        print_info("Extracting update package...")
        if not extract_zip(update_package, update_temp):
            log_message(log_file, f"  - FAILED: {source_zip} (update extraction error)")
            return False
        
        # Apply JSON updates
        print_info(f"Applying JSON updates for {mandala_folder}...")
        update_folder_path = os.path.join(update_temp, mandala_folder)
        
        if os.path.exists(update_folder_path):
            json_files = glob.glob(os.path.join(update_folder_path, "*.json"))
            
            if json_files:
                dest_folder = os.path.join(temp_dir, mandala_folder)
                os.makedirs(dest_folder, exist_ok=True)
                
                for json_file in json_files:
                    dest_file = os.path.join(dest_folder, os.path.basename(json_file))
                    shutil.copy2(json_file, dest_file)
                
                print_info(f"Updated {len(json_files)} JSON file(s)")
                log_message(log_file, f"  - Updated {len(json_files)} JSON files")
            else:
                print_info(f"No JSON files in update for {mandala_folder}")
                log_message(log_file, f"  - INFO: No JSON files to update")
        else:
            print_info(f"{mandala_folder} not in update package (keeping as-is)")
            log_message(log_file, f"  - INFO: No updates for this Mandala")
        
        # Create output ZIP
        print_info(f"Creating {output_zip}...")
        if not create_zip(temp_dir, output_zip):
            log_message(log_file, f"  - FAILED: {source_zip} (compression error)")
            return False
        
        print_success(f"SUCCESS! Created {output_zip}")
        log_message(log_file, f"  {source_zip} --> {output_zip} [OK]")
        return True
        
    finally:
        # Cleanup temporary directories
        shutil.rmtree(temp_dir, ignore_errors=True)
        shutil.rmtree(update_temp, ignore_errors=True)

def main():
    """Main function"""
    os.system('clear' if os.name == 'posix' else 'cls')
    
    print_header("Rigveda JSON Updater - Smart Version Chain Manager")
    
    # Scan for update files
    print("Scanning for available updates...\n")
    update_files = scan_update_files()
    
    if not update_files:
        print_error("No update*.zip files found in this folder!")
        print("\nPlease download an update file with format: update_MM_YY_VX.zip")
        print("Example: update_01_26_V3.zip\n")
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Display available updates
    for i, file in enumerate(update_files, 1):
        print(f"  [{i}] {file}")
    
    print(f"\nFound {len(update_files)} update package(s).\n")
    
    # User selection
    if len(update_files) == 1:
        selected_index = 0
        print(f"Only one update found. Using: {update_files[0]}")
    else:
        while True:
            try:
                choice = input(f"Select update to apply (enter number 1-{len(update_files)}): ")
                selected_index = int(choice) - 1
                if 0 <= selected_index < len(update_files):
                    break
                else:
                    print_error("Invalid selection. Try again.")
            except ValueError:
                print_error("Please enter a number.")
            except KeyboardInterrupt:
                print("\n\nUpdate cancelled.")
                sys.exit(0)
    
    selected_update = update_files[selected_index]
    print(f"\nSelected: {selected_update}\n")
    
    # Extract version
    version = extract_version(selected_update)
    if not version:
        print_error("Could not extract version from filename.")
        print("Expected format: update_MM_YY_VX.zip")
        print("Example: update_01_26_V3.zip\n")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print(f"Target version: {version}\n")
    
    # Scan for Mandala files
    print("Scanning for Mandala files...\n")
    mandala_sources = {}
    
    for mandala_num in range(1, 11):
        latest = find_latest_mandala(mandala_num)
        if latest:
            mandala_sources[mandala_num] = latest
            print(f"  M{mandala_num}: {latest} --> M{mandala_num}_R2_{version}.zip")
    
    print()
    
    if not mandala_sources:
        print_error("No Mandala files found (M1_R2.zip, M1_R2_V*.zip, etc.)")
        print("Make sure your Mandala files are in this folder.\n")
        input("Press Enter to exit...")
        sys.exit(1)
    
    print(f"Found {len(mandala_sources)} Mandala(s) to update.\n")
    
    print("This will:")
    print("  - Use the LATEST available version of each Mandala as source")
    print(f"  - Apply updates from: {selected_update}")
    print(f"  - Create new files with version: {version}")
    print("\nYour existing files will NOT be modified (safe operation).\n")
    
    # Confirm
    try:
        proceed = input("Proceed with update? (Y/N): ").strip().upper()
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled.")
        sys.exit(0)
    
    if proceed != 'Y':
        print("\nUpdate cancelled.")
        sys.exit(0)
    
    # Start update process
    print_header("Starting update process...")
    
    # Initialize log
    log_file = "update_log.txt"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    log_message(log_file, "=" * 77)
    log_message(log_file, f"Update Log - {timestamp}")
    log_message(log_file, "=" * 77)
    log_message(log_file, f"Update Package: {selected_update}")
    log_message(log_file, f"Target Version: {version}")
    log_message(log_file, "")
    
    # Process each Mandala
    success_count = 0
    failed_count = 0
    
    for mandala_num, source_zip in mandala_sources.items():
        if process_mandala(mandala_num, source_zip, selected_update, version, log_file):
            success_count += 1
        else:
            failed_count += 1
        print()
    
    # Summary
    print_header("UPDATE COMPLETE")
    
    print("Summary:")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {len(mandala_sources)}")
    print()
    print(f"New files created with _{version} suffix.")
    print(f"Update log saved to: {log_file}")
    print()
    
    if failed_count > 0:
        print_warning("Some updates failed. Check the log for details.")
        print()
    
    log_message(log_file, "=" * 77)
    log_message(log_file, f"Summary: {success_count} successful, {failed_count} failed")
    log_message(log_file, "=" * 77)
    log_message(log_file, "")
    
    # Show system notification (platform-specific)
    try:
        show_notification(success_count, failed_count, len(mandala_sources))
    except:
        pass  # Notifications are optional
    
    input("Press Enter to exit...")

def show_notification(success, failed, total):
    """Show a system notification (platform-specific)"""
    message = f"Rigveda Update Complete!\n\nSuccess: {success}\nFailed: {failed}\nTotal: {total}\n\nSee update_log.txt for details."
    
    if sys.platform == 'win32':
        # Windows notification
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, "Update Complete", 0x40)
        except:
            pass
    elif sys.platform == 'darwin':
        # macOS notification
        try:
            os.system(f'''osascript -e 'display notification "{message}" with title "Rigveda Updater"' ''')
        except:
            pass
    else:
        # Linux notification (using notify-send if available)
        try:
            os.system(f'notify-send "Rigveda Updater" "{message}"')
        except:
            pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nUpdate cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print_error(f"\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")
        sys.exit(1)
