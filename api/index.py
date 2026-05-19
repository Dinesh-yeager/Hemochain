"""
Vercel Serverless Function Entry Point
Wraps the Flask application for Vercel's Python runtime.
"""
import sys
import os

# Add the project root and backend to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
backend_path = os.path.join(project_root, "backend")
sys.path.insert(0, project_root)
sys.path.insert(0, backend_path)

# Load environment variables from backend/.env if present
from dotenv import load_dotenv
env_path = os.path.join(backend_path, ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

from backend.app import create_app

app = create_app()

# Vercel expects the WSGI app to be named 'app'
# This is the entry point that Vercel's Python runtime calls
