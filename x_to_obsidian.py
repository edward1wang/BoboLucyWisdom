#!/usr/bin/env python3
"""
x_to_obsidian.py
Scrape X/Twitter posts using Twikit (no auth required for public tweets).

Limitations:
  - ~50 tweets per request (Twikit limitation)
  - May break if X changes endpoints
  - No guarantee of completeness

Usage:
    # Get latest 50 tweets from a user
    python3 x_to_obsidian.py --user elonmusk
    
    # Get specific tweet
    python3 x_to_obsidian.py --url https://x.com/user/status/123456789
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

# Config
OBSIDIAN_VAULT = Path.home() / "brain" / "x-posts"
STATE_FILE = Path.home() / ".config" / "x_to_obsidian" / "state.json"

# Try to import twikit
try:
    from twikit import Client
    TWIKIT_AVAILABLE = True
except ImportError:
    TWIKIT_AVAILABLE = False


def ensure_twikit():
    """Ensure twikit is installed."""
    global TWIKIT_AVAILABLE
    if not TWIKIT_AVAILABLE:
        print("twikit not installed. Installing...")
        venv_path = Path.home() / ".venvs" / "xscraper"
        if not venv_path.exists():
            os.makedirs(venv_path.parent, exist_ok=True)
            os.system(f"python3 -m venv {venv_path}")
        
        pip_path = venv_path / "bin" / "pip"
        os.system(f"{pip_path} install twikit -q")
        
        # Re-import
        try:
            import importlib
            sys.path.insert(0, str(venv_path / "lib" / "python3.14" / "site-packages"))
            from twikit import Client
            global Client
            TWIKIT_AVAILABLE = True
            print("twikit installed!")
        except ImportError as e:
            print(f"Failed to install twikit: {e}")
            sys.exit(1)


def load_state() -> Dict:
    """Load state file with last tweet IDs per user."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_state(state: Dict):
    """Save state file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_last_tweet_id(state: Dict, username: str) -> Optional[str]:
    """Get last scraped tweet ID for a user."""
    return state.get(username, {}).get('last_tweet_id')


def set_last_tweet_id(state: Dict, username: str, tweet_id: str):
    """Update last tweet ID for a user."""
    if username not in state:
        state[username] = {}
    state[username]['last_tweet_id'] = tweet_id
    state[username]['last_scraped'] = datetime.now().isoformat()


def sanitize_filename(text: str, max_length: int = 50) -> str:
    """Create safe filename from tweet text."""
    safe = re.sub(r'[^\w\s-]', '', text)
    safe = re.sub(r'\s+', '_', safe).strip('_')
    return safe[:max_length] if safe else "untitled"


def clean_tweet_text(text: str) -> str:
    """Clean tweet text for Markdown."""
    text = re.sub(r'https?://t\.co/\w+', '', text)
    text = re.sub(r'#(\w+)', r'`#\1`', text)
    text = re.sub(r'@(\w+)', r'[@\1](https://x.com/\1)', text)
    return text.strip()


def tweet_to_markdown(tweet, author: str) -> str:
    """Convert tweet to Obsidian-compatible Markdown."""
    
    # Extract data from tweet object
    tweet_id = tweet.id if hasattr(tweet, 'id') else 'unknown'
    text = tweet.text if hasattr(tweet, 'text') else str(tweet)
    created_at = tweet.created_at if hasattr(tweet, 'created_at') else datetime.now().isoformat()
    
    # Engagement stats
    favorite_count = tweet.favorite_count if hasattr(tweet, 'favorite_count') else 0
    retweet_count = tweet.retweet_count if hasattr(tweet, 'retweet_count') else 0
    reply_count = tweet.reply_count if hasattr(tweet, 'reply_count') else 0
    view_count = tweet.view_count if hasattr(tweet, 'view_count') else None
    
    # Author display name
    display_name = author
    if hasattr(tweet, 'user') and tweet.user:
        display_name = tweet.user.name if hasattr(tweet.user, 'name') else author
    
    # Check if reply/quote
    is_reply = text.startswith('@') if text else False
    is_quote = hasattr(tweet, 'quoted') and tweet.quoted
    
    # Parse date
    try:
        if isinstance(created_at, str):
            dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
        else:
            dt = datetime.now()
        date_str = dt.strftime('%Y-%m-%d')
        timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        date_str = datetime.now().strftime('%Y-%m-%d')
        timestamp = date_str
    
    tweet_url = f"https://x.com/{author}/status/{tweet_id}"
    clean_text = clean_tweet_text(text)
    
    # Build frontmatter
    frontmatter = f"""---
author: "{author}"
author_display: "{display_name}"
date: {date_str}
timestamp: "{timestamp}"
tweet_id: "{tweet_id}"
url: "{tweet_url}"
likes: {favorite_count}
retweets: {retweet_count}
replies: {reply_count}
views: {view_count if view_count else 'null'}
is_reply: {str(is_reply).lower()}
is_quote: {str(is_quote).lower()}
source: "x.com"
tags: [x-posts, x-{author}, social-media]
---

"""
    
    # Build body
    body = f"""## Original Post

{clean_text}

---

**Source**: [{display_name} (@{author})]({tweet_url})
**Posted**: {timestamp}
**Engagement**: {favorite_count:,} likes | {retweet_count:,} retweets | {reply_count:,} replies{f' | {view_count:,} views' if view_count else ''}

"""
    
    # Add media if present
    if hasattr(tweet, 'media') and tweet.media:
        body += "\n### Media\n\n"
        for media in tweet.media:
            if hasattr(media, 'url') and media.url:
                body += f"![]({media.url})\n\n"
    
    return frontmatter + body


def save_tweet(tweet, author: str, user_dir: Path) -> bool:
    """Save tweet to Markdown file. Returns True if new file created."""
    tweet_id = tweet.id if hasattr(tweet, 'id') else str(hash(str(tweet)))
    text = tweet.text if hasattr(tweet, 'text') else str(tweet)
    created_at = tweet.created_at if hasattr(tweet, 'created_at') else datetime.now()
    
    # Parse date for filename
    try:
        if isinstance(created_at, str):
            dt = datetime.strptime(created_at, '%a %b %d %H:%M:%S +0000 %Y')
        else:
            dt = datetime.now()
        date_str = dt.strftime('%Y-%m-%d')
    except:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    text_preview = sanitize_filename(text, 30)
    filename = f"{date_str}-{text_preview}-{tweet_id}.md"
    filepath = user_dir / filename
    
    if filepath.exists():
        return False  # Already exists
    
    md_content = tweet_to_markdown(tweet, author)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return True


async def scrape_user_twikit(username: str, limit: int = 50, output_dir: Path = OBSIDIAN_VAULT) -> int:
    """Scrape tweets from a user using Twikit."""
    
    username = username.lstrip('@')
    user_dir = output_dir / username
    user_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Scraping @{username} using Twikit...")
    print(f"Output: {user_dir}")
    print(f"Note: Twikit loads ~{limit} tweets max per run")
    
    # Initialize Twikit client (no auth needed for public tweets)
    client = Client('en-US')
    
    try:
        # Get user by screen name
        user = await client.get_user_by_screen_name(username)
        print(f"Found user: {user.name} (@{user.screen_name})")
        
        # Get tweets
        tweets = await client.get_user_tweets(user.id, 'Tweets', limit=limit)
        
        saved_count = 0
        skipped_count = 0
        newest_id = None
        
        for tweet in tweets:
            if save_tweet(tweet, username, user_dir):
                saved_count += 1
                print(f"  [{saved_count}] {tweet.id[:10]}... - {tweet.created_at[:10] if hasattr(tweet, 'created_at') else 'unknown'}")
                
                # Track newest ID
                if newest_id is None or (hasattr(tweet, 'id') and tweet.id > newest_id):
                    newest_id = tweet.id
            else:
                skipped_count += 1
        
        # Update state
        if newest_id:
            state = load_state()
            current_last = get_last_tweet_id(state, username)
            if current_last is None or (newest_id and newest_id > current_last):
                set_last_tweet_id(state, username, newest_id)
                save_state(state)
        
        print(f"\n✓ Done! New: {saved_count} | Existing: {skipped_count}")
        print(f"  Last tweet ID: {newest_id}")
        print(f"\nNote: Twikit has limitations:")
        print(f"  - Usually returns ~40-50 tweets per run")
        print(f"  - To get more history, run multiple times over several days")
        print(f"  - For complete history, use official X API ($$$)")
        
        return saved_count
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check username exists and is public")
        print("2. Twikit may need update: pip install -U twikit")
        print("3. X may have changed their endpoints")
        raise


async def scrape_single_tweet(url: str, output_dir: Path = OBSIDIAN_VAULT):
    """Scrape a single tweet by URL using Twikit."""
    
    match = re.search(r'/status/(\d+)', url)
    if not match:
        raise ValueError(f"Could not extract tweet ID from URL: {url}")
    
    tweet_id = match.group(1)
    
    client = Client('en-US')
    
    try:
        # Note: Twikit's get_tweet_by_id may require auth in newer versions
        # This is a limitation of the free approach
        print(f"Looking up tweet {tweet_id}...")
        
        # Try to get tweet - this may fail without auth
        tweet = await client.get_tweet_by_id(tweet_id)
        author = tweet.user.screen_name if hasattr(tweet, 'user') and tweet.user else 'unknown'
        
        user_dir = output_dir / author
        user_dir.mkdir(parents=True, exist_ok=True)
        
        if save_tweet(tweet, author, user_dir):
            print(f"Saved: {author}/{tweet_id}")
        else:
            print(f"Already exists: {author}/{tweet_id}")
        
        return user_dir / f"{tweet.created_at.strftime('%Y-%m-%d') if hasattr(tweet, 'created_at') else 'unknown'}-{sanitize_filename(tweet.text if hasattr(tweet, 'text') else '', 30)}-{tweet_id}.md"
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nNote: Single tweet lookup may require authentication.")
        print("Try scraping by username instead: --user <username>")
        raise


def show_status(username: str = None):
    """Show scraping status."""
    state = load_state()
    user_dir = OBSIDIAN_VAULT
    
    if username:
        username = username.lstrip('@')
        last_id = get_last_tweet_id(state, username)
        user_files = list((user_dir / username).glob("*.md")) if (user_dir / username).exists() else []
        
        print(f"\n@{username}:")
        print(f"  Total files: {len(user_files)}")
        print(f"  Last tweet ID: {last_id or 'Not set'}")
        print(f"  Last scraped: {state.get(username, {}).get('last_scraped', 'Never')}")
    else:
        print("\nAll monitored users:")
        for user, data in state.items():
            user_files = list((user_dir / user).glob("*.md")) if (user_dir / user).exists() else []
            print(f"  @{user}: {len(user_files)} files")
        if not state:
            print("  (None yet)")


def main():
    parser = argparse.ArgumentParser(
        description='Scrape X/Twitter posts to Obsidian Markdown (Twikit version - no auth required)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape latest tweets from a user (~50 tweets)
  python3 x_to_obsidian.py --user elonmusk
  
  # Scrape with custom limit (Twikit may ignore this)
  python3 x_to_obsidian.py --user elonmusk --limit 100
  
  # Check status
  python3 x_to_obsidian.py --status --user elonmusk
  
Limitations:
  - Returns ~40-50 tweets per run (Twikit limitation)
  - No authentication required for public profiles
  - Private profiles will fail
  - May break if X changes their API
        """
    )
    
    parser.add_argument('--user', '-u', type=str, help='X username to scrape')
    parser.add_argument('--url', type=str, help='Single tweet URL (may require auth)')
    parser.add_argument('--limit', '-l', type=int, default=50, help='Max tweets (default: 50)')
    parser.add_argument('--status', action='store_true', help='Show scraping status')
    parser.add_argument('--output', '-o', type=Path, default=OBSIDIAN_VAULT,
                       help=f'Output directory (default: {OBSIDIAN_VAULT})')
    
    args = parser.parse_args()
    
    # Ensure twikit is available
    ensure_twikit()
    
    # Status check
    if args.status:
        show_status(args.user)
        return
    
    # Validate
    if not args.user and not args.url:
        print("Error: Must specify --user or --url")
        parser.print_help()
        sys.exit(1)
    
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Execute
    try:
        if args.user:
            asyncio.run(scrape_user_twikit(args.user, args.limit, args.output))
        elif args.url:
            asyncio.run(scrape_single_tweet(args.url, args.output))
    except KeyboardInterrupt:
        print("\n\nInterrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
