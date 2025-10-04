# Concert MCP Server - Reddit Scraper

A Model Context Protocol (MCP) server that scrapes Reddit for concert information, set times, and event details from music-related subreddits.

## Features

🎵 **Concert Search** - Search for concert information across multiple subreddits
🎼 **Setlist Information** - Get detailed setlists and track information
🎧 **EDM Events** - Specialized search for electronic music events and festivals
📅 **Date Extraction** - Extract specific concert dates and times from posts

## Target Subreddits

The server searches these music-related subreddits:
- `/concert` - General concert discussions
- `/edm` - Electronic Dance Music
- `/livemusic` - Live music events
- `/UMF` - Ultra Music Festival
- `/setlist` - Concert setlists
- `/festivals` - Music festivals
- `/electronicmusic` - Electronic music
- `/aves` - Electronic music community
- `/edmprodcirclejerk` - EDM production discussions

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up Reddit API credentials:
   - Go to https://www.reddit.com/prefs/apps
   - Create a new app (choose "script" type)
   - Copy your client ID and secret
   - Create a `.env` file with your credentials:
   ```
   REDDIT_CLIENT_ID=your_client_id_here
   REDDIT_CLIENT_SECRET=your_client_secret_here
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   ```

## Usage

### Available Tools

#### 1. `search_concerts`
Search for general concert information including dates, venues, and times.

**Parameters:**
- `artist` (required): Artist or band name
- `location` (optional): City, state, or venue location
- `date_range` (optional): Number of days to search back (default: 30)

#### 2. `get_setlist_info`
Get detailed setlist information for a specific artist.

**Parameters:**
- `artist` (required): Artist name
- `venue` (optional): Specific venue or festival name

#### 3. `search_edm_events`
Search specifically for EDM events, festivals, and electronic music concerts.

**Parameters:**
- `artist` (required): EDM artist or DJ name
- `festival` (optional): Festival name (e.g., UMF, EDC, Tomorrowland)
- `location` (optional): City or venue location

#### 4. `get_concert_dates`
Extract specific concert dates and times from Reddit posts.

**Parameters:**
- `artist` (required): Artist name
- `location` (optional): Location to filter by

## System Prompts

The server includes specialized system prompts for different search types:

- **Concert Search**: Focuses on dates, venues, set times, ticket availability
- **Setlist Search**: Targets song lists, track order, encore information
- **EDM Events**: Emphasizes festivals, DJ sets, electronic music concerts
- **Date Extraction**: Prioritizes specific dates and times

## Running the Server

```bash
python mcp_server.py
```

The server will run using stdio transport and can be integrated with MCP-compatible clients.

## Example Usage

```python
# Search for Taylor Swift concerts in New York
search_concerts(artist="Taylor Swift", location="New York")

# Get setlist for a specific venue
get_setlist_info(artist="Deadmau5", venue="Ultra Music Festival")

# Search for EDM events
search_edm_events(artist="Skrillex", festival="EDC", location="Las Vegas")

# Get concert dates
get_concert_dates(artist="The Weeknd", location="Los Angeles")
```

## Data Extraction

The server automatically extracts:
- Concert dates (multiple formats supported)
- Show times and door times
- Venue information
- Post scores and engagement
- Direct links to Reddit posts
- Text previews and setlist information

## Error Handling

The server includes comprehensive error handling for:
- Reddit API authentication issues
- Network connectivity problems
- Invalid subreddit access
- Missing or malformed data

## Requirements

- Python 3.10+
- Reddit API credentials
- Internet connection for Reddit API access

## License

This project is open source and available under the MIT License.
