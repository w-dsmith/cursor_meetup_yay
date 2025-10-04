#!/usr/bin/env python3
"""
Debug script to test the search functionality
"""

import os
import praw
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_search_without_filtering():
    """Test search without relevance filtering"""
    print("🔍 Testing Reddit Search Without Filtering")
    print("=" * 50)
    
    # Check credentials
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("❌ Reddit credentials not found")
        return False
    
    print(f"✅ Found credentials - Client ID: {client_id[:8]}...")
    
    try:
        # Initialize Reddit client
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="ConcertMCPBot/1.0 by ConcertInfoBot"
        )
        print("✅ Reddit client initialized")
        
        # Test search in concert subreddit
        print("\n🎵 Testing r/concert search...")
        concert_subreddit = reddit.subreddit("concert")
        search_query = "Taylor Swift"
        
        print(f"🔍 Searching for: '{search_query}'")
        search_results = list(concert_subreddit.search(search_query, limit=5))
        print(f"📊 Found {len(search_results)} total posts")
        
        if search_results:
            print("\n📝 All posts found:")
            for i, post in enumerate(search_results, 1):
                print(f"   {i}. {post.title[:80]}...")
                print(f"      Score: {post.score}, Author: {post.author}")
                print(f"      URL: https://reddit.com{post.permalink}")
                
                # Test the old filtering logic
                text = f"{post.title} {post.selftext}".lower()
                artist_lower = "taylor swift"
                
                has_artist = artist_lower in text
                print(f"      Contains artist: {has_artist}")
                
                if has_artist:
                    concert_keywords = [
                        "concert", "show", "tour", "festival", "setlist", "live", 
                        "venue", "tickets", "date", "time", "schedule", "lineup"
                    ]
                    has_concert_keywords = any(keyword in text for keyword in concert_keywords)
                    print(f"      Contains concert keywords: {has_concert_keywords}")
                    print(f"      Would be filtered: {not has_concert_keywords}")
                print()
        else:
            print("   ⚠️ No results found")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_search_without_filtering()
