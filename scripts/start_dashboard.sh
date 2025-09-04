#!/bin/bash

# FOSS Data Platform Dashboard Startup Script
# Ensures port 5000 is available and starts the dashboard

set -e

echo "🚀 Starting FOSS Data Platform Dashboard..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to check for existing dashboard processes
check_existing_processes() {
    print_status "Checking for existing dashboard processes..."

    # Find all Python processes related to our dashboard
    local dashboard_processes=$(pgrep -f "python.*app\.py" 2>/dev/null || true)
    local flask_processes=$(pgrep -f "flask.*run" 2>/dev/null || true)

    if [ -n "$dashboard_processes" ] || [ -n "$flask_processes" ]; then
        print_warning "Found existing dashboard processes:"

        if [ -n "$dashboard_processes" ]; then
            echo "  Python processes: $dashboard_processes"
            for pid in $dashboard_processes; do
                ps -p $pid -o pid,ppid,cmd 2>/dev/null || echo "  Process $pid (details unavailable)"
            done
        fi

        if [ -n "$flask_processes" ]; then
            echo "  Flask processes: $flask_processes"
            for pid in $flask_processes; do
                ps -p $pid -o pid,ppid,cmd 2>/dev/null || echo "  Process $pid (details unavailable)"
            done
        fi

        return 0  # Found existing processes
    else
        print_status "No existing dashboard processes found"
        return 1  # No existing processes
    fi
}

# Function to test if dashboard is responding
test_dashboard_health() {
    local port=$1
    local max_attempts=3

    for attempt in $(seq 1 $max_attempts); do
        print_status "Testing dashboard health (attempt $attempt/$max_attempts)..."

        # Try to connect to the dashboard
        if curl -s --max-time 5 "http://localhost:$port/" >/dev/null 2>&1; then
            print_success "Dashboard is responding on port $port"
            return 0  # Healthy
        else
            print_warning "Dashboard not responding on port $port (attempt $attempt)"
            if [ $attempt -lt $max_attempts ]; then
                sleep 2
            fi
        fi
    done

    print_error "Dashboard is not responding after $max_attempts attempts"
    return 1  # Unhealthy
}

# Function to gracefully shutdown existing processes
shutdown_existing_processes() {
    print_status "Shutting down existing dashboard processes..."

    # Try graceful shutdown first (SIGTERM)
    pkill -TERM -f "python.*app.py" 2>/dev/null || true
    pkill -TERM -f "flask.*run" 2>/dev/null || true

    # Wait for graceful shutdown
    local grace_period=5
    for i in $(seq 1 $grace_period); do
        if ! pgrep -f "python.*app.py" >/dev/null 2>&1 && ! pgrep -f "flask.*run" >/dev/null 2>&1; then
            print_success "Processes shut down gracefully"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo ""

    # Force kill if graceful shutdown failed
    print_warning "Graceful shutdown failed, force killing processes..."
    pkill -KILL -f "python.*app.py" 2>/dev/null || true
    pkill -KILL -f "flask.*run" 2>/dev/null || true

    # Wait a moment for processes to terminate
    sleep 2

    # Verify all processes are gone
    if pgrep -f "python.*app.py" >/dev/null 2>&1 || pgrep -f "flask.*run" >/dev/null 2>&1; then
        print_error "Could not kill all existing processes"
        return 1
    else
        print_success "All processes successfully terminated"
        return 0
    fi
}

# Function to kill process using port
kill_port_process() {
    local port=$1
    print_warning "Port $port is in use. Attempting to free it..."

    # First, try our intelligent shutdown
    if ! shutdown_existing_processes; then
        print_warning "Intelligent shutdown failed, trying alternative methods..."

        # Handle stale sockets - force close TCP connections
        print_status "Checking for stale sockets on port $port..."
        if command -v ss >/dev/null 2>&1; then
            # Check if port is in TIME_WAIT or CLOSE_WAIT state
            if ss -tulpn | grep ":$port " | grep -q "LISTEN"; then
                print_warning "Port $port shows as LISTEN but no PID - likely stale socket"
                # Try to force close the socket
                timeout 5 bash -c "echo > /dev/tcp/localhost/$port" 2>/dev/null || true
                sleep 2
            fi
        fi

        # Fallback to port-specific killing
        if command -v fuser >/dev/null 2>&1; then
            fuser -k $port/tcp >/dev/null 2>&1 || true
        fi

        if command -v lsof >/dev/null 2>&1; then
            lsof -ti:$port | xargs kill -9 >/dev/null 2>&1 || true
        fi

        # Wait for processes and sockets to terminate
        sleep 5
    fi

    # Check if port is now free
    if check_port $port; then
        print_error "Could not free port $port. Please manually kill the process and try again."
        print_status "Manual cleanup commands:"
        print_status "  sudo lsof -ti:$port | xargs kill -9"
        print_status "  sudo fuser -k $port/tcp"
        print_status "  sudo ss -K dst :$port"
        return 1
    else
        print_success "Successfully freed port $port"
        return 0
    fi
}

# Function to activate virtual environment
activate_venv() {
    # Check if we're already in a virtual environment
    if [ -n "$VIRTUAL_ENV" ]; then
        print_success "Already in virtual environment: $VIRTUAL_ENV"
        return
    fi

    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f "../.venv/bin/activate" ]; then
        source ../.venv/bin/activate
        print_success "Virtual environment activated (from parent directory)"
    else
        print_error "Virtual environment not found. Please run: python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi
}

# Main startup process
main() {
    local port=5000

    print_status "=== FOSS Data Platform Dashboard Startup ==="
    print_status "Target port: $port"

    # Step 1: Check for existing processes
    if check_existing_processes; then
        print_status "Found existing dashboard processes"

        # Test if existing dashboard is healthy
        if test_dashboard_health $port && [ "$FORCE_RESTART" = false ]; then
            print_success "✅ Existing dashboard is healthy and responding!"
            print_status "📍 Dashboard is available at: http://localhost:$port"
            print_status "💡 No need to start a new instance"
            print_status "💡 Run './scripts/start_dashboard.sh --restart' to force restart"
            exit 0
        else
            if [ "$FORCE_RESTART" = true ]; then
                print_status "🔄 Force restart requested, shutting down existing processes..."
            else
                print_warning "Existing dashboard is not responding, will restart..."
            fi

            if ! shutdown_existing_processes; then
                print_error "Failed to shutdown existing processes. Please kill them manually."
                exit 1
            fi
        fi
    else
        print_status "No existing dashboard processes found"
    fi

    # Step 2: Check port availability (double check)
    if check_port $port; then
        print_warning "Port $port still in use after process cleanup"
        if ! kill_port_process $port; then
            print_error "Failed to free port $port. Exiting."
            exit 1
        fi
    else
        print_success "Port $port is available"
    fi

    # Step 3: Prepare environment
    if [ -d "dashboard" ]; then
        cd dashboard
        print_status "Changed to dashboard directory"
    else
        print_error "Dashboard directory not found"
        exit 1
    fi

    # Activate virtual environment
    activate_venv

    # Set environment variables
    export FLASK_ENV=production
    export FLASK_DEBUG=false

    # Step 4: Start Flask application
    print_status "🚀 Starting Flask application on port $port..."
    print_status "📍 Dashboard will be available at: http://localhost:$port"
    print_status "🛑 Press Ctrl+C to stop the server"
    echo ""

    # Start Flask with error handling
    if python app.py; then
        print_success "✅ Flask application started successfully"
        print_status "🎉 Dashboard is running at: http://localhost:$port"
    else
        print_error "❌ Failed to start Flask application"
        exit 1
    fi
}

# Handle script interruption
trap 'echo -e "\n${BLUE}[INFO]${NC} Shutting down gracefully..."; exit 0' INT TERM

# Function to handle command line arguments
parse_args() {
    FORCE_RESTART=false

    while [[ $# -gt 0 ]]; do
        case $1 in
            --restart|-r)
                FORCE_RESTART=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  --restart, -r    Force restart even if dashboard is healthy"
                echo "  --help, -h       Show this help message"
                echo ""
                echo "Examples:"
                echo "  $0               Start dashboard (skip if healthy)"
                echo "  $0 --restart     Force restart dashboard"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

# Run main function with argument parsing
parse_args "$@"
main
