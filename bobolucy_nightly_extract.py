#!/usr/bin/env python3
"""
BoboLucyWisdom Nightly Extraction Script
Processes new content from raw/ directory (X posts, YouTube transcripts, articles)
and updates wiki pages automatically.
"""

import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

# Config
VAULT_PATH = Path("/Users/dawang/BoboLucyWisdom")
RAW_PATH = VAULT_PATH / "raw"
STATE_FILE = Path("~/.config/bobolucy_wiki/state.json").expanduser()
LOG_FILE = Path("~/.config/bobolucy_wiki/nightly.log").expanduser()

def log(msg):
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {msg}"
    print(log_entry)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

def load_state():
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            # Ensure required keys exist
            if "processed_files" not in data:
                data["processed_files"] = {}
            return data
        except json.JSONDecodeError:
            pass
    return {
        "processed_files": {},
        "last_run": None
    }

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))

def get_all_raw_files():
    """Get all files in raw/ directory (x-posts, YouTube-transcript, articles, etc.)"""
    files = []
    
    # Walk through raw/ directory
    if RAW_PATH.exists():
        for path in RAW_PATH.rglob("*.md"):
            # Skip zh versions (process the English one)
            if "/zh/" not in str(path) and not path.name.endswith("-zh.md"):
                files.append(path)
    
    return files

def extract_concepts(content, filepath):
    """Extract concepts from content based on file type."""
    concepts = []
    
    # Health-related terms (Chinese)
    health_terms = {
        "维生素": "vitamin", "维生素D": "vitamin-d", "维生素K2": "vitamin-k2",
        "D3": "vitamin-d", "K2": "vitamin-k2",
        "睾酮": "testosterone-optimization", "DHT": "dht",
        "胰岛素": "insulin-resistance", "生酮": "ketogenic-diet-cancer",
        "冥想": "meditation", "正念": "mindfulness", 
        "睡眠": "sleep", "失眠": "sleep",
        "压力": "rumination-and-stress", "焦虑": "rumination-and-stress",
        "镁": "magnesium", "铁": "iron", "锌": "zinc",
        "果糖": "fructose-metabolic-health",
        "咖啡": "coffee-dementia-prevention",
        "痴呆": "dementia-prevention",
        "禁食": "intermittent-fasting", "断食": "intermittent-fasting",
        "脱发": "hair-loss-reversal",
        "癌症": "ketogenic-diet-cancer",
        "长寿": "longevity", "老化": "longevity",
        "西塔波": "brain-waves-theta", "脑电波": "brain-waves-theta",
        "疲劳": "chronic-fatigue-micronutrients"
    }
    
    for cn, concept in health_terms.items():
        if cn in content:
            concepts.append((cn, concept, "health"))
    
    # Conspiracy/alternative science terms
    alt_terms = {
        "UFO": "foo-fighters", "飞碟": "roswell-incident",
        "罗斯威尔": "roswell-incident", "回形针": "operation-paperclip",
        "特斯拉": "nikola-tesla", "零点能源": "zero-point-energy",
        "标量波": "scalar-waves", "以太": "aether",
        "费城实验": "philadelphia-experiment",
        "自由能源": "free-energy-suppression"
    }
    
    for cn, concept in alt_terms.items():
        if cn in content:
            concepts.append((cn, concept, "alt-science"))
    
    return concepts

def update_stats():
    """Update statistics in index files."""
    concepts = len([f for f in (VAULT_PATH / "concepts").glob("*.md") if f.parent.name == "concepts"])
    concepts_zh = len(list((VAULT_PATH / "concepts/zh").glob("*.md")))
    entities = len(list((VAULT_PATH / "entities/people").glob("*.md")))
    entities_zh = len(list((VAULT_PATH / "entities/people/zh").glob("*.md")))
    
    # Update EN index
    index_en = VAULT_PATH / "index.md"
    if index_en.exists():
        content = index_en.read_text()
        content = re.sub(r'- \*\*Total Pages\*\*: \d+', f'- **Total Pages**: {concepts + entities + 1}', content)
        content = re.sub(r'- \*\*Health Concepts\*\*: \d+', f'- **Health Concepts**: {concepts}', content)
        index_en.write_text(content)
    
    # Update CN index  
    index_zh = VAULT_PATH / "index-zh.md"
    if index_zh.exists():
        content = index_zh.read_text()
        content = re.sub(r'- \*\*总页数\*\*: \d+', f'- **总页数**: {concepts_zh + entities_zh + 1}', content)
        content = re.sub(r'- \*\*健康概念\*\*: \d+', f'- **健康概念**: {concepts_zh}', content)
        index_zh.write_text(content)


def fix_sources_wikilinks_in_file(md_file):
    """Add wikilinks to raw source files in the Sources section."""
    content = md_file.read_text()
    
    # Check if has source_posts
    if "source_posts:" not in content:
        return 0
    
    # Check if already fixed
    if "### Original Source Files" in content:
        return 0
    
    # Extract source_posts from YAML (using regex, no external dependency)
    source_posts = []
    
    # Match source_posts: followed by list items until end of frontmatter
    match = re.search(r'source_posts:\s*\n((?:\s+- .+\n?)+?)(?:^\w|\Z)', content, re.MULTILINE)
    if match:
        sources_text = match.group(1)
        source_posts = re.findall(r'-\s+(.+?)(?:\n|$)', sources_text)
        source_posts = [f.strip() for f in source_posts if f.strip()]
    
    if not source_posts:
        return 0
    
    # Build wikilinks section
    wikilinks = []
    for sf in source_posts:
        if sf.startswith('2026-') or sf.startswith('20'):
            link = f"[[../../../raw/x-posts/{sf}|↩ X Post]]"
        elif 'youtube' in sf.lower() or 'youtu.be' in sf.lower():
            link = f"[[../../../raw/YouTube-transcript/{sf}|↩ YouTube]]"
        else:
            link = f"[[../../../raw/{sf}|↩ Source]]"
        wikilinks.append(link)
    
    # Append to Sources section
    sources_match = re.search(r'(## Sources\s*\n)(.+?)(?=\n## |\Z|$)', content, re.DOTALL)
    if not sources_match:
        return 0
    
    before_sources = content[:sources_match.end(2)]
    after_sources = content[sources_match.end(2):]
    
    new_section = f"\n\n### Original Source Files\n\n"
    new_section += "\n".join([f"- {link}" for link in wikilinks])
    new_section += "\n"
    
    new_content = before_sources + new_section + after_sources
    md_file.write_text(new_content)
    return len(wikilinks)


def fix_all_sources_wikilinks():
    """Fix Sources sections in all concept files."""
    total_fixed = 0
    for md_file in (VAULT_PATH / "concepts").glob("*.md"):
        count = fix_sources_wikilinks_in_file(md_file)
        if count > 0:
            log(f"  Fixed sources in {md_file.name} (+{count} wikilinks)")
            total_fixed += 1
    return total_fixed

def process_file(filepath, state):
    """Process a single raw file and extract concepts."""
    try:
        content = filepath.read_text()
        relative = filepath.relative_to(VAULT_PATH)
        
        log(f"Processing: {relative}")
        
        # Extract concepts
        concepts = extract_concepts(content, filepath)
        if concepts:
            log(f"  Found {len(concepts)} concepts: {[c[0] for c in concepts]}")
        
        # Mark as processed
        file_hash = str(filepath.stat().st_mtime)
        state["processed_files"][str(relative)] = {
            "last_processed": datetime.now().isoformat(),
            "mtime": file_hash,
            "concepts_found": [c[1] for c in concepts]
        }
        
        return len(concepts)
    except Exception as e:
        log(f"  ERROR: {e}")
        return 0

def main():
    log("=" * 60)
    log("BoboLucyWisdom Nightly Extraction Starting")
    log("=" * 60)
    
    state = load_state()
    log(f"Last run: {state.get('last_run', 'Never')}")
    
    # Get all files in raw/
    raw_files = get_all_raw_files()
    log(f"Scanned raw/ directory: {len(raw_files)} files found")
    
    # Process new or modified files
    processed_count = 0
    new_concepts = 0
    
    for filepath in raw_files:
        relative = str(filepath.relative_to(VAULT_PATH))
        file_mtime = str(filepath.stat().st_mtime)
        
        # Check if already processed with same mtime
        if relative in state["processed_files"]:
            if state["processed_files"][relative].get("mtime") == file_mtime:
                continue
        
        # Process the file
        concepts_found = process_file(filepath, state)
        new_concepts += concepts_found
        processed_count += 1
    
    log(f"Processed {processed_count} new/modified files")
    log(f"Found {new_concepts} concept references")
    
    # Update statistics
    update_stats()
    log("Updated index statistics")
    
    # Fix Sources sections wikilinks
    log("Fixing Sources sections wikilinks...")
    fixed_count = fix_all_sources_wikilinks()
    log(f"Fixed {fixed_count} files")
    
    # Save state
    state["last_run"] = datetime.now().isoformat()
    save_state(state)
    
    log("Extraction complete")
    log("")

if __name__ == "__main__":
    main()
