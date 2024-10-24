# File Search and Deletion Script

This Python script allows users to search for files in a specified directory (including subdirectories) based on keywords in the filenames, and optionally delete them.

## Features

- Recursively searches through a specified directory and its subdirectories
- Searches for files whose names contain any of the specified keywords (case-insensitive)
- Provides an option to delete files matching the keywords
- Logs all actions and results to both the console and a JSON file

## Requirements

- Python 3.x
- pysmb package

## Installation

1. Clone or download this repository to your local machine.

2. Open a terminal and navigate to the directory containing the script.

3. Install the required package using pip:

   ```
   pip install pysmb
   ```

   Alternatively, if you have a `requirements.txt` file, you can install all required packages at once:

   ```
   pip install -r requirements.txt
   ```

## Usage

1. After installing the required package, run the script using Python:

   ```
   python3 main.py
   ```

2. When prompted, enter:

   - The full path of the directory you want to search
   - Keywords to search for in filenames, separated by commas
   - Choose the mode: 'search' or 'delete'

3. The script will display its progress and results in the terminal.

## Modes

### Search Mode

- Lists files matching the keywords
- Provides an option to delete the found files after displaying the results

### Delete Mode

- Directly deletes files matching the keywords without listing them first

## Example

This will search the Downloads folder and its subdirectories for files containing "temp", "old", or "backup" in their names and either list them or delete them based on the chosen mode.

## Caution

- The delete mode permanently removes files. Use with caution and ensure you have backups of important data.
- Double-check the directory path and keywords before confirming the deletion process.
- The script requires appropriate permissions to read and delete files in the specified directory.

## Logging

- All actions and results are logged to the console.
- A detailed log is saved as a JSON file named `file_deletion_log_YYYYMMDD_HHMMSS.json` in the same directory as the script.
- The JSON log includes information about checked files, deleted files, and a summary of the operation.

## Customization

You can modify the logging format or behavior by editing the `setup_logging()` function in the script.

## License

MIT
