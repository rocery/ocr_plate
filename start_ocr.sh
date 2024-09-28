#!/bin/bash

# Navigate to the ocr directory
cd
cd ocr_plate || exit

# Activate the virtual environment
source ./venv/bin/activate

# Check if port 5000 is in use and kill the process if it is
if fuser 5000/tcp > /dev/null 2>&1; then
    echo "Port 5001 is in use. Killing the process..."
    fuser -k 5000/tcp
fi

# Run the Python application in the background and redirect output to a log file
python3 app.py > app.log 2>&1 &
