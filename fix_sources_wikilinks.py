#!/usr/bin/env python3
"""
Fix Sources sections in concept files to include wikilinks to original raw files.
Can be run standalone (fix existing) or integrated into nightly extraction.
"""

import re
from pathlib import Path
from datetime import datetime

VAULT_PATH = Path("/Users/dawang/BoboLucyWisdom")
CONCEPTS_DIR = VAULT_PATH / "concepts"


def extract_source_posts_from_yaml(content):
    """Extract source_posts list from YAML frontmatter."""
    # Match source_posts: followed by list items
    match = re.search(r'source_posts:\s*\n((?:\s+- .+\n?)+)', content)
    if not match:
        return []
    
    # Extract individual filenames
    sources_text = match.group(1)
    files = re.findall(r'-\s+(.+?)(?:\n|$)', sources_text)
    return [f.strip() for f in files if f.strip()]


def relative_path_to_wikilink(rel_path, md_file):
    """Convert a relative path to Obsidian wikilink format relative to the concept file."""
    # For concept files in /concepts/, raw/ is at ../raw/
    return f"[[../raw/{rel_path}|↩ Original]]"


def fix_sources_section(content, md_file):
    """Add wikilinks to raw files in the Sources section."""
    source_files = extract_source_posts_from_yaml(content)
    if not source_files:
        return content, 0
    
    # Build wikilinks
    wikilinks = []
    for sf in source_files:
        # For x-posts, the link should be raw/x-posts/filename
        if sf.startswith('2026-') or sf.startswith('20'):
            # It's an X post file
            link = f"[[../../../raw/x-posts/{sf}|↩ X Post]]"
        elif 'youtube' in sf.lower() or 'youtu.be' in sf.lower():
            # YouTube transcript
            link = f"[[../../../raw/YouTube-transcript/{sf}|↩ YouTube]]"
        else:
            # Generic raw file
            link = f"[[../../../raw/{sf}|↩ Source]]"
        wikilinks.append(link)
    
    # Find Sources section and update it
    sources_pattern = r'(## Sources\s*\n)(.+?)(?=\n## |\Z|$)'
    
    def replace_sources(match):
        header = match.group(1)
        existing = match.group(2).strip()
        
        # Check if already has wikilinks
        if "[[" in existing:
            return match.group(0)  # Already fixed
        
        # Build new sources content
        new_content = existing + "\n\n### Original Source Files\n\n"
        new_content += "\n".join([f"- {link}" for link in wikilinks])
        new_content += "\n"
        
        return header + new_content
    
    new_content = re.sub(sources_pattern, replace_sources, content, flags=re.DOTALL)
    
    if new_content != content:
        return new_content, len(wikilinks)
    return content, 0


def process_concept_file(md_file):
    """Process a single concept file."""
    content = md_file.read_text()
    
    # Check if has source_posts
    if "source_posts:" not in content:
        return 0
    
    new_content, count = fix_sources_section(content, md_file)
    
    if new_content != content:
        md_file.write_text(new_content)
        print(f"  ✓ Fixed {md_file.name} (+{count} wikilinks)")
        return count
    
    return 0


def main():
    """Fix all concept files."""
    print(f"[{datetime.now().isoformat()}] Fixing Sources sections in concept files...")
    print(f"Concepts directory: {CONCEPTS_DIR}")
    
    if not CONCEPTS_DIR.exists():
        print(f"ERROR: Directory not found: {CONCEPTS_DIR}")
        return
    
    fixed_count = 0
    total_wikilinks = 0
    
    for md_file in sorted(CONCEPTS_DIR.glob("*.md")):
        wikilinks = process_concept_file(md_file)
        if wikilinks > 0:
            fixed_count += 1
            total_wikilinks += wikilinks
    
    print(f"\n=== Summary ===")
    print(f"Files fixed: {fixed_count}")
    print(f"Wikilinks added: {total_wikilinks}")


if __name__ == "__main__":
    main()
