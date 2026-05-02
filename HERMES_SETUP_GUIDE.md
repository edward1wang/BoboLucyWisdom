# Hermes AI Setup Guide for BoboLucyWisdom Wiki

This guide shows how to set up Hermes AI Agent to browse, search, and interact with the BoboLucyWisdom wiki locally.

---

## Prerequisites

- macOS, Linux, or Windows with WSL
- Python 3.11+ installed
- Git installed
- Terminal/CLI access

---

## Step 1: Install Hermes CLI

### macOS (using Homebrew)
```bash
brew tap hermes-cli/tap
brew install hermes
```

### Or using pip
```bash
pip install hermes-cli
```

### Verify installation
```bash
hermes --version
```

---

## Step 2: Clone the Wiki Repository

```bash
git clone https://github.com/NSAlert/BoboLucyWisdom.git

# Optional: Clone to specific location
git clone https://github.com/NSAlert/BoboLucyWisdom.git ~/Documents/BoboLucyWisdom
```

---

## Step 3: Configure Workspace

### Option A: Set as default workspace
```bash
# Navigate to the cloned repo
cd BoboLucyWisdom

# Set as Hermes workspace (creates .hermes/ folder)
hermes init
```

### Option B: Use without init
```bash
# Start Hermes from the repo directory
cd BoboLucyWisdom
hermes
```

Hermes automatically detects the current directory as workspace.

---

## Step 4: Start Hermes

```bash
hermes
```

You'll see the Hermes prompt:
```
[Workspace: /path/to/BoboLucyWisdom]
>
```

---

## Step 5: Use AI to Search the Wiki

### Example commands:

**Search for concepts:**
```
> Find all concepts about vitamin D
```

**Browse bilingual content:**
```
> Show me the Chinese version of meditation concepts
```

**Cross-reference entities:**
```
> What do we know about Nikola Tesla?
```

**Read raw transcripts:**
```
> Find YouTube transcripts about cold fusion
```

**Summarize:**
```
> Summarize the longevity concepts in the wiki
```

---

## Step 6: Working with the Wiki Structure

The wiki is organized as:

```
BoboLucyWisdom/
├── docs/
│   ├── concepts/
│   │   ├── vitamin-d.md              # English
│   │   ├── zh/vitamin-d.md           # Chinese
│   │   ├── meditation.md
│   │   └── ...
│   ├── entities/
│   │   ├── people/
│   │   │   ├── nikola-tesla.md
│   │   │   └── zh/nikola-tesla.md
│   │   └── organizations/
│   └── raw/
│       ├── YouTube-transcript/
│       ├── articles/
│       └── x-posts/
```

---

## Tips for Best Results

### 1. Use file operations
```
> Read docs/concepts/vitamin-d.md
> Search files for "longevity"
> List files in docs/raw/YouTube-transcript/
```

### 2. Combine with web search
```
> Search the wiki for "intermittent fasting" then search web for latest research
```

### 3. Cross-reference
```
> Find all links to Otto Warburg in the concepts folder
```

### 4. Bilingual queries
```
> Compare English and Chinese versions of the meditation page
```

---

## Troubleshooting

### Hermes not finding files
```bash
# Check current workspace
hermes config get workspace

# Or explicitly set it
hermes config set workspace /full/path/to/BoboLucyWisdom
```

### Permission denied
```bash
chmod +x /path/to/hermes
```

### Clone fails
```bash
# Use SSH instead of HTTPS
git clone git@github.com:edward1wang/BoboLucyWisdom.git
```

---

## Alternative: MkDocs Local Server

If you want the web interface locally:

```bash
# Install MkDocs
pip install mkdocs mkdocs-material

# Serve locally
cd BoboLucyWisdom
mkdocs serve

# Opens at http://127.0.0.1:8000
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Clone wiki | `git clone https://github.com/NSAlert/BoboLucyWisdom.git` |
| Start Hermes | `hermes` |
| Set workspace | `hermes init` |
| Search files | `search_files pattern="vitamin" target="content"` |
| Read file | `read_file path="docs/concepts/vitamin-d.md"` |
| List directory | `terminal command="ls docs/concepts"` |

---

## Links

- Live site: https://edward1wang.github.io/BoboLucyWisdom/
- Source: https://github.com/edward1wang/BoboLucyWisdom
- Hermes docs: https://hermes-agent.nousresearch.com/

---

*Last updated: 2026-05-02*