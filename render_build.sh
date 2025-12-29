#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Node.js dependencies and build frontend
echo "Building Frontend..."
npm install --prefix frontend
npm run build --prefix frontend

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt
