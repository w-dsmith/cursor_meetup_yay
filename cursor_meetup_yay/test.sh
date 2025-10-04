#!/bin/bash

# MCP Testing Script
# Runs the MCP tester with various concert queries

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

# Function to check if .env file exists and has OpenAI key
check_env() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        print_status "Please run ./build.sh first to create the .env file"
        exit 1
    fi
    
    # Check if OpenAI API key is configured
    if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=your_openai_api_key_here" .env; then
        print_warning "OPENAI_API_KEY not configured in .env file"
        print_status "Please add your OpenAI API key to the .env file:"
        print_status "OPENAI_API_KEY=your_actual_api_key_here"
        exit 1
    fi
}

# Function to check if MCP server is running
check_server() {
    print_status "Checking if MCP server is running..."
    
    if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
        print_success "MCP server is running"
        return 0
    else
        print_error "MCP server is not running!"
        print_status "Please start the server first:"
        print_status "1. Run: ./start_app.sh"
        print_status "2. Wait for server to start"
        print_status "3. Then run this test script"
        exit 1
    fi
}

# Function to run interactive test
run_interactive_test() {
    print_status "Starting interactive MCP test..."
    echo ""
    
    source venv/bin/activate
    python3 test_mcp.py
}

# Function to run predefined test cases
run_test_cases() {
    print_status "Running predefined test cases..."
    echo ""
    
    source venv/bin/activate
    
    # Test cases
    test_cases=(
        "Find concerts for Taylor Swift in New York"
        "Get the setlist for Deadmau5 at Ultra Music Festival"
        "Search for EDM events by Skrillex"
        "What are the concert dates for The Weeknd in Los Angeles?"
        "Find live music events for Billie Eilish"
        "Get setlist information for Martin Garrix"
        "Search for electronic music festivals with Calvin Harris"
        "Find concert dates and times for Drake"
    )
    
    passed=0
    total=${#test_cases[@]}
    
    for i in "${!test_cases[@]}"; do
        test_case="${test_cases[$i]}"
        echo ""
        print_status "Test Case $((i+1))/$total: $test_case"
        echo "----------------------------------------"
        
        if python3 test_mcp.py "$test_case"; then
            print_success "Test case $((i+1)) passed"
            ((passed++))
        else
            print_error "Test case $((i+1)) failed"
        fi
        
        # Small delay between tests
        sleep 2
    done
    
    echo ""
    print_status "Test Suite Summary"
    echo "===================="
    print_success "Passed: $passed/$total test cases"
    
    if [ $passed -eq $total ]; then
        print_success "All tests passed! 🎉"
        return 0
    else
        print_error "Some tests failed! ❌"
        return 1
    fi
}

# Function to run custom query
run_custom_query() {
    if [ -z "$1" ]; then
        print_error "No query provided"
        print_status "Usage: $0 custom \"your query here\""
        exit 1
    fi
    
    print_status "Running custom query test..."
    echo ""
    
    source venv/bin/activate
    python3 test_mcp.py "$1"
}

# Function to show help
show_help() {
    echo "MCP Concert Server Testing Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  interactive    Run interactive test (default)"
    echo "  test-cases     Run predefined test cases"
    echo "  custom QUERY   Run custom query test"
    echo "  help           Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Interactive mode"
    echo "  $0 test-cases               # Run all test cases"
    echo "  $0 custom \"Find Taylor Swift concerts\"  # Custom query"
    echo ""
    echo "Prerequisites:"
    echo "  1. MCP server must be running (./start_app.sh)"
    echo "  2. OpenAI API key must be configured in .env"
    echo "  3. Reddit API credentials must be configured in .env"
}

# Main execution
main() {
    echo "🎵 MCP Concert Server Tester"
    echo "============================"
    echo ""
    
    # Check prerequisites
    check_venv
    check_env
    check_server
    
    # Handle command line arguments
    case "${1:-interactive}" in
        "interactive")
            run_interactive_test
            ;;
        "test-cases")
            run_test_cases
            ;;
        "custom")
            run_custom_query "$2"
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
