# lv1-report

Report generator for Waves eMotion LV1 sessions.

This script extracts information from saved session (.emo) files for reference outside of the LV1 software.

As of this release, it supports the export of routing/patching information (Inputs, Outputs, and Device-to-Device routing) exported to an Excel (.xlsx) file.

## Requirements

-   A UNIX-like environemnt, such as:
    -   Linux
    -   macOS X
    -   Windows running Git Bash
-   Python (3.5 or greater)
    -   virtualenv support preferred
    -   in Windows, be sure you chose to add python to PATH at installation. Furthermore, in Windows 10, you may need to 'Manage app execution aliases' and uncheck the Python options.
-   A session (.emo) file from Waves eMotion LV1, version 11 or greater.

## Installation

    sh build.sh
    # in Linux/macOS/etc:
    source venv/bin/activate

    # in Windows:
    source venv/Scripts/activate

## Usage

    lv1report [OPTIONS] SESSION_FILE
    Options:
      -f, --report-file PATH  Specify report file path, otherwise one will be
                              generated in the same directory as the session file.

## Examples

    lv1report "/c/Users/Public\Waves Audio\eMotion\Sessions/my_last_show.emo"

This will read the session "my_last_show.emo" from the default session location in Windows.
It will then create an Excel file in the same folder, based on the name "my_last_show", along with the current date & time.

    lv1report /Users/Shared/Waves/eMotion/Sessions/my_last_show.emo -f ~/Desktop/my_report.xlsx

This will read the session "my_last_show.emo" from the default session location on a Mac.
It will then create an Excel file called "my_report.xlsx" on the Desktop.

## Notes

If you are running this in a python virtual environment (the default if you run build.sh to install), be sure you activate it ("source venv...") before running lv1-report!
