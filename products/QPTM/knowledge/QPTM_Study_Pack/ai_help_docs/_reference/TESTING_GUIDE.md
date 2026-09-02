# AI Documentation Testing Guide

A guide for developers to verify that the AI documentation infrastructure is working correctly in both repos (Web and Batch). Share this with your team so everyone can validate the setup.

---

## Test 1: `/load-process` Skill (Claude Code)

Tests that Claude can load feature documentation on demand.

**In Web repo:**
```
/load-process nominations
```
- Expected: Claude reads `AI_Agent_Help_Docs/nominations/domain.md`, `architecture.md`, `troubleshooting.md`
- Verify: Claude provides a summary of nominations feature

**In Batch repo:**
```
/load-process NNNOMLOAD
```
- Expected: Claude reads `AI_Agent_Help_Docs/nom-load/domain.md`, `architecture.md`, `troubleshooting.md`
- Verify: Claude provides a summary of the Nom Load sub-process

**Also try:** `/load-process autogen`, `/load-process CANOMCLTG`, `/load-process fuel ptr split`

---

## Test 2: `/investigate` Skill (Claude Code)

Tests that Claude can investigate a Work Item with full documentation context.

```
/investigate 1777320
```
- Expected: Claude retrieves WI from Azure DevOps, identifies the feature area, loads relevant docs, and provides structured analysis
- Verify: Output includes Issue Summary, Root Cause Analysis, and Recommended Resolution grounded in actual documentation

**Note:** Requires Azure DevOps MCP server to be configured and accessible.

---

## Test 3: Feature Questions Without WI Number

Tests that Claude auto-loads documentation when you ask about a feature (not just for WI investigation).

**Try these prompts:**
- "How does nomination classification work?"
- "What tables are involved in capacity release?"
- "Explain the scheduling reduction algorithm"
- "How do confirmations work in QPTM?"

**Expected behavior:**
- Claude should automatically load the relevant feature's documentation (triggered by `.claude/rules/doc-loading.md`)
- Answer should reference specific classes, methods, tables from the architecture docs
- Should NOT just give generic answers — should be grounded in project documentation

---

## Test 4: Copilot Prompt Files (GitHub Copilot)

Tests that GitHub Copilot can use the prompt files for structured workflows.

**In VS Code with Copilot Chat:**
```
@workspace /load-process NNLFAGN
```
- Expected: Copilot reads the 3 docs for AutoGen Load Following and summarizes

```
@workspace /investigate 1777320
```
- Expected: Copilot follows the investigation workflow from `.github/prompts/investigate.prompt.md`

**Note:** Copilot prompt files (`.github/prompts/*.prompt.md`) require GitHub Copilot Chat in VS Code.

---

## Test 5: Routing Table Auto-Loading

Tests that CLAUDE.md / copilot-instructions.md routing tables help AI find the right docs.

**Try ambiguous questions:**
- "There's a bug in how we calculate overrun charges" → Should route to `greater-of-overrun/` (Batch) or `invoicing/` (Web)
- "EDI noms are failing" → Should route to `edi-integration/` (Batch)
- "Rate detail screen is slow" → Should route to `rate-management/` (Web)
- "Imbalance numbers look wrong" → Should route to `monthly-cumulative-imbalance/` or `daily-contract-overrun/` (Batch)

**Expected:** Claude identifies the correct feature from the routing table and loads the right docs before answering.

---

## Test 6: Cross-Repo Awareness

Tests that AI understands when to look across repos.

**In Web repo, ask:**
- "What batch processes does the nominations screen trigger?"
- Expected: Claude mentions NNNOMLOAD, CANOMCLTG, etc. and references Batch repo docs

**In Batch repo, ask:**
- "What Web service does Nom Load call?"
- Expected: Claude references Web repo nomination services

---

## File Inventory Checklist

### Both Repos Should Have:

| File | Purpose | Check |
|------|---------|-------|
| `CLAUDE.md` | Auto-loaded routing table + coding rules | [ ] |
| `.github/copilot-instructions.md` | Auto-loaded routing table + coding rules | [ ] |
| `.claude/rules/doc-loading.md` | Auto-trigger doc loading | [ ] |
| `.claude/rules/wi-investigation.md` | Auto-trigger WI investigation | [ ] |
| `.claude/skills/load-process/SKILL.md` | `/load-process` skill | [ ] |
| `.claude/skills/investigate/SKILL.md` | `/investigate` skill | [ ] |
| `.github/prompts/load-process.prompt.md` | Copilot load-process prompt | [ ] |
| `.github/prompts/investigate.prompt.md` | Copilot investigate prompt | [ ] |
| `AI_Agent_Help_Docs/README.md` | Navigation guide | [ ] |
| `AI_Agent_Help_Docs/QUICK_REFERENCE.md` | Keyword-to-feature mapping | [ ] |
| `AI_Agent_Help_Docs/DOCUMENTATION_STRATEGY.md` | Authoring guidelines | [ ] |
| `AI_Agent_Help_Docs/WORK_ITEM_INVESTIGATION.md` | Legacy reference (deprecated) | [ ] |

### Feature Documentation:

**Web repo** — 14 features, 42 docs:
- [ ] `AI_Agent_Help_Docs/{feature}/domain.md` exists for all 14 features
- [ ] `AI_Agent_Help_Docs/{feature}/architecture.md` exists for all 14 features
- [ ] `AI_Agent_Help_Docs/{feature}/troubleshooting.md` exists for all 14 features

**Batch repo** — 34 sub-processes, 102 docs:
- [ ] `AI_Agent_Help_Docs/{feature}/domain.md` exists for all 34 features
- [ ] `AI_Agent_Help_Docs/{feature}/architecture.md` exists for all 34 features
- [ ] `AI_Agent_Help_Docs/{feature}/troubleshooting.md` exists for all 34 features

### Quick Verification Commands (run in repo root):

```bash
# Count feature folders
ls -d AI_Agent_Help_Docs/*/  | wc -l

# Count total doc files (should be 42 for Web, 102 for Batch)
find AI_Agent_Help_Docs -name "*.md" -path "*/*/domain.md" -o -name "*.md" -path "*/*/architecture.md" -o -name "*.md" -path "*/*/troubleshooting.md" | wc -l

# Verify all 3 docs exist per feature
for dir in AI_Agent_Help_Docs/*/; do
  for f in domain.md architecture.md troubleshooting.md; do
    [ ! -f "$dir$f" ] && echo "MISSING: $dir$f"
  done
done
```

---

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Claude doesn't load docs automatically | `doc-loading.md` rule not triggering | Check `.claude/rules/doc-loading.md` exists and has correct triggers |
| `/load-process` doesn't work | Skill not found | Check `.claude/skills/load-process/SKILL.md` exists |
| `/investigate` returns generic analysis | Docs not loaded | Verify `QUICK_REFERENCE.md` maps keywords to correct feature folders |
| Copilot prompts not available | Prompt files missing | Check `.github/prompts/*.prompt.md` exist |
| Azure DevOps WI fetch fails | MCP server not configured | Ensure `azure-devops` MCP server is configured in Claude Code settings |

---

*Last updated: 2026-03-03*
