#!/usr/bin/env python3
"""
Concert MCP Server Flask Application
Web interface for the MCP server that scrapes Reddit for concert information
"""

import os
import json
import asyncio
import logging
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import praw
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('flask_app.log')
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

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
        logger.info("Initializing Reddit API connection for Flask app...")
        
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
            logger.info("Creating Reddit API client for Flask app...")
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
            logger.info("Reddit API initialization completed successfully for Flask app")
            
        except Exception as e:
            error_msg = f"Reddit authentication failed: {e}"
            logger.error(error_msg)
            logger.error("Please check your REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
            print(f"❌ {error_msg}")
            print("Please check your REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
            self.reddit = None
    
    def search_concerts(self, artist: str, location: str = None, date_range: str = "30"):
        """Search for concert information across multiple subreddits"""
        if not self.reddit:
            return {"error": "Reddit API not initialized. Please check credentials."}
        
        results = {}
        search_terms = self._generate_search_terms(artist, location)
        
        for subreddit_name in CONCERT_SUBREDDITS:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                subreddit_results = []
                seen_posts = set()  # Avoid duplicates
                
                # Search with multiple terms
                for search_query in search_terms[:3]:  # Try first 3 search terms
                    print(f"\n🚀 EXECUTING REDDIT SEARCH:")
                    print(f"   Subreddit: r/{subreddit_name}")
                    print(f"   Query: '{search_query}'")
                    print(f"   Time filter: all")
                    print(f"   Limit: 10")
                    print("=" * 50)
                    
                    try:
                        for submission in subreddit.search(search_query, 
                                                        time_filter="all", 
                                                        limit=10):
                            # Skip if we've already seen this post
                            if submission.id in seen_posts:
                                continue
                            seen_posts.add(submission.id)
                            
                            print(f"🔍 REDDIT API RESULT in r/{subreddit_name}:")
                            print(f"   Title: {submission.title}")
                            print(f"   URL: https://reddit.com{submission.permalink}")
                            print(f"   Score: {submission.score}, Author: {submission.author}")
                            print(f"   Selftext: {submission.selftext[:100]}...")
                            print()
                            
                            # Add all posts without filtering - let LLM decide relevance
                            subreddit_results.append(self._extract_concert_info(submission))
                            print(f"✅ ADDED TO RESULTS: {submission.title[:60]}...")
                                
                    except Exception as search_error:
                        print(f"Search failed for query '{search_query}' in r/{subreddit_name}: {search_error}")
                        continue
                
                if subreddit_results:
                    results[subreddit_name] = subreddit_results
                    
            except Exception as e:
                print(f"Error searching r/{subreddit_name}: {e}")
                continue
        
        return results
    
    def _generate_search_terms(self, artist: str, location: str = None):
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
    
    def _is_relevant_post(self, submission, artist: str, location: str = None):
        """Check if a post is relevant to the concert search"""
        text = f"{submission.title} {submission.selftext}".lower()
        artist_lower = artist.lower()
        
        # Must contain artist name
        if artist_lower not in text:
            return False
        
        # If location specified, should contain location
        if location and location.lower() not in text:
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
            return True
        
        # If no concert keywords, still allow if it's in a concert-related subreddit
        # and contains the artist name (might be discussion, news, etc.)
        concert_subreddits = ["concert", "edm", "livemusic", "UMF", "setlist", "festivals"]
        if submission.subreddit.display_name.lower() in [s.lower() for s in concert_subreddits]:
            return True
        
        return False
    
    def _extract_concert_info(self, submission):
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

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_concerts():
    """API endpoint to search for concerts"""
    logger.info("🎵 Received concert search request")
    logger.info(f"📡 Request method: {request.method}")
    logger.info(f"🌐 Request URL: {request.url}")
    logger.info(f"📋 Request headers: {dict(request.headers)}")
    
    try:
        data = request.get_json()
        logger.info(f"📝 Request JSON data: {data}")
        
        artist = data.get('artist', '').strip()
        location = data.get('location')
        if location:
            location = location.strip() or None
        date_range = data.get('date_range', '30')
        
        logger.info(f"🔍 Parsed search parameters:")
        logger.info(f"   Artist: '{artist}'")
        logger.info(f"   Location: '{location or 'None'}'")
        logger.info(f"   Date range: '{date_range}'")
        
        if not artist:
            logger.warning("❌ Search request missing artist name")
            return jsonify({'error': 'Artist name is required'}), 400
        
        # Search for concerts
        logger.info("🚀 Starting Reddit search...")
        logger.info(f"🎯 Target subreddits: {CONCERT_SUBREDDITS}")
        
        results = reddit_scraper.search_concerts(artist, location, date_range)
        
        if 'error' in results:
            logger.error(f"❌ Reddit search failed: {results['error']}")
            return jsonify({'error': results['error']}), 500
        
        total_posts = sum(len(posts) for posts in results.values())
        logger.info(f"✅ Search completed successfully:")
        logger.info(f"   Total posts found: {total_posts}")
        logger.info(f"   Subreddits with results: {len(results)}")
        logger.info(f"   Results breakdown: {[(sub, len(posts)) for sub, posts in results.items()]}")
        
        response_data = {
            'success': True,
            'artist': artist,
            'location': location,
            'results': results,
            'total_subreddits': len(results),
            'total_posts': total_posts
        }
        
        logger.info(f"📤 Sending response with {total_posts} posts")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"❌ Search API error: {str(e)}")
        logger.error(f"   Error type: {type(e).__name__}")
        logger.error(f"   Request data: {request.get_json()}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/setlist', methods=['POST'])
def get_setlist():
    """API endpoint to get setlist information"""
    try:
        data = request.get_json()
        artist = data.get('artist', '').strip()
        venue = data.get('venue')
        if venue:
            venue = venue.strip() or None
        
        if not artist:
            return jsonify({'error': 'Artist name is required'}), 400
        
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
        
        return jsonify({
            'success': True,
            'artist': artist,
            'venue': venue,
            'results': results,
            'total_subreddits': len(results),
            'total_posts': sum(len(posts) for posts in results.values())
        })
        
    except Exception as e:
        return jsonify({'error': f'Setlist search failed: {str(e)}'}), 500

@app.route('/api/edm', methods=['POST'])
def search_edm():
    """API endpoint to search for EDM events"""
    try:
        data = request.get_json()
        artist = data.get('artist', '').strip()
        festival = data.get('festival')
        if festival:
            festival = festival.strip() or None
        location = data.get('location')
        if location:
            location = location.strip() or None
        
        if not artist:
            return jsonify({'error': 'Artist name is required'}), 400
        
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
        
        return jsonify({
            'success': True,
            'artist': artist,
            'festival': festival,
            'location': location,
            'results': results,
            'total_subreddits': len(results),
            'total_posts': sum(len(posts) for posts in results.values())
        })
        
    except Exception as e:
        return jsonify({'error': f'EDM search failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    reddit_status = "connected" if reddit_scraper.reddit else "disconnected"
    return jsonify({
        'status': 'healthy',
        'reddit_api': reddit_status,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("🎵 Concert MCP Server Flask Application")
    print("======================================")
    print("")
    print("Starting Flask server...")
    print("Reddit API Status:", "✅ Connected" if reddit_scraper.reddit else "❌ Disconnected")
    print("")
    print("Server will be available at:")
    print("  http://localhost:5000")
    print("")
    print("Press Ctrl+C to stop the server")
    print("")
    
    logger.info("Starting Flask application")
    logger.info(f"Reddit API Status: {'Connected' if reddit_scraper.reddit else 'Disconnected'}")
    logger.info("Flask server starting on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
