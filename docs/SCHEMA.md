# BoboLucyWisdom Wiki Schema

## Domain
Health, wellness, neuroscience, nutrition, biohacking, and longevity insights — organizing knowledge from @BoboLucyWisdom's content into a structured wiki.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `intermittent-fasting.md`)
- Every wiki page starts with YAML frontmatter
- Use `[wikilinks](wikilinks.md)` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md`
- Every action must be appended to `log.md`

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary | theme
source_post: [tweet_filename.md]
tags: [from taxonomy below]
---
```

## Tag Taxonomy

### Health Domains
- `sleep` — Sleep optimization, circadian rhythms
- `nutrition` — Diet, supplements, fasting
- `fitness` — Exercise, movement, physical training
- `mental-health` — Brain health, stress, anxiety
- `longevity` — Aging, lifespan, healthspan
- `neuroscience` — Brain science, cognition
- `biochemistry` — Cellular processes, metabolism

### Content Types
- `biohacking` — Self-experimentation, optimization protocols
- `medical-research` — Studies, trials, clinical evidence
- `supplements` — Vitamins, minerals, nootropics
- `lifestyle` — Daily habits, routines, practices
- `diet` — Specific eating patterns (keto, mediterranean, etc.)

### Entities
- `person` — Researchers, doctors, experts mentioned
- `organization` — Universities, labs, companies
- `study` — Specific research papers or trials
- `bio-marker` — Measurable health indicators

### Meta
- `concept` — Core concepts and frameworks
- `comparison` — Side-by-side analyses
- `protocol` — Step-by-step methods
- `myth` — Debunked claims

## Page Thresholds
- **Create a page** when a health topic appears in 2+ posts OR is central to one post
- **Add to existing page** when a post mentions something already covered
- **DON'T create a page** for passing mentions, minor details
- **Split a page** when it exceeds ~200 lines
- **Archive a page** when superseded — move to `_archive/`

## Entity Pages
One page per notable entity. Include:
- Overview / who/what it is
- Key facts, credentials, affiliations
- Relationships to other entities ([wikilinks](wikilinks.md))
- Source references (post links)

## Concept Pages
One page per concept or topic. Include:
- Definition / explanation
- Current state of knowledge
- Evidence quality (studies cited)
- Open questions or debates
- Related concepts ([wikilinks](wikilinks.md))

## Comparison Pages
Side-by-side analyses. Include:
- What is being compared and why
- Dimensions of comparison (table format preferred)
- Evidence-based verdict or synthesis
- Sources

## Protocol Pages
Step-by-step health methods. Include:
- Prerequisites / who it's for
- The protocol (numbered steps)
- Expected outcomes / timeline
- Risks / contraindications
- References

## Update Policy
When new information conflicts with existing content:
1. Check dates — newer sources generally supersede older
2. Note both positions with dates/sources if genuinely contradictory
3. Mark contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in lint report
