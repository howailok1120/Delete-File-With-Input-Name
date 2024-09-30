import os
import json
import logging
from datetime import datetime

def setup_logging():
    # Set up console logger
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(message)s')
    console.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console)

def delete_files_with_keywords(directory, keywords):
    setup_logging()
    logger = logging.getLogger('')

    deleted_count = 0
    total_files = 0
    log_data = {
        "checked_files": [],
        "deleted_files": [],
        "summary": {}
    }

    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, directory)
            
            logger.info(f"Checking file: {relative_path}")
            
            file_info = {
                "path": relative_path,
                "checked_at": datetime.now().isoformat()
            }
            
            try:
                # Check if any of the keywords are in the filename
                if any(keyword.lower() in filename.lower() for keyword in keywords):
                    os.remove(file_path)
                    logger.info(f"Deleted: {relative_path}")
                    file_info["deleted"] = True
                    file_info["deletion_reason"] = "Keyword match"
                    log_data["deleted_files"].append(file_info)
                    deleted_count += 1
                else:
                    file_info["deleted"] = False
                log_data["checked_files"].append(file_info)
            except Exception as e:
                error_message = f"Error processing {relative_path}: {str(e)}"
                logger.error(error_message)
                file_info["error"] = error_message
                log_data["checked_files"].append(file_info)
            
            total_files += 1

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

# Get user input and call the function
directory = input("Enter the directory path: ")
keywords = input("Enter keywords separated by commas: ").split(',')
delete_files_with_keywords(directory, keywords)