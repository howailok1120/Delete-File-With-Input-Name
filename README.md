# File Deletion Script

This Python script allows users to delete files in a specified directory (including subdirectories) based on keywords in the filenames.

## Features

- Recursively searches through a specified directory and its subdirectories
- Deletes files whose names contain any of the specified keywords (case-insensitive)
- Logs all actions and errors to both a file and the console

## Requirements

- Python 3.x

## Usage

1. Clone or download this repository to your local machine.

2. Open a terminal and navigate to the directory containing the script.

3. Run the script using Python:

   ```
   python3 main.py
   ```

4. When prompted, enter:

   - The full path of the directory you want to search
   - Keywords to search for in filenames, separated by commas

5. The script will display its progress and results in the terminal and log them to a file named `file_deletion_log.txt`.

## Example

This will search the Downloads folder and its subdirectories for files containing "temp", "old", or "backup" in their names and delete them.

## Caution

- This script permanently deletes files. Use with caution and ensure you have backups of important data.
- Double-check the directory path and keywords before confirming the deletion process.
- The script requires appropriate permissions to read and delete files in the specified directory.

## Logging

- All actions and errors are logged to `file_deletion_log.txt` in the same directory as the script.
- The log file is overwritten each time the script runs.

## Customization

You can modify the logging level, format, or file name by editing the logging configuration in the script.

## License

MIT License

## Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page] if you want to contribute.

## Author

Leo Ho
