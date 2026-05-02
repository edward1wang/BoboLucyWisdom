#!/usr/bin/env python3
"""
x_monitor_simple.py
Simple Playwright script to monitor X user.
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

DATA_DIR = Path.home() / ".config" / "x_monitor"
COOKIES_FILE = DATA_DIR / "cookies.json"
VAULT_DIR = Path.home() / "brain" / "x-posts"


def setup():
    """Manual setup - open browser and wait for user to close."""
    print("\n" + "="*60)
    print("X LOGIN SETUP")
    print("="*60)
    print("\n1. A browser will open")
    print("2. Navigate to https://x.com and login manually")
    print("3. Once logged in and you see your feed, close the browser")
    print("4. Your session will be saved\n")
    
    input("Press Enter to continue...")
    
    with sync_playwright() as p:
        # Launch visible browser
        browser = p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled']
        )
        
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = context.new_page()
        
        # Open X homepage
        print("Opening browser...")
        page.goto("https://x.com")
        
        print("\nBrowser opened. Please:")
        print("- If not logged in, click 'Sign in' and complete login")
        print("- Once you see your home feed, CLOSE the browser window")
        print("Waiting...\n")
        
        # Keep browser open until user closes it
        try:
            while True:
                try:
                    # Check if page is still accessible
                    url = page.url
                    time.sleep(2)
                except:
                    # Browser closed
                    break
        except KeyboardInterrupt:
            pass
        
        # Save cookies
        print("\nSaving session...")
        try:
            cookies = context.cookies()
            storage = context.storage_state()
            
            DATA_DIR.mkdir(parents=True, exist_ok=True)
            
            with open(COOKIES_FILE, 'w') as f:
                json.dump({'cookies': cookies, 'storage': storage}, f)
            
            print(f"✓ Session saved to {COOKIES_FILE}")
        except Exception as e:
            print(f"Warning: {e}")
        
        try:
            browser.close()
        except:
            pass
        
        print("\n✓ Setup complete!")


def monitor(username: str):
    """Monitor user for new tweets."""
    username = username.lstrip('@')
    user_dir = VAULT_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = DATA_DIR / f"{username}_state.json"
    seen_ids = set()
    if state_file.exists():
        try:
            with open(state_file) as f:
                data = json.load(f)
                seen_ids = set(data.get('seen_ids', []))
        except:
            pass
    
    print(f"\nMonitoring @{username}...")
    print(f"Previously seen: {len(seen_ids)} tweets")
    
    if not COOKIES_FILE.exists():
        print("\n⚠️ Not logged in. Run: python3 x_monitor_simple.py --setup")
        return
    
    new_tweets = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Load saved session
        try:
            with open(COOKIES_FILE) as f:
                session = json.load(f)
            
            context = browser.new_context(
                storage_state=session.get('storage'),
                viewport={'width': 1280, 'height': 800}
            )
        except Exception as e:
            print(f"Error loading session: {e}")
            browser.close()
            return
        
        page = context.new_page()
        
        try:
            # Navigate to user profile
            url = f"https://x.com/{username}"
            print(f"  Visiting {url}...")
            page.goto(url, wait_until='domcontentloaded')
            
            # Wait for content
            time.sleep(5)
            
            # Scroll to load tweets
            print("  Loading tweets...")
            for _ in range(3):
                page.evaluate('window.scrollBy(0, 800)')
                time.sleep(2)
            
            # Extract tweets
            articles = page.query_selector_all('article')
            print(f"  Found {len(articles)} tweets")
            
            for article in articles[:20]:  # Process first 20
                try:
                    # Get link
                    link = article.query_selector('a[href*="/status/"]')
                    if not link:
                        continue
                    
                    href = link.get_attribute('href') or ''
                    tweet_id = href.split('/status/')[-1].split('?')[0] if '/status/' in href else ''
                    
                    if not tweet_id or tweet_id in seen_ids:
                        continue
                    
                    # Get text
                    text_elem = article.query_selector('[data-testid="tweetText"]')
                    text = text_elem.inner_text() if text_elem else ''
                    
                    # Get date
                    time_elem = article.query_selector('time')
                    date_str = datetime.now().strftime('%Y-%m-%d')
                    if time_elem:
                        dt_attr = time_elem.get_attribute('datetime')
                        if dt_attr:
                            try:
                                dt = datetime.fromisoformat(dt_attr.replace('Z', '+00:00'))
                                date_str = dt.strftime('%Y-%m-%d')
                            except:
                                pass
                    
                    # Get stats
                    likes = 0
                    try:
                        like_elem = article.query_selector('[data-testid="like"]')
                        if like_elem:
                            label = like_elem.get_attribute('aria-label') or '0'
                            match = re.search(r'(\d+)', label.replace(',', ''))
                            if match:
                                likes = int(match.group(1))
                    except:
                        pass
                    
                    new_tweets.append({
                        'id': tweet_id,
                        'text': text,
                        'date': date_str,
                        'likes': likes,
                        'url': f"https://x.com/{username}/status/{tweet_id}"
                    })
                    
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"  Error: {e}")
        
        browser.close()
    
    # Save new tweets
    if new_tweets:
        print(f"\n  Saving {len(new_tweets)} new tweets:")
        for tweet in new_tweets:
            # Create filename
            safe_text = re.sub(r'[^\w\s-]', '', tweet['text'])[:30].strip()
            safe_text = re.sub(r'\s+', '_', safe_text)
            filename = f"{tweet['date']}-{safe_text}-{tweet['id']}.md"
            filepath = user_dir / filename
            
            if filepath.exists():
                continue
            
            # Write markdown
            md = f"""---
author: "{username}"
date: {tweet['date']}
tweet_id: "{tweet['id']}"
url: "{tweet['url']}"
likes: {tweet['likes']}
tags: [x-posts, x-{username}, tracked]
---

## Tweet

{tweet['text']}

---

**Source**: [@{username}]({tweet['url']})
**Date**: {tweet['date']}
**Likes**: {tweet['likes']}
"""
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(md)
            
            print(f"    ✓ {filename}")
            seen_ids.add(tweet['id'])
        
        # Save state
        with open(state_file, 'w') as f:
            json.dump({'seen_ids': list(seen_ids)}, f)
    else:
        print("  No new tweets found.")
    
    print(f"\n✓ Total tracked: {len(seen_ids)} tweets")
    print(f"  Location: {user_dir}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--setup', action='store_true', help='Setup login')
    parser.add_argument('--user', '-u', help='Username to monitor')
    args = parser.parse_args()
    
    if args.setup:
        setup()
    elif args.user:
        monitor(args.user)
    else:
        print("Usage:")
        print("  python3 x_monitor_simple.py --setup")
        print("  python3 x_monitor_simple.py --user BoboLucyWisdom")


if __name__ == "__main__":
    main()
