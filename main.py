import os
import json
import logging
from datetime import datetime
from urllib.parse import urlparse
import socket
from smb.SMBConnection import SMBConnection
import getpass
import re

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

    def keyword_matches(filename, keyword):
        # Check for exact match of "-{keyword}-"
        if f"-{keyword}-" in filename.lower():
            return True
        
        # Check for standalone word
        word_pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        return bool(re.search(word_pattern, filename.lower()))

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
                        if keyword_matches(f.filename, keyword):
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
                        if keyword_matches(file, keyword):
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

    def keyword_matches(filename, keyword):
        # Check for exact match of "-{keyword}-"
        if f"-{keyword}-" in filename.lower():
            return True
        
        # Check for standalone word
        word_pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
        return bool(re.search(word_pattern, filename.lower()))

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
                        if any(keyword_matches(f.filename, keyword) for keyword in keywords):
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
                        if any(keyword_matches(file, keyword) for keyword in keywords):
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
        mode = input("Choose mode (1 for local path, 2 for SMB): ")
        
        if mode == "1":
            is_smb = False
            path = input("Enter the local directory path: ")
            if not os.path.exists(path):
                print("The specified local path does not exist.")
                return
            conn, share_name, directory = None, None, path
        elif mode == "2":
            is_smb = True
            smb_connections = []  # This list is empty as per your observation
            
            if not smb_connections:
                print("No existing SMB connections found.")
                choice = 'n'
            else:
                print("Existing SMB connections:")
                for i, connection in enumerate(smb_connections, 1):
                    print(f"{i}. {connection['server']} - {connection['share']}")
                
                choice = input("Enter the number of the SMB connection to use, or 'n' for a new connection: ")
            
            if choice.lower() == 'n':
                path = input("Enter the SMB URL: ")
                username = input("Enter SMB username: ")
                password = getpass.getpass("Enter SMB password: ")
                conn, share_name, directory, ip_address = connect_to_smb(path, username, password)
                if not conn:
                    print("Connection failed. Exiting program.")
                    return
            else:
                try:
                    selected_conn = smb_connections[int(choice) - 1]
                    conn, share_name, directory, ip_address = connect_to_smb(
                        selected_conn['server'], 
                        selected_conn['username'], 
                        selected_conn['password']
                    )
                    if not conn:
                        print("Connection failed. Exiting program.")
                        return
                except (ValueError, IndexError):
                    print("Invalid selection. Exiting program.")
                    return
        else:
            print("Invalid mode selection. Exiting program.")
            return

        keywords = input("Enter keywords separated by commas: ").split(',')
        
        matches = search_files_with_keywords(conn, share_name, directory, keywords, is_smb)

        if not any(matches.values()):
            print("No files found matching the given keywords.")
        else:
            total_matches = sum(len(files) for files in matches.values())
            for keyword, files in matches.items():
                print(f'"{keyword}": {len(files)} results')
                for file in files:
                    print(f'  - {file}')
            
            print(f"\nTotal files matching keywords: {total_matches}")
            delete_choice = input(f"Do you want to delete these {total_matches} files? (yes/no): ").lower()
            if delete_choice == 'yes':
                delete_files_with_keywords(conn, share_name, directory, keywords, is_smb)

        if conn:
            conn.close()

        another_search = input("Do you want to perform another search? (yes/no): ").lower()
        if another_search != 'yes':
            break

    print("Program finished. Goodbye!")

if __name__ == "__main__":
    main()
