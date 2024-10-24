import os
import json
import logging
from datetime import datetime
from urllib.parse import urlparse
import socket
from smb.SMBConnection import SMBConnection

def setup_logging():
    # Set up console logger
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console)

def connect_to_smb(smb_url, username, password):
    parsed_url = urlparse(smb_url)
    server_name = parsed_url.hostname
    share_name = parsed_url.path.strip('/').split('/')[0]
    
    print(f"Attempting to connect to server: {server_name}")
    
    try:
        ip_address = socket.gethostbyname(server_name)
        print(f"Resolved IP address: {ip_address}")
    except socket.gaierror as e:
        print(f"Unable to resolve hostname: {e}")
        print("Please check if the hostname is correct and your DNS settings are properly configured.")
        return None, None, None, None

    try:
        conn = SMBConnection(username, password, 'local-machine', server_name, use_ntlm_v2=True)
        if conn.connect(ip_address, 139):
            print("Successfully connected to SMB server")
            return conn, share_name, '/'.join(parsed_url.path.strip('/').split('/')[1:]), ip_address
        else:
            print("Failed to connect to SMB server")
            print("Please check if the server is reachable and the SMB service is running.")
            return None, None, None, None
    except Exception as e:
        print(f"Error connecting to SMB server: {e}")
        print("This could be due to firewall settings, incorrect credentials, or server configuration.")
        return None, None, None, None

def is_smb_path(path):
    return path.lower().startswith('smb://')

def search_files_with_keywords(conn, share_name, directory, keywords, is_smb=False):
    setup_logging()
    logger = logging.getLogger('')

    matches = {}
    total_files = 0

    def search_smb_directory(current_path):
        nonlocal total_files
        try:
            file_list = conn.listPath(share_name, current_path)
            for f in file_list:
                if f.filename in ['.', '..']:
                    continue
                file_path = os.path.join(current_path, f.filename)
                if f.isDirectory:
                    search_smb_directory(file_path)
                else:
                    for keyword in keywords:
                        if keyword.lower() in f.filename.lower():
                            if keyword not in matches:
                                matches[keyword] = []
                            matches[keyword].append(file_path)
                    total_files += 1
        except Exception as e:
            logger.error(f"Error accessing {current_path}: {str(e)}")

    def search_local_directory(current_path):
        nonlocal total_files
        try:
            for root, _, files in os.walk(current_path):
                for file in files:
                    total_files += 1
                    file_path = os.path.join(root, file)
                    for keyword in keywords:
                        if keyword.lower() in file.lower():
                            if keyword not in matches:
                                matches[keyword] = []
                            matches[keyword].append(file_path)
        except Exception as e:
            logger.error(f"Error accessing {current_path}: {str(e)}")

    if is_smb:
        search_smb_directory(directory)
    else:
        search_local_directory(directory)

    for keyword, files in matches.items():
        logger.info(f'"{keyword}": {len(files)} results')
        for file in files:
            logger.info(f'  - {file}')

    summary = f"Processed {total_files} files. Found matches for {len(matches)} keywords."
    logger.info(summary)

    return matches

def delete_files_with_keywords(conn, share_name, directory, keywords, is_smb=False):
    setup_logging()
    logger = logging.getLogger('')

    deleted_count = 0
    total_files = 0
    log_data = {
        "checked_files": [],
        "deleted_files": [],
        "summary": {}
    }

    def process_smb_directory(current_path):
        nonlocal deleted_count, total_files
        try:
            file_list = conn.listPath(share_name, current_path)
            for f in file_list:
                if f.filename in ['.', '..']:
                    continue
                file_path = os.path.join(current_path, f.filename)
                
                logger.info(f"Checking file: {file_path}")
                
                file_info = {
                    "path": file_path,
                    "checked_at": datetime.now().isoformat()
                }
                
                try:
                    if f.isDirectory:
                        process_smb_directory(file_path)
                    else:
                        if any(keyword.lower() in f.filename.lower() for keyword in keywords):
                            conn.deleteFiles(share_name, file_path)
                            logger.info(f"Deleted: {file_path}")
                            file_info["deleted"] = True
                            file_info["deletion_reason"] = "Keyword match"
                            log_data["deleted_files"].append(file_info)
                            deleted_count += 1
                        else:
                            file_info["deleted"] = False
                        log_data["checked_files"].append(file_info)
                        total_files += 1
                except Exception as e:
                    error_message = f"Error processing {file_path}: {str(e)}"
                    logger.error(error_message)
                    file_info["error"] = error_message
                    log_data["checked_files"].append(file_info)
        except Exception as e:
            logger.error(f"Error accessing {current_path}: {str(e)}")

    def process_local_directory(current_path):
        nonlocal deleted_count, total_files
        try:
            for root, _, files in os.walk(current_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    logger.info(f"Checking file: {file_path}")
                    
                    file_info = {
                        "path": file_path,
                        "checked_at": datetime.now().isoformat()
                    }
                    
                    try:
                        if any(keyword.lower() in file.lower() for keyword in keywords):
                            os.remove(file_path)
                            logger.info(f"Deleted: {file_path}")
                            file_info["deleted"] = True
                            file_info["deletion_reason"] = "Keyword match"
                            log_data["deleted_files"].append(file_info)
                            deleted_count += 1
                        else:
                            file_info["deleted"] = False
                        log_data["checked_files"].append(file_info)
                        total_files += 1
                    except Exception as e:
                        error_message = f"Error processing {file_path}: {str(e)}"
                        logger.error(error_message)
                        file_info["error"] = error_message
                        log_data["checked_files"].append(file_info)
        except Exception as e:
            logger.error(f"Error accessing {current_path}: {str(e)}")

    if is_smb:
        process_smb_directory(directory)
    else:
        process_local_directory(directory)

    summary = f"Processed {total_files} files. Deleted {deleted_count} files."
    logger.info(summary)
    
    log_data["summary"] = {
        "total_files": total_files,
        "deleted_files": deleted_count,
        "keywords": keywords,
        "directory": directory,
        "timestamp": datetime.now().isoformat()
    }

    # Write log data to JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"file_deletion_log_{timestamp}.json"
    with open(json_filename, 'w') as json_file:
        json.dump(log_data, json_file, indent=2)

    logger.info(f"Log data written to {json_filename}")

def main():
    while True:
        path = input("Enter the path (local directory or SMB URL): ")
        
        if is_smb_path(path):
            username = input("Enter SMB username: ")
            password = input("Enter SMB password: ")
            conn, share_name, directory, ip_address = connect_to_smb(path, username, password)
            if not conn:
                retry = input("Connection failed. Do you want to try again? (yes/no): ").lower()
                if retry != 'yes':
                    print("Exiting program.")
                    return
                continue
            is_smb = True
        else:
            if not os.path.exists(path):
                print("The specified local path does not exist.")
                retry = input("Do you want to try again? (yes/no): ").lower()
                if retry != 'yes':
                    print("Exiting program.")
                    return
                continue
            conn, share_name, directory = None, None, path
            is_smb = False
        
        break  # If we reach here, we have a valid path

    keywords = input("Enter keywords separated by commas: ").split(',')
    
    matches = search_files_with_keywords(conn, share_name, directory, keywords, is_smb)

    if not any(matches.values()):
        print("No files found matching the given keywords.")
    else:
        for keyword, files in matches.items():
            print(f'"{keyword}": {len(files)} results')
            for file in files:
                print(f'  - {file}')
        
        delete_choice = input("Do you want to delete these files? (yes/no): ").lower()
        if delete_choice == 'yes':
            delete_files_with_keywords(conn, share_name, directory, keywords, is_smb)

    if conn:
        conn.close()

if __name__ == "__main__":
    main()
