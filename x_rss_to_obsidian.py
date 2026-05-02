#!/usr/bin/env python3
"""
x_rss_to_obsidian.py
Poll RSS feeds from X/Twitter via Nitter and save to Obsidian Markdown.

Nitter RSS feeds are free and work without authentication.
Multiple Nitter instances available (some may be blocked, script auto-rotates).

Usage:
    # Scrape latest posts from RSS
    python3 x_rss_to_obsidian.py --user BoboLucyWisdom
    
    # Run as daemon/cron for monitoring
    python3 x_rss_to_obsidian.py --user BoboLucyWisdom --daemon
"""

import argparse
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set
from urllib.parse import urljoin, urlparse

# Try to import feedparser
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Config
OBSIDIAN_VAULT = Path.home() / "brain" / "x-posts"
STATE_FILE = Path.home() / ".config" / "x_to_obsidian" / "rss_state.json"
LOG_FILE = Path.home() / ".config" / "x_to_obsidian" / "rss_scraper.log"

# Nitter instances (rotated if one fails)
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.it",
    "https://nitter.cz",
    "https://nitter.privacydev.net",
    "https://nitter.unixfox.eu",
]


def ensure_dependencies():
    """Ensure required packages are installed."""
    global FEEDPARSER_AVAILABLE, REQUESTS_AVAILABLE
    
    to_install = []
    if not FEEDPARSER_AVAILABLE:
        to_install.append("feedparser")
    if not REQUESTS_AVAILABLE:
        to_install.extend(["requests", "beautifulsoup4"])
    
    if to_install:
        print(f"Installing dependencies: {', '.join(to_install)}...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install"] + to_install + ["-q"])
        
        # Re-import
        import importlib
        global feedparser, requests, BeautifulSoup
        if "feedparser" in to_install:
            feedparser = importlib.import_module("feedparser")
        if "requests" in to_install:
            requests = importlib.import_module("requests")
            BeautifulSoup = importlib.import_module("bs4").BeautifulSoup
        
        FEEDPARSER_AVAILABLE = True
        REQUESTS_AVAILABLE = True
        print("Done!")


def load_state() -> dict:
    """Load state tracking last seen posts."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_state(state: dict):
    """Save state file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_seen_posts(state: dict, username: str) -> Set[str]:
    """Get set of already seen post IDs for a user."""
    return set(state.get(username, {}).get('seen_ids', []))


def add_seen_post(state: dict, username: str, post_id: str):
    """Mark a post as seen."""
    if username not in state:
        state[username] = {'seen_ids': []}
    state[username]['seen_ids'].append(post_id)
    # Keep only last 1000 IDs
    state[username]['seen_ids'] = state[username]['seen_ids'][-1000:]
    state[username]['last_check'] = datetime.now().isoformat()


def log_message(msg: str):
    """Log to file and print."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """Create safe filename from text."""
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'\s+', '_', safe).strip('_')
    return safe[:max_length] if safe else "untitled"


def parse_tweet_id_from_url(url: str) -> str:
    """Extract tweet ID from X/Nitter URL."""
    match = re.search(r'/status/(\d+)', url)
    return match.group(1) if match else hashlib.md5(url.encode()).hexdigest()[:16]


def clean_content(text: str) -> str:
    """Clean content for Markdown."""
    # Convert t.co links to plain (we'll have full URLs from RSS)
    text = re.sub(r'https?://t\.co/\w+', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\n+', '\n', text)
    return text.strip()


def parse_date(date_str: str) -> tuple:
    """Parse RSS date to date and timestamp."""
    try:
        # Common RSS date formats
        for fmt in [
            '%a, %d %b %Y %H:%M:%S %Z',
            '%a, %d %b %y %H:%M:%S %Z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%SZ',
        ]:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime('%Y-%m-%d'), dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                continue
    except:
        pass
    
    # Fallback
    now = datetime.now()
    return now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')


def feed_entry_to_markdown(entry, username: str) -> tuple:
    """Convert RSS entry to Obsidian Markdown. Returns (filename, content)."""
    
    # Get link (tweet URL)
    link = entry.get('link', '')
    tweet_id = parse_tweet_id_from_url(link)
    
    # Get content
    content = entry.get('description', entry.get('summary', entry.get('title', '')))
    content = clean_content(content)
    
    # Parse date
    published = entry.get('published', entry.get('updated', ''))
    date_str, timestamp = parse_date(published)
    
    # Author info
    author = entry.get('author', username)
    
    # Build markdown
    md = f"""---
author: "{username}"
date: {date_str}
timestamp: "{timestamp}"
tweet_id: "{tweet_id}"
url: "{link}"
source: "x.com"
tags: [x-posts, x-{username}, social-media]
---

## Original Post

{content}

---

**Source**: [@{username}]({link})
**Posted**: {timestamp}

"""
    
    # Generate filename
    text_preview = sanitize_filename(content, 30)
    filename = f"{date_str}-{text_preview}-{tweet_id}.md"
    
    return filename, md, tweet_id


def scrape_rss_feed(username: str, output_dir: Path, max_retries: int = 3) -> int:
    """Scrape RSS feed from Nitter instances."""
    
    username = username.lstrip('@')
    user_dir = output_dir / username
    user_dir.mkdir(parents=True, exist_ok=True)
    
    state = load_state()
    seen_ids = get_seen_posts(state, username)
    
    log_message(f"Fetching RSS for @{username}...")
    
    # Try each Nitter instance
    for instance in NITTER_INSTANCES[:max_retries]:
        try:
            rss_url = f"{instance}/{username}/rss"
            log_message(f"  Trying {instance}...")
            
            feed = feedparser.parse(rss_url)
            
            if feed.bozo and hasattr(feed, 'bozo_exception'):
                # Feed parsing error, try next instance
                continue
            
            if not feed.entries:
                log_message(f"  No entries found")
                continue
            
            # Process entries
            new_count = 0
            skipped_count = 0
            
            for entry in feed.entries:
                link = entry.get('link', '')
                tweet_id = parse_tweet_id_from_url(link)
                
                if tweet_id in seen_ids:
                    skipped_count += 1
                    continue
                
                filename, content, _ = feed_entry_to_markdown(entry, username)
                filepath = user_dir / filename
                
                # Save if not exists
                if not filepath.exists():
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    new_count += 1
                
                # Mark as seen
                add_seen_post(state, username, tweet_id)
            
            save_state(state)
            log_message(f"  ✓ Saved {new_count} new posts, skipped {skipped_count} existing")
            return new_count
            
        except Exception as e:
            log_message(f"  ✗ Failed: {e}")
            continue
    
    log_message(f"  All {max_retries} instances failed. Nitter may be down.")
    return 0


def scrape_all_history(username: str, output_dir: Path) -> int:
    """Try to scrape as much history as possible."""
    
    username = username.lstrip('@')
    
    log_message(f"\n=== Scraping all history for @{username} ===")
    log_message("Note: RSS feeds typically show last 20-30 tweets")
    log_message("For older posts, see alternative methods below\n")
    
    total = 0
    
    # Clear seen posts to re-fetch everything
    state = load_state()
    if username in state:
        prev_seen = len(state[username].get('seen_ids', []))
        state[username]['seen_ids'] = []
        log_message(f"Cleared {prev_seen} previously seen posts")
    
    save_state(state)
    
    # Try all Nitter instances to get max variety
    for instance in NITTER_INSTANCES:
        try:
            rss_url = f"{instance}/{username}/rss"
            log_message(f"Trying {instance}...")
            
            feed = feedparser.parse(rss_url)
            
            if not feed.entries:
                continue
            
            new_count = 0
            for entry in feed.entries:
                link = entry.get('link', '')
                tweet_id = parse_tweet_id_from_url(link)
                
                filename, content, _ = feed_entry_to_markdown(entry, username)
                filepath = output_dir / username / filename
                
                if not filepath.exists():
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    new_count += 1
                    total += 1
                
                # Always mark as seen
                state = load_state()
                add_seen_post(state, username, tweet_id)
                save_state(state)
            
            log_message(f"  Got {new_count} posts from this instance")
            
        except Exception as e:
            log_message(f"  Failed: {e}")
            continue
    
    log_message(f"\n=== Total new posts: {total} ===")
    log_message(f"Location: {output_dir / username}")
    
    if total == 0:
        print("\n" + "="*60)
        print("ALTERNATIVE METHODS FOR HISTORICAL TWEETS:")
        print("="*60)
        print("\n1. NITTER WEB (Manual browsing)")
        print(f"   https://nitter.net/{username}")
        print("   - Browse all tweets")
        print("   - Use SingleFile browser extension to save important ones")
        print("\n2. TWITTER ARCHIVE (If you own the account)")
        print("   Settings → Your account → Download archive")
        print("\n3. BROWSER EXTENSIONS")
        print("   - Twitter Media Downloader (Chrome/Firefox)")
        print("   - Social Focus (export to CSV/Markdown)")
        print("\n4. OFFICIAL X API (Paid)")
        print("   developer.x.com - $100/mo for basic access")
        print("="*60)
    
    return total


def show_status(username: str = None):
    """Show scraping status."""
    state = load_state()
    user_dir = OBSIDIAN_VAULT
    
    if username:
        username = username.lstrip('@')
        files = list((user_dir / username).glob("*.md")) if (user_dir / username).exists() else []
        seen = len(state.get(username, {}).get('seen_ids', []))
        last = state.get(username, {}).get('last_check', 'Never')
        
        print(f"\n@{username}:")
        print(f"  Files saved: {len(files)}")
        print(f"  Posts tracked: {seen}")
        print(f"  Last check: {last}")
    else:
        print("\nAll users:")
        for user, data in state.items():
            files = list((user_dir / user).glob("*.md")) if (user_dir / user).exists() else []
            print(f"  @{user}: {len(files)} files, {len(data.get('seen_ids', []))} tracked")
        if not state:
            print("  (None yet)")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape X/Twitter posts via Nitter RSS to Obsidian Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape latest posts
  python3 x_rss_to_obsidian.py --user BoboLucyWisdom
  
  # Scrape all available history (may get duplicates from multiple instances)
  python3 x_rss_to_obsidian.py --user BoboLucyWisdom --history
  
  # Run as daemon (check every 10 minutes)
  python3 x_rss_to_obsidian.py --user BoboLucyWisdom --daemon --interval 600
  
  # Show status
  python3 x_rss_to_obsidian.py --status --user BoboLucyWisdom
  
Limitations:
  - RSS feeds show ~20-30 most recent tweets only
  - Nitter instances may be blocked/restricted
  - No media download (links only)
        """
    )
    
    parser.add_argument('--user', '-u', type=str, help='X username to scrape')
    parser.add_argument('--history', action='store_true', help='Scrape all available history')
    parser.add_argument('--daemon', '-d', action='store_true', help='Run continuously')
    parser.add_argument('--interval', '-i', type=int, default=600,
                       help='Check interval in seconds (default: 600 = 10min)')
    parser.add_argument('--status', action='store_true', help='Show status')
    parser.add_argument('--output', '-o', type=Path, default=OBSIDIAN_VAULT,
                       help=f'Output directory (default: {OBSIDIAN_VAULT})')
    
    args = parser.parse_args()
    
    # Ensure dependencies
    ensure_dependencies()
    
    # Show status
    if args.status:
        show_status(args.user)
        return
    
    if not args.user:
        print("Error: Must specify --user")
        parser.print_help()
        sys.exit(1)
    
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Run
    try:
        if args.daemon:
            log_message(f"Starting daemon for @{args.user}...")
            while True:
                scrape_rss_feed(args.user, args.output)
                log_message(f"Sleeping {args.interval}s...")
                time.sleep(args.interval)
        elif args.history:
            scrape_all_history(args.user, args.output)
        else:
            scrape_rss_feed(args.user, args.output)
    except KeyboardInterrupt:
        log_message("\nInterrupted.")


if __name__ == "__main__":
    main()
