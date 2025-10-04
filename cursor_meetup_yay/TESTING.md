# MCP Concert Server Testing Guide

This guide explains how to test the Concert MCP Server using the LLM-powered testing system.

## 🧪 Testing System Overview

The testing system uses OpenAI's GPT-4 to understand natural language queries and automatically test the MCP server's functionality. It can:

- **Analyze queries** using LLM to determine which MCP tools to call
- **Extract parameters** from natural language input
- **Execute MCP tools** via the Flask API
- **Validate responses** and provide detailed feedback

## 🚀 Quick Start

### 1. Setup
```bash
# Build the project
./build.sh

# Configure API keys in .env file
nano .env
```

### 2. Start the Server
```bash
# Start the Flask MCP server
./start_app.sh
```

### 3. Run Tests
```bash
# Interactive testing
./test.sh

# Run predefined test cases
./test.sh test-cases

# Test custom query
./test.sh custom "Find Taylor Swift concerts in New York"
```

## 📋 Required API Keys

### Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Create a new app (choose "script" type)
3. Copy client ID and secret

### OpenAI API
1. Go to https://platform.openai.com/api-keys
2. Create a new API key
3. Copy the key

### .env Configuration
```env
# Reddit API Credentials
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USERNAME=your_reddit_username
REDDIT_PASSWORD=your_reddit_password

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key
```

## 🔧 Testing Modes

### 1. Interactive Mode
```bash
./test.sh
```
- Prompts for user input
- Analyzes query with LLM
- Executes appropriate MCP tools
- Shows detailed results

### 2. Test Cases Mode
```bash
./test.sh test-cases
```
- Runs 8 predefined test cases
- Tests different query types
- Provides pass/fail summary
- Examples:
  - "Find concerts for Taylor Swift in New York"
  - "Get the setlist for Deadmau5 at Ultra Music Festival"
  - "Search for EDM events by Skrillex"

### 3. Custom Query Mode
```bash
./test.sh custom "your query here"
```
- Tests a specific query
- Useful for debugging
- Shows detailed execution flow

## 🎯 MCP Tools Tested

The testing system validates these MCP tools:

### 1. `search_concerts(artist, location, date_range)`
- **Purpose**: General concert search
- **Example**: "Find concerts for Taylor Swift in New York"
- **Parameters**: artist, location (optional), date_range (optional)

### 2. `get_setlist_info(artist, venue)`
- **Purpose**: Setlist information
- **Example**: "Get the setlist for Deadmau5 at Ultra Music Festival"
- **Parameters**: artist, venue (optional)

### 3. `search_edm_events(artist, festival, location)`
- **Purpose**: EDM events and festivals
- **Example**: "Search for EDM events by Skrillex"
- **Parameters**: artist, festival (optional), location (optional)

### 4. `get_concert_dates(artist, location)`
- **Purpose**: Extract specific dates and times
- **Example**: "What are the concert dates for The Weeknd?"
- **Parameters**: artist, location (optional)

## 📊 Test Output

### Successful Test
```
🎵 Testing MCP Server
📝 User Query: 'Find concerts for Taylor Swift in New York'
==================================================

🤖 Step 1: Analyzing query with LLM...
✅ LLM Analysis:
   Tools to call: ['search_concerts']
   Expected response: concert information
   Confidence: 0.95

🔧 Step 2: Executing MCP tools...

--- Testing search_concerts ---
🔧 Testing MCP tool: search_concerts
📝 Parameters: {'artist': 'Taylor Swift', 'location': 'New York'}
✅ Tool executed successfully
📊 Results: 5 posts found across 3 subreddits

📊 Step 3: Test Summary
==============================
✅ Successful tests: 1/1
✅ search_concerts: {'artist': 'Taylor Swift', 'location': 'New York'}

🎉 MCP Server test completed successfully!
```

### Failed Test
```
❌ Tool execution failed: 500
Error: Reddit API connection failed
❌ search_concerts: {'artist': 'Taylor Swift', 'location': 'New York'}

❌ MCP Server test failed!
```

## 🐛 Troubleshooting

### Common Issues

#### 1. "MCP server is not running"
```bash
# Start the server first
./start_app.sh
```

#### 2. "OPENAI_API_KEY not configured"
```bash
# Add OpenAI API key to .env
echo "OPENAI_API_KEY=your_key_here" >> .env
```

#### 3. "Reddit API connection failed"
- Check Reddit credentials in .env
- Verify Reddit app is configured as "script" type
- Ensure Reddit account has 2FA disabled (if using password auth)

#### 4. "No results found"
- This is normal for some queries
- Reddit search depends on recent posts
- Try different artists or locations

### Debug Mode
```bash
# Run with verbose output
python3 test_mcp.py "your query here"
```

## 📈 Test Coverage

The testing system covers:

- ✅ **Query Analysis**: LLM understanding of natural language
- ✅ **Parameter Extraction**: Automatic parameter mapping
- ✅ **Tool Execution**: API calls to Flask endpoints
- ✅ **Response Validation**: Success/failure detection
- ✅ **Error Handling**: Network and API errors
- ✅ **Multiple Tools**: All 4 MCP tools tested
- ✅ **Edge Cases**: Empty results, invalid parameters

## 🔄 Continuous Testing

### Automated Test Suite
```bash
# Run all tests
./test.sh test-cases

# Check exit code
echo $?  # 0 = success, 1 = failure
```

### Integration with CI/CD
```bash
#!/bin/bash
# Example CI script
./build.sh
./start_app.sh &
sleep 10
./test.sh test-cases
```

## 📝 Adding New Test Cases

Edit `test.sh` and add to the `test_cases` array:

```bash
test_cases=(
    "Find concerts for Taylor Swift in New York"
    "Get the setlist for Deadmau5 at Ultra Music Festival"
    "Your new test case here"
)
```

## 🎉 Success Criteria

A test passes when:
- ✅ LLM successfully analyzes the query
- ✅ Correct MCP tool is identified
- ✅ Parameters are extracted accurately
- ✅ Flask API responds successfully
- ✅ Results are returned (even if empty)

The testing system ensures the MCP server works correctly with natural language input and provides reliable concert information from Reddit!
