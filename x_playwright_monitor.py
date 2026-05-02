#!/usr/bin/env python3
"""
x_playwright_monitor.py
Track X/Twitter user tweets using Playwright browser automation.

Usage:
    # First run - setup browser and login
    python3 x_playwright_monitor.py --setup
    
    # Daily check for new tweets
    python3 x_playwright_monitor.py --user BoboLucyWisdom
    
    # Add to cron for daily monitoring
    0 9 * * * cd /Users/dawang/workspace && python3 x_playwright_monitor.py --user BoboLucyWisdom
"""

import argparse
import json
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Set

# Config
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = Path.home() / ".config" / "x_monitor"
STATE_FILE = DATA_DIR / "state.json"
COOKIES_FILE = DATA_DIR / "cookies.json"
VAULT_DIR = Path.home() / "brain" / "x-posts"


def ensure_playwright():
    """Ensure playwright is installed."""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except ImportError:
        print("Installing playwright...")
        import subprocess
        subprocess.run([sys.executable, "-m", "pip", "install", "playwright", "-q"])
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
        print("Playwright installed!")
        return True


def load_state() -> dict:
    """Load state with seen tweet IDs."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_state(state: dict):
    """Save state."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_seen_ids(state: dict, username: str) -> Set[str]:
    """Get set of seen tweet IDs for user."""
    return set(state.get(username, {}).get('seen_ids', []))


def add_seen_id(state: dict, username: str, tweet_id: str):
    """Mark tweet as seen."""
    if username not in state:
        state[username] = {'seen_ids': []}
    state[username]['seen_ids'].append(tweet_id)
    # Keep last 5000
    state[username]['seen_ids'] = state[username]['seen_ids'][-5000:]
    state[username]['last_check'] = datetime.now().isoformat()


def sanitize_filename(text: str, max_length: int = 40) -> str:
    """Create safe filename."""
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'\s+', '_', safe).strip('_')
    return safe[:max_length] if safe else "untitled"


def format_tweet_markdown(tweet_data: dict) -> str:
    """Convert tweet data to Markdown."""
    author = tweet_data.get('author', 'unknown')
    text = tweet_data.get('text', '')
    tweet_id = tweet_data.get('id', '')
    date_str = tweet_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    timestamp = tweet_data.get('timestamp', datetime.now().isoformat())
    likes = tweet_data.get('likes', 0)
    retweets = tweet_data.get('retweets', 0)
    replies = tweet_data.get('replies', 0)
    url = f"https://x.com/{author}/status/{tweet_id}"
    
    # Clean text
    clean_text = re.sub(r'https?://t\.co/\w+', '', text)
    clean_text = re.sub(r'#(\w+)', r'`#\1`', clean_text)
    clean_text = re.sub(r'@(\w+)', r'[@\1](https://x.com/\1)', clean_text)
    
    md = f"""---
author: "{author}"
date: {date_str}
timestamp: "{timestamp}"
tweet_id: "{tweet_id}"
url: "{url}"
likes: {likes}
retweets: {retweets}
replies: {replies}
source: "x.com"
tags: [x-posts, x-{author}, social-media, tracked]
---

## Original Post

{clean_text}

---

**Source**: [@{author}]({url})
**Posted**: {timestamp}
**Engagement**: {likes:,} likes | {retweets:,} retweets | {replies:,} replies

"""
    
    # Add images if present
    media = tweet_data.get('media', [])
    if media:
        md += "### Media\n\n"
        for img_url in media:
            md += f"![]({img_url})\n\n"
    
    return md


def save_tweet(tweet_data: dict, user_dir: Path) -> bool:
    """Save tweet as Markdown file."""
    tweet_id = tweet_data.get('id', '')
    text = tweet_data.get('text', '')
    date_str = tweet_data.get('date', datetime.now().strftime('%Y-%m-%d'))
    author = tweet_data.get('author', 'unknown')
    
    text_preview = sanitize_filename(text, 25)
    filename = f"{date_str}-{text_preview}-{tweet_id}.md"
    filepath = user_dir / filename
    
    if filepath.exists():
        return False
    
    md = format_tweet_markdown(tweet_data)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md)
    
    return True


def setup_browser():
    """Interactive setup to login and save cookies."""
    from playwright.sync_api import sync_playwright
    import threading
    
    print("\n=== X Login Setup ===")
    print("A browser window will open. Please:")
    print("1. Complete the X login process")
    print("2. Once you're logged in and see the home feed, close the browser")
    print("3. Cookies will be saved automatically\n")
    
    # Use a file-based signal for manual completion
    DONE_FILE = DATA_DIR / "login_done"
    if DONE_FILE.exists():
        DONE_FILE.unlink()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        page = context.new_page()
        page.goto("https://x.com/i/flow/login")
        
        print("Browser opened. Complete login and close the window.")
        print("(Waiting for browser to close...)\n")
        
        # Wait for browser to close (user closes it after login)
        try:
            # Poll every second to see if browser still open
            while True:
                # Check if browser is still connected
                try:
                    # Simple check - if we can access page, browser is still open
                    _ = page.url
                    time.sleep(1)
                except:
                    # Browser closed
                    break
        except KeyboardInterrupt:
            print("\nInterrupted.")
        
        try:
            # Try to save cookies even if browser is closing
            print("Saving cookies...")
            # Get cookies before closing
            cookies = context.cookies()
            
            # Save cookies
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            with open(COOKIES_FILE, 'w') as f:
                json.dump(cookies, f)
            
            print(f"✓ Cookies saved to {COOKIES_FILE}")
            browser.close()
        except Exception as e:
            print(f"Note: {e}")
            pass
        
        print("\n✓ Setup complete!")
        print("You can now run: ~/workspace/x_monitor_wrapper.sh --user BoboLucyWisdom")


def extract_tweets_from_page(page, username: str) -> list:
    """Extract tweet data from X profile page."""
    tweets = []
    
    # Wait for tweets to load
    page.wait_for_selector('article[data-testid="tweet"]', timeout=30000)
    
    # Get all tweet articles
    tweet_articles = page.query_selector_all('article[data-testid="tweet"]')
    
    for article in tweet_articles:
        try:
            # Tweet ID from link
            link_elem = article.query_selector('a[href*="/status/"]')
            if not link_elem:
                continue
            
            href = link_elem.get_attribute('href')
            tweet_id = href.split('/status/')[-1].split('?')[0] if '/status/' in href else None
            if not tweet_id:
                continue
            
            # Tweet text - try multiple selectors
            text = ""
            text_selectors = [
                '[data-testid="tweetText"]',
                'div[lang]',
            ]
            for sel in text_selectors:
                text_elem = article.query_selector(sel)
                if text_elem:
                    text = text_elem.inner_text()
                    break
            
            # Time/date
            time_elem = article.query_selector('time')
            date_str = datetime.now().strftime('%Y-%m-%d')
            timestamp = datetime.now().isoformat()
            if time_elem:
                datetime_attr = time_elem.get_attribute('datetime')
                if datetime_attr:
                    try:
                        dt = datetime.fromisoformat(datetime_attr.replace('Z', '+00:00'))
                        date_str = dt.strftime('%Y-%m-%d')
                        timestamp = dt.isoformat()
                    except:
                        pass
            
            # Engagement stats
            likes = 0
            retweets = 0
            replies = 0
            
            # Look for engagement numbers in aria-labels
            for elem in article.query_selector_all('[aria-label*="likes"]'):
                label = elem.get_attribute('aria-label') or ''
                match = re.search(r'(\d+)\s+like', label.lower())
                if match:
                    likes = int(match.group(1))
                break
            
            # Media images
            media = []
            for img in article.query_selector_all('img[src*="twimg.com"]'):
                src = img.get_attribute('src')
                if src and 'profile_images' not in src:
                    media.append(src)
            
            tweets.append({
                'id': tweet_id,
                'text': text,
                'author': username,
                'date': date_str,
                'timestamp': timestamp,
                'likes': likes,
                'retweets': retweets,
                'replies': replies,
                'media': media,
            })
            
        except Exception as e:
            print(f"  Error parsing tweet: {e}")
            continue
    
    return tweets


def monitor_user(username: str, max_tweets: int = 50):
    """Monitor user for new tweets."""
    from playwright.sync_api import sync_playwright
    
    username = username.lstrip('@')
    user_dir = VAULT_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    
    state = load_state()
    seen_ids = get_seen_ids(state, username)
    
    print(f"\nMonitoring @{username}...")
    print(f"Already seen: {len(seen_ids)} tweets")
    
    if not COOKIES_FILE.exists():
        print("\n⚠️ Not logged in! Run --setup first")
        return 0
    
    new_count = 0
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800}
        )
        
        # Load cookies
        with open(COOKIES_FILE) as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        
        page = context.new_page()
        
        try:
            # Navigate to profile
            url = f"https://x.com/{username}"
            print(f"  Visiting {url}...")
            page.goto(url, wait_until='networkidle')
            
            # Wait for content
            page.wait_for_timeout(3000)
            
            # Extract tweets
            tweets = extract_tweets_from_page(page, username)
            print(f"  Found {len(tweets)} tweets on page")
            
            # Process new tweets
            for tweet in tweets[:max_tweets]:
                tweet_id = tweet['id']
                
                if tweet_id in seen_ids:
                    continue
                
                if save_tweet(tweet, user_dir):
                    new_count += 1
                    print(f"  [NEW] {tweet_id}: {tweet['text'][:50]}...")
                
                add_seen_id(state, username, tweet_id)
            
            save_state(state)
            
        except Exception as e:
            print(f"  Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            browser.close()
    
    print(f"\n✓ Done! Found {new_count} new tweets")
    print(f"  Saved to: {user_dir}")
    print(f"  Total tracked: {len(seen_ids) + new_count}")
    
    return new_count


def main():
    parser = argparse.ArgumentParser(
        description='Monitor X/Twitter users with Playwright',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup (login once)
  python3 x_playwright_monitor.py --setup
  
  # Check for new tweets
  python3 x_playwright_monitor.py --user BoboLucyWisdom
  
  # Cron job (daily at 9am)
  0 9 * * * cd /Users/dawang/workspace && python3 x_playwright_monitor.py --user BoboLucyWisdom
        """
    )
    
    parser.add_argument('--setup', action='store_true', help='Setup browser login')
    parser.add_argument('--user', '-u', type=str, help='Username to monitor')
    parser.add_argument('--max', '-m', type=int, default=50, help='Max tweets to check (default: 50)')
    parser.add_argument('--status', action='store_true', help='Show monitoring status')
    
    args = parser.parse_args()
    
    # Install dependencies
    ensure_playwright()
    
    if args.status:
        state = load_state()
        print("\nMonitored users:")
        for user, data in state.items():
            seen = len(data.get('seen_ids', []))
            last = data.get('last_check', 'Never')
            print(f"  @{user}: {seen} tweets tracked, last check {last}")
        return
    
    if args.setup:
        setup_browser()
    elif args.user:
        import time
        monitor_user(args.user, args.max)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
