#!/usr/bin/env python3
"""
Debug script to test RSS feed parsing.
"""
import feedparser
import requests
import urllib3
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_rss_feed(url):
    """Test parsing a single RSS feed."""
    print(f"\n=== Testing RSS feed: {url} ===")

    try:
        # Use requests with SSL verification disabled for better compatibility
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        try:
            response = requests.get(url, headers=headers, verify=False, timeout=30)
            response.raise_for_status()
            feed = feedparser.parse(response.content)
        except Exception as req_error:
            print(f"Requests failed, trying feedparser directly: {req_error}")
            feed = feedparser.parse(url)
        
        print(f"Feed title: {getattr(feed.feed, 'title', 'No title')}")
        print(f"Feed description: {getattr(feed.feed, 'description', 'No description')}")
        print(f"Bozo: {feed.bozo}")
        print(f"Number of entries: {len(feed.entries)}")
        
        if feed.bozo:
            print(f"Bozo exception: {feed.bozo_exception}")
        
        # Test first few entries
        for i, entry in enumerate(feed.entries[:3]):
            print(f"\n--- Entry {i+1} ---")
            print(f"Title: {getattr(entry, 'title', 'No title')}")
            print(f"Link: {getattr(entry, 'link', 'No link')}")
            print(f"Summary: {getattr(entry, 'summary', 'No summary')[:100]}...")
            
            # Check publication date
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6])
                print(f"Published (parsed): {published}")
            elif hasattr(entry, 'published'):
                print(f"Published (raw): {entry.published}")
            else:
                print("No publication date")
            
            # Check content
            if hasattr(entry, 'content') and entry.content:
                content = entry.content[0].value if isinstance(entry.content, list) else entry.content
                print(f"Content: {content[:100]}...")
            elif hasattr(entry, 'description'):
                print(f"Description: {entry.description[:100]}...")
            else:
                print("No content/description")
                
    except Exception as e:
        print(f"Error parsing feed: {e}")

if __name__ == "__main__":
    # Test RSS feeds from updated config
    test_feeds = [
        "https://feeds.bbci.co.uk/news/rss.xml",
        "https://www.npr.org/rss/rss.php?id=1001",
        "https://www.theguardian.com/world/rss",
        "https://www.billboard.com/feed/",
        "https://www.theverge.com/rss/index.xml",
    ]
    
    for feed_url in test_feeds:
        test_rss_feed(feed_url)
