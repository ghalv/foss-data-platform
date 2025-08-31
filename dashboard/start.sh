#!/bin/bash

echo "🚀 Starting FOSS Data Platform Dashboard..."

# Check if running in container or host
if [ -f /.dockerenv ]; then
    echo "Running in Docker container..."
    export FLASK_ENV=development
    export FLASK_APP=app.py
    python app.py
else
    echo "Running on host system..."
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install dependencies
    echo "Installing dependencies..."
    pip install -r requirements.txt
    
    # Set environment variables
    export FLASK_ENV=development
    export FLASK_APP=app.py
    export FLASK_DEBUG=1
    
    # Start the application
    echo "Starting dashboard on http://localhost:5000"
    python app.py
fi
