# Project Summary: Personal Knowledge Base
## "Build A Person's Knowledge Base Shared with the World"

---

## 1. Project Vision

A **federated knowledge base** architecture where:
- **The Person** collects knowledge through automated and manual means
- Knowledge is stored centrally with version control (GitHub)
- **Consumers** (humans or AI agents) obtain the knowledge base and interact with it through their own AI agents

The Person does not host the interaction layer — consumers bring their own AI to the data.

---

## 2. Target Model

**Public Figure / Influencer Model**
- Like Nikita or Naval Ravikant
- Fully public access (anyone can read/clone)
- Continuous updates as The Person generates new content

---

## 3. Content Sources

The Person has multiple data sources:
- Published articles
- Social media posts (Twitter/X)
- YouTube videos
- Personal notes
- And more...

---

## 4. Architecture Overview

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────────┐
│  The Person     │────▶│   GitHub     │────▶│    Consumer     │
│                 │     │  (Central)   │     │   AI Agents     │
├─────────────────┤     ├──────────────┤     ├─────────────────┤
│ • Auto-collect  │     │ • Markdown   │     │ • git clone     │
│ • Manual add    │     │ • Wiki links │     │ • local search  │
│ • GBrain/Hermes │     │ • Versioned  │     │ • voice chat    │
│ • Scheduled commit│   │ • Embeddings │     │ • video chat    │
└─────────────────┘     └──────────────┘     └─────────────────┘
```

---

## 5. Detailed Components

### 5.1 Collector Tool (Personal, Private)

**Input Methods:**
| Type | Method |
|------|--------|
| **Auto-collection** | Social APIs (Twitter/X, YouTube), RSS feeds, web scrapers |
| **Manual inputs** | Web clipper, email-to-KB, Obsidian plugin, mobile app |

**Processing:**
- Normalize to Markdown
- Extract entities
- Generate embeddings
- Suggest wiki links

**Scheduler:**
- Auto-commit to GitHub on schedule OR event-triggered
- Daily recommended frequency

**Implementation:**
- LLM Wiki + Hermes Agent with custom skills
- Minimal configuration via YAML
- Markdown-native, no database required
- **Skill provided:** Pre-built Hermes skill for setting up initial wiki folder structure (`wiki-init`)

---

### 5.2 Central Place (GitHub Public Repository)

**Repository Structure:**
```
person-knowledge-base/
├── people/                    # Person profiles
│   └── example-person.md
├── concepts/                  # Concept explanations
│   └── leverage.md
├── sources/                   # Raw source material
│   └── podcast-interview-2024.md
├── notes/                     # Personal notes
│   └── thought-on-ai.md
├── meta.json                  # Schema definition
├── embeddings/                # Pre-computed vectors
│   └── nomic/
└── README.md                  # Getting started guide
```

**Content Format:**
- Markdown files with YAML frontmatter
- Obsidian-style `[[wikilinks]]` for connectivity
- Frontmatter metadata: `date`, `source`, `tags`, `type`, `author`

**Version Control:**
- Git tags/releases: Weekly curated snapshots (e.g., "v2024.04")
- Nightly `main` branch: Auto-committed raw additions
- Optional: Webhook push notifications for subscribers

---

### 5.3 Consumer Access (Distributed)

| Mode | How It Works |
|------|--------------|
| **Download** | `git clone github.com/person/kb` — Full access to raw data |
| **Direct Search** | Consumer indexes repo locally (LLM Wiki structure, vector DB optional) for semantic search |
| **Work Chat** | Consumer's AI loads repo as RAG context |
| **Voice Chat** | Consumer's agent + Whisper (STT) + Piper (TTS) |
| **Video Chat** | Consumer's agent + WebRTC (LiveKit, Daily.co) |

**No central server required** — consumers own their interaction layer.

---

## 6. Design Decisions

### A. Data Format ✓
- **Single source:** Markdown files
- **Wrapped:** Wiki-style with internal links
- **Priority:** Human readable first, machine parseable second

### B. Update Mechanism ✓
**Hybrid approach:**
1. **Git tags/releases** — Weekly curated snapshots (stable)
2. **Nightly `main` branch** — Auto-committed raw additions (fresh)
3. **Optional webhook** — For real-time push notifications

### C. Personalization Layer ✓
| Feature | Decision |
|---------|----------|
| **Fork** | Yes — Consumers create their own view |
| **Private annotations** | Local only — No changes to public data |
| **Feedback to Person** | Two channels: Public (GitHub Issues) + Private (Encrypted email/Signal) |

### D. Collector Tech ✓
- **Tool:** LLM Wiki + Hermes Agent with custom skills
- **Format:** Markdown files with YAML frontmatter, `[[wikilinks]]` for connectivity
- **Config:** Single YAML file
- **Operation:** Minimal configuration, set-and-forget

---

## 7. Consumer Workflow Example

```bash
# Step 1: Get the knowledge
$ git clone github.com/person/knowledge-base

# Step 2: Browse directly (human-readable markdown)
# Or index for personal use if desired
$ llm-wiki index ./knowledge-base --embed-model nomic

# Step 3: Chat with it (own AI agent)
$ hermes --system-prompt "You have access to this repository..."

# Step 4: Add private annotations (local only)
$ echo "My thought: [[AI]] will change everything" >> ./private-annotations.md
```

---

## 8. Potential Project Names

| Name | Rationale |
|------|-----------|
| **nomadic-kb** | Knowledge that travels with consumers |
| **personal-wiki** | Clear, descriptive, boring |
| **memex-public** | Vannevar Bush's vision, realized |
| **persona-code** | Identity as code |

---

## 9. Next Steps

1. **Finalize project name**
2. **Create prototype repo structure** — Set up initial GitHub repository
3. **Build collector skill** — LLM Wiki/Hermes skill for auto-ingestion and cross-referencing
4. **Test consumer workflow** — Verify end-to-end flow (collect → commit → clone → search → chat)
5. **Document API/schema** — For other developers who want to build on top

---

## 10. Key Principles

1. **Human-readable first** — GitHub repo should be browsable without tools
2. **No lock-in** — Markdown files can move anywhere
3. **Consumer owns the experience** — They choose how to interact
4. **Single source of truth** — GitHub is canonical, forks are derivatives
5. **Minimal maintenance** — Set up once, runs automatically

---

*Generated: April 30, 2026*
*For: Dali Wang / NSAlert*
