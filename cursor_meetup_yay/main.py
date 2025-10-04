#!/usr/bin/env python3
"""
Concert MCP Server Flask Application
Web interface for the MCP server that scrapes Reddit for concert information
"""

import os
import json
import asyncio
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import praw
import re
from datetime import datetime

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
        """Initialize Reddit API client with OAuth"""
        try:
            self.reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="ConcertMCPBot/1.0 by ConcertInfoBot",
                username=os.getenv("REDDIT_USERNAME"),
                password=os.getenv("REDDIT_PASSWORD")
            )
            # Test the connection
            self.reddit.user.me()
            print("✅ Reddit API connected successfully")
        except Exception as e:
            print(f"❌ Reddit authentication failed: {e}")
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
                
                # Search in subreddit
                for submission in subreddit.search(f"{artist} {location or ''}", 
                                                time_filter="month", 
                                                limit=10):
                    if self._is_relevant_post(submission, artist, location):
                        subreddit_results.append(self._extract_concert_info(submission))
                
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
        
        # Look for concert-related keywords
        concert_keywords = [
            "concert", "show", "tour", "festival", "setlist", "live", 
            "venue", "tickets", "date", "time", "schedule", "lineup"
        ]
        
        return any(keyword in text for keyword in concert_keywords)
    
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
    try:
        data = request.get_json()
        artist = data.get('artist', '').strip()
        location = data.get('location', '').strip() or None
        date_range = data.get('date_range', '30')
        
        if not artist:
            return jsonify({'error': 'Artist name is required'}), 400
        
        # Search for concerts
        results = reddit_scraper.search_concerts(artist, location, date_range)
        
        if 'error' in results:
            return jsonify({'error': results['error']}), 500
        
        return jsonify({
            'success': True,
            'artist': artist,
            'location': location,
            'results': results,
            'total_subreddits': len(results),
            'total_posts': sum(len(posts) for posts in results.values())
        })
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@app.route('/api/setlist', methods=['POST'])
def get_setlist():
    """API endpoint to get setlist information"""
    try:
        data = request.get_json()
        artist = data.get('artist', '').strip()
        venue = data.get('venue', '').strip() or None
        
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
        festival = data.get('festival', '').strip() or None
        location = data.get('location', '').strip() or None
        
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
    
    app.run(debug=True, host='0.0.0.0', port=5000)
