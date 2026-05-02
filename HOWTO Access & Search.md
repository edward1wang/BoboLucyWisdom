# BoboLucyWisdom Wiki - HOWTO Access & Search

**Live Site:** https://edward1wang.github.io/BoboLucyWisdom/  
**Source:** https://github.com/edward1wang/BoboLucyWisdom

---

## Part 1: Access the Wiki

### Option 1: Browse Online (Easiest)
Just visit the live site:
```
https://edward1wang.github.io/BoboLucyWisdom/
```

- ✅ Search works instantly
- ✅ No install needed
- ✅ Works on phone/tablet
- ✅ Offline after page load (PWA)

---

### Option 2: Run Local Server (Offline, Editable)

```bash
# Clone the repo
git clone https://github.com/edward1wang/BoboLucyWisdom.git

# Install requirements
pip install mkdocs mkdocs-material

# Run local server
cd BoboLucyWisdom
mkdocs serve

# Open http://127.0.0.1:8000 in browser
```

**Requirements:** Python 3.9+ with pip

---

### Option 3: Read Raw Markdown (Obsidian, VS Code, etc.)

```bash
# Clone the repo
git clone https://github.com/edward1wang/BoboLucyWisdom.git

# Open docs folder in your favorite editor
cd BoboLucyWisdom/docs
# Drag folder to Obsidian, VS Code, Typora, etc.
```

**Best for:** Personal note-taking, editing, offline access

---

## Part 2: AI-Powered Search

### Option A: AI-Enabled Editor (Recommended)

Open `BoboLucyWisdom/` folder in:
- **Cursor** (cursor.sh)
- **Claude Code** (Claude desktop)
- **GitHub Copilot** (VS Code extension)

**Ask naturally:**
```
"Find all vitamin D concepts"
"Summarize meditation practices in Chinese"
"Cross-reference Tesla with scalar waves"
```

**How it works:** AI reads markdown files directly from disk.

---

### Option B: Local LLM + RAG (Privacy-First)

**Ollama setup:**
```bash
# Install Ollama
brew install ollama

# Pull embedding model
ollama pull nomic-embed-text

# Start server
ollama serve
```

**Then use a RAG tool:**
- AnythingLLM
- Obsidian + Smart Connections plugin
- PrivateGPT

**How it works:** Embeddings created from `docs/` folder, queried locally.

---

### Option C: Hermes AI Agent

**Setup:**
```bash
# Install Hermes CLI
pip install hermes-cli

# Clone wiki
git clone https://github.com/edward1wang/BoboLucyWisdom.git

# Start Hermes from wiki folder
cd BoboLucyWisdom
hermes
```

**Search examples:**
```
[Workspace: ~/BoboLucyWisdom]
> Find concepts about insulin resistance
> Compare English and Chinese meditation pages  
> What do we know about Nikola Tesla?
> Search raw transcripts for cold fusion
```

**How it works:** Hermes CLI provides AI with file tools to read/search the wiki.

---

### Option D: Cloud AI Upload

```bash
# Create archive
cd BoboLucyWisdom/docs
zip -r wiki.zip .

# Upload to cloud AI:
# - Claude (claude.ai)
# - ChatGPT (chat.openai.com)
# - Perplexity (perplexity.ai)

# Then ask:
"Search this knowledge base for longevity topics"
"Find all Chinese content about meditation"
```

**Note:** Sends content to external API. Don't use for sensitive data.

---

## Quick Comparison

| Method | Setup | Offline | AI Search | Privacy | Best For |
|--------|-------|---------|-----------|---------|----------|
| Online | None | ✓ (after load) | Limited | High | Quick browsing |
| Local server | pip install | ✓ | No | High | Development/preview |
| Raw markdown | git clone | ✓ | Manual | High | Editing/ownership |
| AI Editor | Install app | ✓ | Native | Medium | Daily use |
| Local LLM | Setup Ollama | ✓ | ✓ | Very High | Privacy-critical |
| Hermes | pip install | ✓ | ✓ | High | Technical users |
| Cloud AI | Upload | ✗ | ✓ | Low | Quick analysis |

---

## Wiki Structure Reference

```
BoboLucyWisdom/
├── docs/
│   ├── concepts/           # Health & science concepts (EN + CN)
│   ├── entities/           # People & organizations
│   └── raw/                # Transcripts, articles, posts
└── mkdocs.yml             # Site configuration
```

**Total:** ~181 markdown pages, bilingual (EN/CN)

---

## Update Workflow

**If you fork this repo and want to update:**

```bash
# Pull latest changes
git pull origin main

# If running local server, restart:
mkdocs serve
```

---

*Last updated: 2026-05-02*