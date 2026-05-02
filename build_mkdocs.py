#!/usr/bin/env python3
"""
Build script to convert BoboLucyWisdom Obsidian vault to MkDocs site
Handles: wikilink conversion, bilingual nav, directory structure preservation
"""

import os
import re
import shutil
from pathlib import Path

VAULT_PATH = Path.home() / "BoboLucyWisdom"
DOCS_PATH = Path.home() / "workspace" / "docs"
WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|([^\]]+))?\]\]')

def wikilink_converter(match):
    """Convert [[page|alias]] -> [alias](path/page.md)"""
    page = match.group(1).strip()
    alias = match.group(2).strip() if match.group(2) else page
    
    # Handle subdirectory references like "concepts/zh/维生素"
    if '/' in page or '\\' in page:
        return f"[{alias}]({page}.md)"
    
    # Simple page name - will be relative
    return f"[{alias}]({page}.md)"

def process_markdown(src_path, dest_path):
    """Copy markdown file and convert wikilinks"""
    content = src_path.read_text(encoding='utf-8')
    
    # Convert wikilinks to standard markdown links
    content = WIKILINK_PATTERN.sub(wikilink_converter, content)
    
    # Ensure destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write converted content
    dest_path.write_text(content, encoding='utf-8')
    print(f"  Processed: {src_path.relative_to(VAULT_PATH)} -> {dest_path.relative_to(DOCS_PATH)}")

def build_docs():
    """Build the docs/ directory from Obsidian vault"""
    print(f"Building docs from: {VAULT_PATH}")
    
    # Clean/create docs directory
    if DOCS_PATH.exists():
        shutil.rmtree(DOCS_PATH)
    DOCS_PATH.mkdir(parents=True)
    
    # Copy markdown files and convert wikilinks
    md_count = 0
    for md_file in VAULT_PATH.rglob("*.md"):
        # Skip template files
        if "templates/" in str(md_file):
            continue
        
        # Calculate destination path
        rel_path = md_file.relative_to(VAULT_PATH)
        dest_file = DOCS_PATH / rel_path
        
        process_markdown(md_file, dest_file)
        md_count += 1
    
    # Copy assets (images, etc.)
    asset_count = 0
    for suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.pdf']:
        for asset_file in VAULT_PATH.rglob(f"*{suffix}"):
            if "templates/" in str(asset_file):
                continue
            rel_path = asset_file.relative_to(VAULT_PATH)
            dest_file = DOCS_PATH / rel_path
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(asset_file, dest_file)
            asset_count += 1
    
    # Create README files for directories without index.md
    ensure_indexes()
    
    print(f"\n✅ Built successfully:")
    print(f"   {md_count} markdown files processed")
    print(f"   {asset_count} assets copied")
    print(f"   Output: {DOCS_PATH}")

def ensure_indexes():
    """Create index.md for directories missing one"""
    for dir_path in DOCS_PATH.rglob("*"):
        if dir_path.is_dir():
            index_file = dir_path / "README.md"
            if not index_file.exists():
                readme_content = f"# {dir_path.name}\n\nDirectory contents.\n"
                index_file.write_text(readme_content, encoding='utf-8')

def serve():
    """Run mkdocs serve"""
    os.system("cd ~/workspace && mkdocs serve")

def build():
    """Run mkdocs build"""
    os.system("cd ~/workspace && mkdocs build")

if __name__ == "__main__":
    import sys
    cmd = sys.argv[1] if len(sys.argv) > 1 else "build"
    
    if cmd == "serve":
        build_docs()
        serve()
    elif cmd == "build":
        build_docs()
        build()
    else:
        build_docs()
