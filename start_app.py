#!/usr/bin/env python3
"""
DOCX Translator App Launcher
This script ensures the app runs with the correct Python environment.
"""

import os
import subprocess
import sys


def main():
    print("🚀 Starting DOCX Translator App...")
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")

    # Check if we're in a conda environment
    conda_env = os.environ.get("CONDA_DEFAULT_ENV", "Not in conda")
    print(f"Conda environment: {conda_env}")

    # Install dependencies
    print("📦 Installing/updating dependencies...")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        )
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return

    # Run the Streamlit app
    print("🌐 Starting Streamlit app...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n👋 App stopped by user")
    except Exception as e:
        print(f"❌ Error running app: {e}")


if __name__ == "__main__":
    main()
