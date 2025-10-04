#!/bin/bash

# Concert MCP Server Startup Script
# Starts the Flask web application

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if virtual environment exists
check_venv() {
    if [ ! -d "venv" ]; then
        print_error "Virtual environment not found!"
        print_status "Please run ./build.sh first to set up the project"
        exit 1
    fi
}

# Function to check if .env file exists and is configured
check_env() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_status "Please run ./build.sh first to create the .env file"
        exit 1
    fi
    
    # Check if .env has been configured (not just template values)
    if grep -q "your_client_id_here" .env; then
        print_warning ".env file contains template values"
        print_status "Please edit .env file with your Reddit API credentials before starting"
        print_status "Run: nano .env (or your preferred editor)"
        exit 1
    fi
}

# Function to start the Flask application
start_flask_app() {
    print_status "Starting Concert MCP Server Flask Application..."
    print_status "Server will be available at: http://localhost:5000"
    print_status "Press Ctrl+C to stop the server"
    echo ""
    
    source venv/bin/activate
    python3 main.py
}

# Main execution
main() {
    echo "🎵 Concert MCP Server Startup"
    echo "=============================="
    echo ""
    
    # Check prerequisites
    check_venv
    check_env
    
    # Start the Flask app
    start_flask_app
}

# Show help
show_help() {
    echo "Concert MCP Server Startup Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --help         Show this help message"
    echo ""
    echo "Example:"
    echo "  $0              # Start Flask web application"
}

# Handle command line arguments
case "${1:-}" in
    "--help"|"-h")
        show_help
        ;;
    *)
        main "$@"
        ;;
esac