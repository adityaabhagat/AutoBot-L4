# AI Agent Documentation Guide - QPTM Web

## Purpose

This folder contains all AI agent knowledge base documentation for the QPTM Web system. It helps AI agents (Claude Code, GitHub Copilot) investigate WIs, understand business logic, and locate code.

## Quick Start

### Working on a Work Item?

**Use `/investigate <WI#>`** (Claude Code) or **`@workspace /investigate`** (Copilot).

Or manually follow [WORK_ITEM_INVESTIGATION.md](WORK_ITEM_INVESTIGATION.md).

### Need feature documentation?

**Use `/load-process <CODE>`** or find the feature in [QUICK_REFERENCE.md](QUICK_REFERENCE.md).

## Use Cases

These docs support multiple workflows — not just ticket investigation:

| I want to... | Start with... |
|--------------|---------------|
| Understand a feature | `{feature}/domain.md` — business concepts, rules, glossary |
| Find or modify code | `{feature}/architecture.md` — classes, methods, DB schema |
| Investigate a bug/WI | `{feature}/troubleshooting.md` + [WORK_ITEM_INVESTIGATION.md](WORK_ITEM_INVESTIGATION.md) |
| Debug an error message | `{feature}/troubleshooting.md` — search for the error text |
| Learn the full picture | Read all 3 docs for the feature |

## Documentation Structure

```
AI_Agent_Help_Docs/
├── README.md                              # This file
├── QUICK_REFERENCE.md                     # Keyword-to-feature mapping
├── WORK_ITEM_INVESTIGATION.md             # WI investigation workflow
├── capacity-scheduling-allocations/       # CAS - Capacity Scheduling Allocations
│   ├── domain.md                          # Business concepts & rules
│   ├── architecture.md                    # Code structure & implementation
│   └── troubleshooting.md                 # Known issues & solutions
├── nominations/                           # NOM - Nominations
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── allocations/                           # ALLOC - Allocations (PDA)
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── capacity-release/                      # CR - Capacity Release
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── confirmations/                         # CONF - Confirmations
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── contracts/                             # CTR - Contracts
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── rate-management/                       # RATE - Rate Management
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── inventory/                             # INV - Inventory
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── edi-integration/                       # EDI - EDI Integration
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── rfs/                                   # RFS - Request For Service
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── location-management/                   # LOC - Location Management
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── invoice-management/                    # INVC - Invoice Management
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
├── penalties/                             # PEN - Penalties
│   ├── domain.md
│   ├── architecture.md
│   └── troubleshooting.md
└── measurement/                           # MEAS - Measurement
    ├── domain.md
    ├── architecture.md
    └── troubleshooting.md
```

## Each Feature Has 3 Docs

| Doc | Contains | Use When |
|-----|----------|----------|
| `domain.md` | Business concepts, rules, workflows, glossary | Need business context |
| `architecture.md` | Classes, methods, DB schema, algorithms, service deps | Need to find/modify code |
| `troubleshooting.md` | Error messages, diagnostic SQL, RCA patterns, historical WIs | Investigating an issue |

## Investigation Output Format

When investigating a WI, produce:

1. **Issue Summary** - What is broken, for which customer/environment
2. **Root Cause Analysis** - Why it's happening, with specific code/config references
3. **Recommended Resolution** - Specific fix steps with file paths and queries

## Related

- `CLAUDE.md` (repo root) - Auto-loaded routing table for Claude Code
- `.github/copilot-instructions.md` - Auto-loaded instructions for Copilot
- `.claude/skills/` - Claude Code skills (`/investigate`, `/load-process`)
- `.github/prompts/` - Copilot prompt files

---

*Last updated: 2026-03-03*
