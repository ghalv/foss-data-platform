#!/bin/bash

# FOSS Data Platform Dashboard Monitor
# Checks dashboard health and restarts if needed

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[MONITOR]${NC} $1"
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

# Function to check if dashboard is running
check_dashboard_running() {
    local dashboard_processes=$(pgrep -f "python.*app.py" 2>/dev/null || true)
    if [ -n "$dashboard_processes" ]; then
        return 0  # Running
    else
        return 1  # Not running
    fi
}

# Function to test dashboard health
test_dashboard_health() {
    local port=5000
    local max_attempts=2

    for attempt in $(seq 1 $max_attempts); do
        if curl -s --max-time 3 "http://localhost:$port/" >/dev/null 2>&1; then
            return 0  # Healthy
        fi
        sleep 1
    done

    return 1  # Unhealthy
}

# Function to restart dashboard
restart_dashboard() {
    print_warning "Restarting dashboard..."

    # Kill existing processes
    pkill -TERM -f "python.*app.py" 2>/dev/null || true
    pkill -TERM -f "flask.*run" 2>/dev/null || true

    sleep 2

    # Start dashboard
    if [ -f "./scripts/start_dashboard.sh" ]; then
        ./scripts/start_dashboard.sh &
        local new_pid=$!
        print_success "Dashboard restart initiated (PID: $new_pid)"

        # Wait a moment and check if it's running
        sleep 5
        if test_dashboard_health; then
            print_success "Dashboard successfully restarted"
            return 0
        else
            print_error "Dashboard failed to start properly"
            return 1
        fi
    else
        print_error "scripts/start_dashboard.sh not found"
        return 1
    fi
}

# Function to send notification (placeholder)
send_notification() {
    local message="$1"
    local level="$2"

    # For now, just log to console
    # In production, you could integrate with:
    # - Email notifications
    # - Slack/Discord webhooks
    # - System monitoring tools

    echo "$(date): [$level] $message" >> /tmp/dashboard_monitor.log
}

# Main monitoring function
main() {
    local port=5000

    print_status "=== Dashboard Health Check ==="
    print_status "Time: $(date)"
    print_status "Target: http://localhost:$port"

    # Check if dashboard is running
    if check_dashboard_running; then
        print_status "Dashboard process is running"

        # Test health
        if test_dashboard_health; then
            print_success "✅ Dashboard is healthy and responding"
            return 0
        else
            print_error "❌ Dashboard process exists but is not responding"
            send_notification "Dashboard is not responding" "ERROR"

            if restart_dashboard; then
                send_notification "Dashboard automatically restarted" "INFO"
                return 0
            else
                print_error "Failed to restart dashboard"
                return 1
            fi
        fi
    else
        print_warning "Dashboard process is not running"
        send_notification "Dashboard process not found" "WARNING"

        if restart_dashboard; then
            send_notification "Dashboard started" "INFO"
            return 0
        else
            print_error "Failed to start dashboard"
            return 1
        fi
    fi
}

# Run main function
main "$@"
