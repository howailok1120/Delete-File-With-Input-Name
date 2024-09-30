import os
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    filename='file_deletion_log.txt',
                    filemode='w')

# Create a console handler
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

def delete_files_with_keywords(directory, keywords):
    # Ensure the directory path ends with a slash
    if not directory.endswith('/'):
        directory += '/'

    # Counter for deleted files
    deleted_count = 0

    logging.info(f"\nSearching in directory: {directory}")
    logging.info(f"Keywords: {', '.join(keywords)}\n")
    print(f"\nSearching in directory: {directory}")
    print(f"Keywords: {', '.join(keywords)}\n")

    for root, dirs, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            relative_path = os.path.relpath(file_path, directory)
            
            logging.info(f"Checking file: {relative_path}")
            print(f"Checking file: {relative_path}")
            
            try:
                # Check if any of the keywords are in the filename
                if any(keyword.lower() in filename.lower() for keyword in keywords):
                    os.remove(file_path)
                    logging.info(f"Deleted: {relative_path}")
                    print(f"Deleted: {relative_path}")
                    deleted_count += 1
                else:
                    logging.debug(f"No keyword match in filename: {relative_path}")
            except Exception as e:
                error_message = f"Error processing {relative_path}: {str(e)}"
                logging.error(error_message)
                print(error_message)

    summary = f"\nTotal files deleted: {deleted_count}"
    logging.info(summary)
    print(summary)

# Get user input
directory = input("Enter the directory path: ").strip()
keywords = input("Enter keywords (separated by commas): ").split(',')

# Strip whitespace from keywords
keywords = [k.strip() for k in keywords]

# Call the function
delete_files_with_keywords(directory, keywords)

logging.info("File deletion process completed.")