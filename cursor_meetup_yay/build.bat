@echo off
REM Concert MCP Server Build Script for Windows
REM Simplified version - only handles essential setup

setlocal enabledelayedexpansion

REM Status messages
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"

:print_success
echo %SUCCESS% %~1
goto :eof

:print_warning
echo %WARNING% %~1
goto :eof

REM Function to create .env file
:create_env
if not exist ".env" (
    echo Creating .env file...
    (
        echo # Reddit API Credentials
        echo # Get these from https://www.reddit.com/prefs/apps
        echo REDDIT_CLIENT_ID=your_client_id_here
        echo REDDIT_CLIENT_SECRET=your_client_secret_here
        echo REDDIT_USERNAME=your_reddit_username
        echo REDDIT_PASSWORD=your_reddit_password
    ) > .env
    call :print_warning "Please edit .env file with your Reddit API credentials"
) else (
    echo .env file already exists
)
goto :eof

REM Function to create virtual environment
:create_venv
if exist "venv" (
    call :print_warning "Virtual environment already exists. Removing old one..."
    rmdir /s /q venv
)

echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    exit /b 1
)
call :print_success "Virtual environment created"
goto :eof

REM Function to install requirements
:install_requirements
echo Installing requirements...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install requirements
    exit /b 1
)
call :print_success "Requirements installed"
goto :eof

REM Main setup function
:setup
echo Setting up Concert MCP Server...
echo.

call :create_env
call :create_venv
call :install_requirements

echo.
call :print_success "Setup completed!"
echo.
echo Next steps:
echo 1. Edit .env file with your Reddit API credentials
echo 2. Activate virtual environment: venv\Scripts\activate
echo 3. Run the server: python mcp_server.py
goto :eof

REM Show help
:show_help
echo Concert MCP Server Build Script for Windows
echo.
echo Usage: %~nx0 [COMMAND]
echo.
echo Commands:
echo   setup     - Set up the project (create .env, venv, install requirements)
echo   help      - Show this help message
echo.
echo Example:
echo   %~nx0 setup    # First time setup
goto :eof

REM Main script logic
if "%1"=="" goto :show_help
if "%1"=="help" goto :show_help
if "%1"=="setup" goto :setup

:show_help
goto :eof
