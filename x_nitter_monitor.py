#!/usr/bin/env python3
"""
x_nitter_monitor.py
Monitor X users via Nitter RSS using direct HTTP requests.
"""

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Set

# Config
VAULT_DIR = Path.home() / "brain" / "x-posts"
DATA_DIR = Path.home() / ".config" / "x_to_obsidian"
STATE_FILE = DATA_DIR / "nitter_state.json"


def load_state() -> dict:
    """Load state with seen posts."""
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
    """Get set of seen GUIDs."""
    return set(state.get(username, {}).get('seen_ids', []))


def mark_seen(state: dict, username: str, guid: str):
    """Mark post as seen."""
    if username not in state:
        state[username] = {'seen_ids': []}
    state[username]['seen_ids'].append(guid)
    # Keep last 10000
    state[username]['seen_ids'] = state[username]['seen_ids'][-10000:]
    state[username]['last_check'] = datetime.now().isoformat()


def strip_html(html: str) -> str:
    """Remove HTML tags from content."""
    text = re.sub(r'<script[^>]*>[^<]*</script>', '', html, flags=re.DOTALL)
    text = re.sub(r'<style[^>]*>[^<]*</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = text.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
    text = text.replace('&#39;', "'").replace('&quot;', '"').replace('&nbsp;', ' ')
    return text


def sanitize_filename(text: str, max_length: int = 40) -> str:
    """Create safe filename."""
    safe = re.sub(r'[^\w\u4e00-\u9fff\s-]', '', text)
    safe = re.sub(r'\s+', '_', safe).strip('_')
    return safe[:max_length] if safe else "untitled"


def parse_rss_date(date_str: str) -> tuple:
    """Parse RSS pubDate."""
    try:
        from email.utils import parsedate_to_datetime
        dt = parsedate_to_datetime(date_str)
        return dt.strftime('%Y-%m-%d'), dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        now = datetime.now()
        return now.strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d %H:%M:%S')


def parse_item(item_elem) -> dict:
    """Parse RSS item element."""
    result = {}
    
    for child in item_elem:
        tag = child.tag
        if '}' in tag:
            tag = tag.split('}')[1]  # Remove namespace
        
        if tag == 'title':
            result['title'] = child.text or ''
        elif tag == 'link':
            result['link'] = child.text or ''
        elif tag == 'description':
            result['description'] = child.text or ''
        elif tag == 'pubDate':
            result['published'] = child.text or ''
        elif tag == 'guid':
            result['guid'] = child.text or ''
        elif tag == 'creator':
            result['author'] = child.text or ''
    
    return result


def fetch_feed_v2(username: str) -> list:
    """Fetch RSS using curl subprocess."""
    import subprocess
    import time
    
    instances = [
        "https://nitter.net",
        "https://nitter.it", 
        "https://nitter.cz",
    ]
    
    entries = []
    
    for instance in instances:
        url = f"{instance}/{username}/rss"
        print(f"  Trying {instance}...")
        
        try:
            result = subprocess.run(
                ['curl', '-sL', '-A', 'Mozilla/5.0', '--max-time', '15', url],
                capture_output=True,
                text=True,
                timeout=20
            )
            
            if result.returncode != 0 or not result.stdout:
                continue
            
            # Parse XML
            try:
                root = ET.fromstring(result.stdout)
            except:
                print(f"    Invalid XML response")
                continue
            
            # Find channel and items
            channel = root.find('.//channel') or root
            items = channel.findall('.//item') or root.findall('.//item')
            
            for item in items:
                entry = parse_item(item)
                if entry.get('title') or entry.get('description'):
                    entries.append(entry)
            
            if entries:
                print(f"    ✓ Got {len(entries)} entries")
                return entries
            
            time.sleep(1)  # Be nice between requests
            
        except Exception as e:
            print(f"    Error: {e}")
            continue
    
    return entries


def save_tweet(entry: dict, username: str, user_dir: Path) -> bool:
    """Save RSS entry as Markdown."""
    
    guid = entry.get('guid', '')
    title = entry.get('title', '')
    link = entry.get('link', '')
    pub_date = entry.get('published', '')
    description = entry.get('description', '')
    
    # Get tweet ID
    tweet_id = guid
    if not tweet_id and link:
        match = re.search(r'/status/(\d+)', link)
        if match:
            tweet_id = match.group(1)
    if not tweet_id:
        tweet_id = hashlib.md5((title + link).encode()).hexdigest()[:16]
    
    # Use description as content (title is often truncated)
    # Strip CDATA wrapper if present
    content = description
    if content.startswith('<![CDATA['):
        content = content[9:-3]
    content = strip_html(content)
    
    # Parse date
    if pub_date:
        date_str, timestamp = parse_rss_date(pub_date)
    else:
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Generate filename
    text_preview = sanitize_filename(content, 30)
    filename = f"{date_str}-{text_preview}-{tweet_id}.md"
    filepath = user_dir / filename
    
    if filepath.exists():
        return False
    
    # Build Markdown
    clean_content = re.sub(r'https?://t\.co/\w+', '', content)
    clean_content = re.sub(r'#(\w+)', r'`#\1`', clean_content)
    
    md = f"""---
author: "{username}"
date: {date_str}
timestamp: "{timestamp}"
tweet_id: "{tweet_id}"
url: "{link}"
source: "x.com"
tags: [x-posts, x-{username}, nitter]
---

## Post

{clean_content}

---

**Source**: [@{username}]({link})
**Posted**: {timestamp}

"""
    
    # Extract images from description
    img_matches = re.findall(r'src=["\'](https://nitter\.net/pic/[^"\']+)["\']', description)
    if img_matches:
        md += "### Media\n\n"
        for img_url in img_matches[:5]:  # Max 5 images
            # Convert nitter to twitter CDN
            actual_url = img_url.replace('https://nitter.net/pic/', 'https://')
            actual_url = actual_url.replace('%2F', '/')
            actual_url = actual_url.replace('media%2F', 'pbs.twimg.com/media/')
            md += f"![]({actual_url})\n\n"
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(md)
    
    return True


def monitor(username: str) -> int:
    """Monitor user and save new tweets."""
    
    username = username.lstrip('@')
    user_dir = VAULT_DIR / username
    user_dir.mkdir(parents=True, exist_ok=True)
    
    state = load_state()
    seen_ids = get_seen_ids(state, username)
    
    print(f"\nMonitoring @{username} via Nitter RSS...")
    print(f"Previously seen: {len(seen_ids)} tweets")
    print(f"Saving to: {user_dir}\n")
    
    # Fetch feed
    entries = fetch_feed_v2(username)
    
    if not entries:
        print("⚠️ No entries found")
        return 0
    
    print(f"\nProcessing {len(entries)} entries...")
    
    new_count = 0
    skipped_count = 0
    
    for entry in entries:
        guid = entry.get('guid', '')
        if not guid:
            # Use link as fallback
            guid = entry.get('link', '')
        
        if not guid:
            continue
        
        if guid in seen_ids:
            skipped_count += 1
            continue
        
        if save_tweet(entry, username, user_dir):
            title_preview = entry.get('title', '')[:50]
            print(f"  [NEW] {title_preview}...")
            new_count += 1
        
        mark_seen(state, username, guid)
    
    save_state(state)
    
    print(f"\n✓ Done!")
    print(f"  New: {new_count} | Skipped (already saved): {skipped_count}")
    print(f"  Total tracked: {len(seen_ids) + new_count}")
    
    return new_count


def show_status(username: str = None):
    """Show monitoring status."""
    state = load_state()
    
    if username:
        username = username.lstrip('@')
        files = list((VAULT_DIR / username).glob("*.md")) if (VAULT_DIR / username).exists() else []
        seen = len(state.get(username, {}).get('seen_ids', []))
        last = state.get(username, {}).get('last_check', 'Never')
        
        print(f"\n@{username}:")
        print(f"  Files saved: {len(files)}")
        print(f"  Posts tracked: {seen}")
        print(f"  Last check: {last}")
        
        if files:
            print(f"  Location: {VAULT_DIR / username}")
    else:
        print("\nMonitored users:")
        for user, data in state.items():
            files = list((VAULT_DIR / user).glob("*.md")) if (VAULT_DIR / user).exists() else []
            print(f"  @{user}: {len(files)} files, {len(data.get('seen_ids', []))} tracked")
        if not state:
            print("  (None yet)")


def main():
    parser = argparse.ArgumentParser(
        description='Monitor X users via Nitter RSS',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check for new tweets
  python3 x_nitter_monitor.py --user BoboLucyWisdom
  
  # Show status  
  python3 x_nitter_monitor.py --status --user BoboLucyWisdom
  
  # Cron job (daily at 9am)
  0 9 * * * python3 /Users/dawang/workspace/x_nitter_monitor.py --user BoboLucyWisdom
        """
    )
    
    parser.add_argument('--user', '-u', help='X username to monitor')
    parser.add_argument('--status', '-s', action='store_true', help='Show status')
    
    args = parser.parse_args()
    
    if args.status:
        show_status(args.user)
        return 0
    
    if args.user:
        try:
            return monitor(args.user)
        except KeyboardInterrupt:
            print("\n\nInterrupted.")
            return 0
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main() or 0)
