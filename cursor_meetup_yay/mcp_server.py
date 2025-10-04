#!/usr/bin/env python3
"""
Concert Information MCP Server - Reddit Scraper
Scrapes Reddit for concert information from specific subreddits
"""

import asyncio
import json
import os
import re
import logging
from datetime import datetime, timedelta
from typing import Any, Sequence, Dict, List, Optional
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import praw
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('mcp_server.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Concert-related subreddits to search
CONCERT_SUBREDDITS = [
    "concert",
    "edm", 
    "livemusic",
    "UMF",
    "setlist",
    "festivals",
    "electronicmusic",
    "aves",
    "edmprodcirclejerk",
    "electronicdancemusic"
]

class RedditConcertScraper:
    """Reddit scraper for concert information"""
    
    def __init__(self):
        self.reddit = None
        self._initialize_reddit()
    
    def _initialize_reddit(self):
        """Initialize Reddit API client with OAuth2 (client credentials only)"""
        logger.info("Initializing Reddit API connection...")
        
        # Check if credentials are available
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        
        if not client_id or not client_secret:
            logger.error("Reddit credentials not found in environment variables")
            logger.error("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
            print("❌ Reddit credentials not found in environment variables")
            print("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET in .env file")
            self.reddit = None
            return
        
        logger.info(f"Found Reddit credentials - Client ID: {client_id[:8]}...")
        
        try:
            logger.info("Creating Reddit API client...")
            self.reddit = praw.Reddit(
                client_id=client_id,
                client_secret=client_secret,
                user_agent="ConcertMCPBot/1.0 by ConcertInfoBot"
            )
            logger.info("Reddit API client created successfully")
            
            # Test the connection by accessing a public subreddit
            logger.info("Testing Reddit API connection...")
            test_subreddit = self.reddit.subreddit("test")
            subreddit_name = test_subreddit.display_name
            logger.info(f"Successfully accessed subreddit: r/{subreddit_name}")
            
            # Test search functionality
            logger.info("Testing Reddit search functionality...")
            search_results = list(test_subreddit.search("test", limit=1))
            logger.info(f"Search test successful - found {len(search_results)} results")
            
            print("✅ Reddit API connected successfully (OAuth2)")
            logger.info("Reddit API initialization completed successfully")
            
        except Exception as e:
            error_msg = f"Reddit authentication failed: {e}"
            logger.error(error_msg)
            logger.error("Please check your REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
            print(f"❌ {error_msg}")
            print("Please check your REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
            self.reddit = None
    
    def search_concerts(self, artist: str, location: str = None, date_range: str = "30") -> Dict[str, List[Dict]]:
        """Search for concert information across multiple subreddits"""
        logger.info(f"Starting concert search for artist: '{artist}', location: '{location}'")
        
        if not self.reddit:
            error_msg = "Reddit API not initialized. Please check credentials."
            logger.error(error_msg)
            return {"error": error_msg}
        
        results = {}
        search_terms = self._generate_search_terms(artist, location)
        logger.info(f"Generated search terms: {search_terms}")
        
        for subreddit_name in CONCERT_SUBREDDITS:
            logger.info(f"🔍 Searching r/{subreddit_name}...")
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                subreddit_results = []
                
                logger.info(f"📝 Search parameters for r/{subreddit_name}:")
                logger.info(f"   Search terms: {search_terms}")
                logger.info(f"   Time filter: 'all' (no time restriction)")
                logger.info(f"   Limit: 10 per search term")
                logger.info(f"   Artist: '{artist}'")
                logger.info(f"   Location: '{location or 'None'}'")
                
                # Search with multiple terms
                search_count = 0
                seen_posts = set()  # Avoid duplicates
                
                for search_query in search_terms[:3]:  # Try first 3 search terms
                    print(f"\n🚀 EXECUTING REDDIT SEARCH:")
                    print(f"   Subreddit: r/{subreddit_name}")
                    print(f"   Query: '{search_query}'")
                    print(f"   Time filter: all")
                    print(f"   Limit: 10")
                    print("=" * 50)
                    
                    logger.info(f"🚀 Executing Reddit search in r/{subreddit_name} with query: '{search_query}'")
                    logger.info(f"🔗 Reddit API call: subreddit.search('{search_query}', time_filter='all', limit=10)")
                    
                    try:
                        search_generator = subreddit.search(search_query, 
                                                          time_filter="all", 
                                                          limit=10)
                        logger.info(f"📡 Reddit API response generator created for r/{subreddit_name}")
                        
                        for submission in search_generator:
                            # Skip if we've already seen this post
                            if submission.id in seen_posts:
                                continue
                            seen_posts.add(submission.id)
                            
                            search_count += 1
                            print(f"🔍 REDDIT API RESULT #{search_count} in r/{subreddit_name}:")
                            print(f"   Title: {submission.title}")
                            print(f"   URL: https://reddit.com{submission.permalink}")
                            print(f"   Score: {submission.score}, Author: {submission.author}")
                            print(f"   Selftext: {submission.selftext[:100]}...")
                            print()
                            
                            logger.debug(f"📄 Found submission #{search_count} in r/{subreddit_name}: {submission.title[:50]}...")
                            logger.debug(f"   URL: https://reddit.com{submission.permalink}")
                            logger.debug(f"   Score: {submission.score}, Author: {submission.author}")
                            
                            # Add all posts without filtering - let LLM decide relevance
                            concert_info = self._extract_concert_info(submission)
                            subreddit_results.append(concert_info)
                            print(f"✅ ADDED TO RESULTS: {submission.title[:60]}...")
                            logger.debug(f"✅ Added post: {submission.title[:50]}...")
                                
                    except Exception as search_error:
                        logger.warning(f"⚠️ Search failed for query '{search_query}' in r/{subreddit_name}: {search_error}")
                        continue
                
                logger.info(f"📊 r/{subreddit_name} results:")
                logger.info(f"   Total posts found: {search_count}")
                logger.info(f"   Posts added to results: {len(subreddit_results)}")
                logger.info(f"   All posts included (no filtering)")
                
                if subreddit_results:
                    results[subreddit_name] = subreddit_results
                    logger.info(f"✅ Added {len(subreddit_results)} posts from r/{subreddit_name} to results")
                else:
                    logger.info(f"📭 No relevant posts found in r/{subreddit_name}")
                    
            except Exception as e:
                error_msg = f"❌ Error searching r/{subreddit_name}: {e}"
                logger.error(error_msg)
                logger.error(f"   Subreddit: r/{subreddit_name}")
                logger.error(f"   Query: '{search_query}'")
                logger.error(f"   Error type: {type(e).__name__}")
                print(error_msg)
                continue
        
        total_posts = sum(len(posts) for posts in results.values())
        logger.info(f"Concert search completed: {total_posts} posts found across {len(results)} subreddits (all posts included, no filtering)")
        print(f"\n🎉 SEARCH COMPLETE: {total_posts} posts found across {len(results)} subreddits")
        print("📝 All posts passed to LLM without filtering")
        return results
    
    def _generate_search_terms(self, artist: str, location: str = None) -> List[str]:
        """Generate various search term combinations"""
        terms = [artist]
        if location:
            terms.extend([f"{artist} {location}", f"{location} {artist}"])
        
        # Add common concert-related terms
        concert_terms = ["concert", "show", "tour", "festival", "setlist", "live"]
        for term in concert_terms:
            terms.extend([f"{artist} {term}", f"{term} {artist}"])
            if location:
                terms.extend([f"{artist} {term} {location}", f"{location} {artist} {term}"])
        
        return terms
    
    def _is_relevant_post(self, submission, artist: str, location: str = None) -> bool:
        """Check if a post is relevant to the concert search"""
        text = f"{submission.title} {submission.selftext}".lower()
        artist_lower = artist.lower()
        
        # Must contain artist name
        if artist_lower not in text:
            logger.debug(f"❌ Post doesn't contain artist '{artist_lower}': {submission.title[:50]}...")
            return False
        
        # If location specified, should contain location
        if location and location.lower() not in text:
            logger.debug(f"❌ Post doesn't contain location '{location.lower()}': {submission.title[:50]}...")
            return False
        
        # More flexible concert-related keywords (expanded list)
        concert_keywords = [
            "concert", "show", "tour", "festival", "setlist", "live", 
            "venue", "tickets", "date", "time", "schedule", "lineup",
            "performance", "gig", "event", "appearance", "playing", "stage",
            "music", "song", "album", "release", "new", "upcoming", "announced"
        ]
        
        # Check for concert keywords
        has_concert_keywords = any(keyword in text for keyword in concert_keywords)
        
        if has_concert_keywords:
            logger.debug(f"✅ Post contains concert keywords: {submission.title[:50]}...")
            return True
        
        # If no concert keywords, still allow if it's in a concert-related subreddit
        # and contains the artist name (might be discussion, news, etc.)
        concert_subreddits = ["concert", "edm", "livemusic", "UMF", "setlist", "festivals"]
        if submission.subreddit.display_name.lower() in [s.lower() for s in concert_subreddits]:
            logger.debug(f"✅ Post in concert subreddit without keywords: {submission.title[:50]}...")
            return True
        
        logger.debug(f"❌ Post filtered out: {submission.title[:50]}...")
        return False
    
    def _extract_concert_info(self, submission) -> Dict:
        """Extract relevant concert information from a Reddit post"""
        # Extract dates and times using regex
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',  # MM/DD/YYYY or DD/MM/YYYY
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',  # YYYY/MM/DD
            r'(january|february|march|april|may|june|july|august|september|october|november|december)\s+\d{1,2},?\s+\d{4}',
            r'(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})'
        ]
        
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:am|pm|AM|PM)?)',
            r'(\d{1,2}\s*(?:am|pm|AM|PM))',
            r'(doors?\s+(?:at\s+)?\d{1,2}:\d{2})',
            r'(show\s+(?:at\s+)?\d{1,2}:\d{2})'
        ]
        
        text = f"{submission.title} {submission.selftext}"
        
        dates = []
        times = []
        
        for pattern in date_patterns:
            dates.extend(re.findall(pattern, text, re.IGNORECASE))
        
        for pattern in time_patterns:
            times.extend(re.findall(pattern, text, re.IGNORECASE))
        
        return {
            "title": submission.title,
            "url": f"https://reddit.com{submission.permalink}",
            "subreddit": submission.subreddit.display_name,
            "score": submission.score,
            "created_utc": datetime.fromtimestamp(submission.created_utc).isoformat(),
            "text": submission.selftext[:500] + "..." if len(submission.selftext) > 500 else submission.selftext,
            "dates_found": dates,
            "times_found": times,
            "author": str(submission.author) if submission.author else "[deleted]"
        }

# Initialize Reddit scraper
reddit_scraper = RedditConcertScraper()

# Initialize MCP server
app = Server("concert-mcp-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools."""
    return [
        Tool(
            name="search_concerts",
            description="Search Reddit for concert information including set times, venues, and dates",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist": {
                        "type": "string",
                        "description": "Artist or band name to search for (required)",
                    },
                    "location": {
                        "type": "string", 
                        "description": "City, state, or venue location (optional)",
                    },
                    "date_range": {
                        "type": "string",
                        "description": "Number of days to search back (default: 30)",
                        "default": "30"
                    }
                },
                "required": ["artist"],
            },
        ),
        Tool(
            name="get_setlist_info",
            description="Get detailed setlist information for a specific artist from Reddit",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist": {
                        "type": "string",
                        "description": "Artist name to get setlist for",
                    },
                    "venue": {
                        "type": "string",
                        "description": "Specific venue or festival name (optional)",
                    }
                },
                "required": ["artist"],
            },
        ),
        Tool(
            name="search_edm_events",
            description="Search specifically for EDM events, festivals, and electronic music concerts",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist": {
                        "type": "string",
                        "description": "EDM artist or DJ name",
                    },
                    "festival": {
                        "type": "string",
                        "description": "Festival name (e.g., UMF, EDC, Tomorrowland)",
                    },
                    "location": {
                        "type": "string",
                        "description": "City or venue location",
                    }
                },
                "required": ["artist"],
            },
        ),
        Tool(
            name="get_concert_dates",
            description="Extract specific concert dates and times from Reddit posts",
            inputSchema={
                "type": "object",
                "properties": {
                    "artist": {
                        "type": "string",
                        "description": "Artist name",
                    },
                    "location": {
                        "type": "string",
                        "description": "Location to filter by",
                    }
                },
                "required": ["artist"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> Sequence[TextContent]:
    """Handle tool calls."""
    
    if name == "search_concerts":
        artist = arguments.get("artist", "")
        location = arguments.get("location")
        date_range = arguments.get("date_range", "30")
        
        if not artist:
            return [TextContent(type="text", text="Error: Artist name is required")]
        
        # System prompt for concert search
        system_prompt = f"""
        🎵 CONCERT SEARCH SYSTEM PROMPT 🎵
        
        Searching for: {artist}
        Location: {location or "Any"}
        Date Range: Last {date_range} days
        
        TARGET SUBREDDITS: /concert, /edm, /livemusic, /UMF, /setlist, /festivals, /electronicmusic, /aves
        
        SEARCH FOCUS:
        - Concert dates and times
        - Venue information
        - Set times and schedules
        - Ticket availability
        - Festival lineups
        - Live music events
        
        FILTERING CRITERIA:
        - Must contain artist name: {artist}
        - Location match: {location or "Any location"}
        - Concert-related keywords: concert, show, tour, festival, setlist, live, venue, tickets, date, time, schedule, lineup
        """
        
        try:
            results = reddit_scraper.search_concerts(artist, location, date_range)
            
            if "error" in results:
                return [TextContent(type="text", text=f"Error: {results['error']}")]
            
            if not results:
                return [TextContent(type="text", text=f"No concert information found for {artist} in the specified subreddits.")]
            
            # Format results
            response = f"{system_prompt}\n\n🎤 CONCERT SEARCH RESULTS FOR: {artist.upper()}\n"
            response += "=" * 60 + "\n\n"
            
            for subreddit, posts in results.items():
                response += f"📱 r/{subreddit}:\n"
                response += "-" * 30 + "\n"
                
                for i, post in enumerate(posts[:3], 1):  # Limit to top 3 per subreddit
                    response += f"{i}. {post['title']}\n"
                    response += f"   🔗 {post['url']}\n"
                    response += f"   ⭐ Score: {post['score']}\n"
                    response += f"   📅 Posted: {post['created_utc']}\n"
                    
                    if post['dates_found']:
                        response += f"   📅 Dates: {', '.join(post['dates_found'])}\n"
                    
                    if post['times_found']:
                        response += f"   ⏰ Times: {', '.join(post['times_found'])}\n"
                    
                    if post['text']:
                        response += f"   📝 Preview: {post['text'][:200]}...\n"
                    
                    response += "\n"
                
                response += "\n"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error searching concerts: {str(e)}")]

    elif name == "get_setlist_info":
        artist = arguments.get("artist", "")
        venue = arguments.get("venue")
        
        if not artist:
            return [TextContent(type="text", text="Error: Artist name is required")]
        
        # System prompt for setlist search
        system_prompt = f"""
        🎼 SETLIST SEARCH SYSTEM PROMPT 🎼
        
        Searching for setlist information for: {artist}
        Venue: {venue or "Any venue"}
        
        TARGET SUBREDDITS: /setlist, /concert, /edm, /livemusic, /UMF
        
        SEARCH FOCUS:
        - Song lists and setlists
        - Track order and timing
        - Encore information
        - Special performances
        - Set duration and structure
        """
        
        try:
            # Search specifically in setlist-related subreddits
            setlist_subreddits = ["setlist", "concert", "edm", "livemusic", "UMF"]
            results = {}
            
            for subreddit_name in setlist_subreddits:
                try:
                    subreddit = reddit_scraper.reddit.subreddit(subreddit_name)
                    subreddit_results = []
                    
                    search_query = f"{artist} setlist"
                    if venue:
                        search_query += f" {venue}"
                    
                    for submission in subreddit.search(search_query, time_filter="month", limit=5):
                        if "setlist" in submission.title.lower() or "setlist" in submission.selftext.lower():
                            subreddit_results.append(reddit_scraper._extract_concert_info(submission))
                    
                    if subreddit_results:
                        results[subreddit_name] = subreddit_results
                        
                except Exception as e:
                    continue
            
            if not results:
                return [TextContent(type="text", text=f"No setlist information found for {artist}")]
            
            response = f"{system_prompt}\n\n🎼 SETLIST RESULTS FOR: {artist.upper()}\n"
            response += "=" * 50 + "\n\n"
            
            for subreddit, posts in results.items():
                response += f"📱 r/{subreddit}:\n"
                response += "-" * 25 + "\n"
                
                for i, post in enumerate(posts, 1):
                    response += f"{i}. {post['title']}\n"
                    response += f"   🔗 {post['url']}\n"
                    response += f"   ⭐ Score: {post['score']}\n"
                    if post['text']:
                        response += f"   📝 Setlist: {post['text'][:300]}...\n"
                    response += "\n"
                
                response += "\n"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error searching setlists: {str(e)}")]

    elif name == "search_edm_events":
        artist = arguments.get("artist", "")
        festival = arguments.get("festival")
        location = arguments.get("location")
        
        if not artist:
            return [TextContent(type="text", text="Error: Artist name is required")]
        
        # System prompt for EDM search
        system_prompt = f"""
        🎧 EDM EVENT SEARCH SYSTEM PROMPT 🎧
        
        Searching for EDM events for: {artist}
        Festival: {festival or "Any festival"}
        Location: {location or "Any location"}
        
        TARGET SUBREDDITS: /edm, /UMF, /electronicmusic, /aves, /festivals, /edmprodcirclejerk
        
        SEARCH FOCUS:
        - EDM festivals and events
        - DJ sets and performances
        - Electronic music concerts
        - Festival lineups and schedules
        - Club events and raves
        - Set times and stage information
        """
        
        try:
            # Search in EDM-specific subreddits
            edm_subreddits = ["edm", "UMF", "electronicmusic", "aves", "festivals", "edmprodcirclejerk"]
            results = {}
            
            search_query = artist
            if festival:
                search_query += f" {festival}"
            if location:
                search_query += f" {location}"
            
            for subreddit_name in edm_subreddits:
                try:
                    subreddit = reddit_scraper.reddit.subreddit(subreddit_name)
                    subreddit_results = []
                    
                    for submission in subreddit.search(search_query, time_filter="month", limit=5):
                        if reddit_scraper._is_relevant_post(submission, artist, location):
                            subreddit_results.append(reddit_scraper._extract_concert_info(submission))
                    
                    if subreddit_results:
                        results[subreddit_name] = subreddit_results
                        
                except Exception as e:
                    continue
            
            if not results:
                return [TextContent(type="text", text=f"No EDM events found for {artist}")]
            
            response = f"{system_prompt}\n\n🎧 EDM EVENT RESULTS FOR: {artist.upper()}\n"
            response += "=" * 50 + "\n\n"
            
            for subreddit, posts in results.items():
                response += f"📱 r/{subreddit}:\n"
                response += "-" * 25 + "\n"
                
                for i, post in enumerate(posts, 1):
                    response += f"{i}. {post['title']}\n"
                    response += f"   🔗 {post['url']}\n"
                    response += f"   ⭐ Score: {post['score']}\n"
                    if post['dates_found']:
                        response += f"   📅 Dates: {', '.join(post['dates_found'])}\n"
                    if post['times_found']:
                        response += f"   ⏰ Times: {', '.join(post['times_found'])}\n"
                    response += "\n"
                
                response += "\n"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error searching EDM events: {str(e)}")]

    elif name == "get_concert_dates":
        artist = arguments.get("artist", "")
        location = arguments.get("location")
        
        if not artist:
            return [TextContent(type="text", text="Error: Artist name is required")]
        
        try:
            results = reddit_scraper.search_concerts(artist, location)
            
            if "error" in results:
                return [TextContent(type="text", text=f"Error: {results['error']}")]
            
            if not results:
                return [TextContent(type="text", text=f"No concert dates found for {artist}")]
            
            # Extract and format dates
            response = f"📅 CONCERT DATES FOR: {artist.upper()}\n"
            response += "=" * 40 + "\n\n"
            
            all_dates = []
            for subreddit, posts in results.items():
                for post in posts:
                    if post['dates_found']:
                        for date in post['dates_found']:
                            all_dates.append({
                                'date': date,
                                'title': post['title'],
                                'subreddit': subreddit,
                                'url': post['url'],
                                'times': post['times_found']
                            })
            
            if not all_dates:
                return [TextContent(type="text", text=f"No specific dates found for {artist}")]
            
            # Sort by date (basic sorting)
            all_dates.sort(key=lambda x: x['date'])
            
            for i, date_info in enumerate(all_dates[:10], 1):  # Limit to 10 results
                response += f"{i}. {date_info['date']}\n"
                response += f"   📝 {date_info['title']}\n"
                response += f"   📱 r/{date_info['subreddit']}\n"
                response += f"   🔗 {date_info['url']}\n"
                if date_info['times']:
                    response += f"   ⏰ Times: {', '.join(date_info['times'])}\n"
                response += "\n"
            
            return [TextContent(type="text", text=response)]
            
        except Exception as e:
            return [TextContent(type="text", text=f"Error getting concert dates: {str(e)}")]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
