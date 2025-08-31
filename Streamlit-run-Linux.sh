#!/bin/bash

# Script: run_app.sh
# Runs generate_secrets.py, then starts streamlit app

# Exit on any error
set -e

# Go to the directory of the script
cd "$(dirname "$0")" || { echo "Failed to enter script directory"; exit 1; }

echo "Running generate_secrets.py..."
python3 generate_secrets.py

if [ $? -ne 0 ]; then
    echo "Error: generate_secrets.py failed!"
    exit 1
fi

echo "Starting Streamlit app (streamlit_app_v2.py)..."
echo "Press Ctrl+C to stop the server."

# Run Streamlit app
python3 -m streamlit run streamlit_app_v2.py

# This will run until user presses Ctrl+C
echo "Streamlit app stopped."