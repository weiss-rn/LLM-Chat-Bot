#!/bin/bash

cd cli-only

if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "Running generate_secrets.py..."
python3 generate_secrets.py

echo "Running app.py..."
python3 app.py

cd ..