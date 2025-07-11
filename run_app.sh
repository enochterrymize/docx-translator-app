#!/bin/bash

# Ensure we're in the right directory
cd "$(dirname "$0")"

# Check if we're in a conda environment
if [[ "$CONDA_DEFAULT_ENV" != "" ]]; then
    echo "Running in conda environment: $CONDA_DEFAULT_ENV"
else
    echo "Warning: Not in a conda environment"
fi

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the app with the current Python interpreter
echo "Starting Streamlit app..."
python -m streamlit run app.py 
