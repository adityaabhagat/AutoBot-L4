# AI Documentation Strategy

## Purpose

This document defines the strategy and guidelines for maintaining AI agent documentation across the QPTM codebase. This ensures AI agents (Claude Code, GitHub Copilot) can effectively assist developers in understanding features, resolving tickets, implementing changes, and troubleshooting issues.

---

## Documentation Principles

### 1. Primary Functionality = Primary Documentation

Documentation resides in the repository where the primary functionality is implemented.

- **Batch processes** → Documented in `Quorum.QPTM.Batch/AI_Agent_Help_Docs/`
  - Even if the batch process calls Web services — include cross-references
- **Web screens/APIs** → Documented in `Quorum.QPTM.Web/AI_Agent_Help_Docs/`
  - Even if they trigger batch processes — include cross-references

### 2. Feature-First Layout

Each feature/sub-process has its own folder with 3 docs:

```
AI_Agent_Help_Docs/
├── README.md                  # Navigation guide
├── QUICK_REFERENCE.md         # Keyword-to-feature mapping
├── DOCUMENTATION_STRATEGY.md  # This file
├── {feature}/                 # One folder per feature
│   ├── domain.md              # WHAT — Business concepts, rules, workflows
│   ├── architecture.md        # HOW — Classes, methods, DB schema, algorithms
│   └── troubleshooting.md     # FIX — Errors, diagnostic SQL, historical WIs
└── ... (more feature folders)
```

### 3. AI Tool Infrastructure

Each repo also has tool-specific files that reference the docs:

| File | Tool | Purpose |
|------|------|---------|
| `CLAUDE.md` | Claude Code | Auto-loaded routing table + coding rules |
| `.github/copilot-instructions.md` | GitHub Copilot | Auto-loaded routing table + coding rules |
| `.claude/rules/*.md` | Claude Code | Auto-loaded behavior rules |
| `.claude/skills/*/SKILL.md` | Claude Code | `/investigate`, `/load-process` skills |
| `.github/prompts/*.prompt.md` | GitHub Copilot | Reusable prompt files |

---

## Three-Doc Pattern

### domain.md — Business Concepts (WHAT)

Help AI understand business rules, processes, and domain terminology.

**Content:**
- Core business concepts and terminology
- Business rules and validation logic
- Domain workflows and processes
- Relationships between business entities
- Industry-specific concepts (gas days, nominations, scheduling cycles)

### architecture.md — Technical Implementation (HOW)

Help AI understand system design, code structure, and implementation details.

**Content:**
- Key classes, methods, and their responsibilities
- Data models and database schemas (table names, key columns)
- Integration points and service dependencies
- Algorithm implementations
- Performance considerations
- File paths and project structure

### troubleshooting.md — Issues & Solutions (FIX)

Help AI quickly resolve known issues and common problems.

**Content:**
- Common error messages and their causes
- Diagnostic SQL queries
- Known issues and workarounds
- Root cause analysis patterns
- Historical Work Items: past tickets with WI#, description, resolution, PR reference
- Recurring problems and their fixes

---

## Documentation Standards

### File Naming Convention
- Feature folders: lowercase with hyphens (`nominations/`, `capacity-release/`, `rate-management/`)
- Inside each folder: always `domain.md`, `architecture.md`, `troubleshooting.md`
- Consistent naming across repos

### Document Structure

Each document should include:

```markdown
---
title: [Feature Name] - [Domain|Architecture|Troubleshooting]
keywords: [keyword1, keyword2, keyword3]
last_updated: [YYYY-MM-DD]
---

# [Title]

## Overview
Brief description of what this document covers

## [Relevant Sections]
Content organized logically

## Related Documentation
- Links to related docs in this repo
- Links to related docs in other repos
```

### Cross-Repository References

**In Web repo (referencing Batch):**
```markdown
## Batch Process Integration
This feature triggers:
- Nomination Classification (CANOMCLTG) — See Batch repo: `AI_Agent_Help_Docs/nomination-classification-transaction-grouping/domain.md`
```

**In Batch repo (referencing Web):**
```markdown
## Web Service Dependencies
This batch process calls:
- `NominationService.SubmitNomination()` — See Web repo: `AI_Agent_Help_Docs/nominations/architecture.md`
```

---

## When to Document

Document when:
- Implementing a significant new feature
- Resolving a complex customer issue (add to troubleshooting.md with WI#)
- Understanding domain logic through code analysis
- Discovering undocumented business rules
- Creating reusable solutions to common problems

## Workflow for Adding New Documentation

1. **Determine primary repo** — Where is the main functionality?
2. **Create feature folder** — `AI_Agent_Help_Docs/{feature-name}/`
3. **Write all 3 docs** — domain.md, architecture.md, troubleshooting.md
4. **Add cross-references** — Link to related features in same/other repos
5. **Update QUICK_REFERENCE.md** — Add feature to the routing table with keywords
6. **Update CLAUDE.md + copilot-instructions.md** — Add to routing table

## Capturing Historical Work Items

When fixing a bug, add to the feature's `troubleshooting.md`:

```markdown
## Historical Work Items

### WI #12345 — [Brief description]
- **Customer**: [Name] | **Environment**: [PRD/UAT]
- **Symptom**: [What was observed]
- **Root Cause**: [Why it happened]
- **Resolution**: [What was fixed]
- **PR**: [PR link or number]
```

This creates a searchable knowledge base of real issues that AI agents can reference.

---

## Content Quality Guidelines

**DO:**
- Include actual class names, method names, file paths
- Explain WHY things work the way they do (business reasons)
- Include diagnostic SQL queries in troubleshooting docs
- Document workarounds and known limitations
- Include customer scenarios and use cases

**DON'T:**
- Duplicate code that changes frequently
- Write generic descriptions without specifics
- Assume AI knows your domain terminology
- Load all documentation at once — use QUICK_REFERENCE for routing

---

## Maintenance

- **After bug fixes**: Add to troubleshooting.md with WI# and resolution
- **After major releases**: Review and update architecture docs
- **When business rules change**: Update domain docs
- **When patterns change**: Update relevant docs

When functionality is removed:
1. Mark document as deprecated with date
2. Explain what replaced it
3. Keep for historical reference, then remove when no longer relevant

---

*Last updated: 2026-03-03*
