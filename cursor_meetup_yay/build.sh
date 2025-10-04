#!/bin/bash
set -e

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
  echo "Creating .env file..."
  cat > .env << EOF
# Reddit API Credentials (OAuth2)
# Get these from https://www.reddit.com/prefs/apps
# Create a "script" type app and copy the client ID and secret
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here

# OpenAI API Key
# Get this from https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here
EOF
  echo "[WARNING] Please edit .env file with your API credentials"
else
  echo ".env file already exists"
fi

# Remove old venv if it exists
if [ -d "venv" ]; then
  echo "[WARNING] Virtual environment already exists. Removing old one..."
  rm -rf venv
fi

# Create new virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
echo "[SUCCESS] Virtual environment created"

# Activate venv and install requirements
echo "Installing requirements..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "[SUCCESS] Requirements installed"

echo ""
echo "[SUCCESS] Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your Reddit API credentials"
echo "2. Activate virtual environment: source venv/bin/activate"
echo "3. Run the server: python mcp_server.py"
