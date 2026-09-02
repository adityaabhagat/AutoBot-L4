# SKILL: L4 Case Queue Prioritization

**Version:** 1.0 | **Created:** 2026-05-27
**Use When:** Daily queue triage, "what should I work on next", scheduled queue digest, SLO review

---

## SLO Reference (Quorum Support — working assumption)

| Priority | First response | Resolution target | Stale threshold (no update) |
|----------|----------------|-------------------|------------------------------|
| **High / P1** | 4 hours | 5 business days | >5 days = stale, >14 days = breach |
| **Medium / P2** | 1 business day | 10 business days | >10 days = stale, >21 days = breach |
| **Low / P3** | 2 business days | 20+ business days | >20 days = stale |

*Adjust to actual Quorum support contractual SLOs when confirmed.*

---

## Prioritization Framework

Rank each open case on four axes, then bucket:

### Axis 1 — Priority (weight: highest)
- `High` → P1
- `Medium` → P2
- `Low` → P3

### Axis 2 — Action owner (who is blocked)
Derived from `Status`:
- **On Quorum (us):** `In Progress`, `Pending Quorum`, `In Review`, `New`
- **On Engineering:** `In Development Queue`, `In Dev`, `In UAT`
- **On Customer:** `Pending Customer`, `Waiting on Customer`
- **Closed/terminal:** `Closed`, `Closed - No Response`, `Resolved`

### Axis 3 — Staleness (days since `LastModifiedDate`)
Compare against the priority's stale threshold above. Stale items on us = top of queue.

### Axis 4 — Age (days since `CreatedDate`)
Tiebreaker. Older cases erode CSAT — surface anything >90 days regardless of recent activity.

---

## Bucket Output

Produce 4 buckets, in this order:

### 🔴 Act today
- **P1 + on Quorum + stale (>5d since update)** — these are SLO breaches sitting on us
- Any P1 escalated (`IsEscalated = true`)
- Any case >180 days old regardless of priority (CSAT risk)

### 🟡 This week
- P1 + on Quorum + fresh updates (recent client activity)
- P1 + on Engineering (verify dev status, push for release date)
- P2 + on Quorum + stale (>10d)

### 🟢 Waiting on customer
- All `Pending Customer` cases
- Flag with "nudge if >14d silence" if last update > 14 days

### 🔵 Standard cadence
- P2/P3 with recent activity, not stale

---

## SOQL Query

```sql
SELECT Id, CaseNumber, Subject, Status, Priority,
       CreatedDate, LastModifiedDate, Account.Name, IsEscalated
FROM Case
WHERE Owner.Email = '<consultant-email>'
  AND Status NOT IN ('Closed','Closed - No Response','Resolved')
ORDER BY Priority ASC, CreatedDate ASC
```

---

## Computing the Buckets (pseudo-logic)

```
for each case:
    age_days        = today - CreatedDate
    stale_days      = today - LastModifiedDate
    action_owner    = map(Status)   # us | eng | customer
    sla_stale       = priority threshold lookup

    if action_owner == 'customer':
        bucket = 'waiting'  (flag if stale_days > 14)
    elif priority == 'High' and action_owner == 'us' and stale_days > 5:
        bucket = 'today'    (SLO breach)
    elif age_days > 180:
        bucket = 'today'    (CSAT risk regardless)
    elif IsEscalated:
        bucket = 'today'
    elif priority == 'High':
        bucket = 'this_week'
    elif priority == 'Medium' and stale_days > 10:
        bucket = 'this_week'
    else:
        bucket = 'standard'
```

---

## Output Format (markdown table per bucket)

```
| # | Case (link) | Account | Status | Age | Days since update | Why now |
```

`Why now` should be a 5-10 word reason: "SLO breached", "Fix in UAT — confirm deploy", "Same theme as case X — investigate together", "Stale — nudge customer", etc.

---

## Cluster Detection (bonus)

When two or more cases share **the same account AND a related theme** (e.g., both mention "Service Points", both EDI on same TSP, both AUTOCONF), group them in the recommendation. Investigating clustered issues together is much faster than handling them serially.

Theme detection heuristics:
- Same `Account.Name`
- Subject keyword overlap (use 3+ shared significant words, excluding stopwords like "error", "issue", "QPTM")
- Same module hint (EDI / nomination / report / invoice / contract / scheduling / confirmation)

---

## When to Use This Skill

- User asks: "what should I work on?", "prioritize my queue", "any SLO breaches?"
- Daily routine: include this prioritization in the morning queue digest
- After investigating one case: use the cluster-detection step to suggest the next related case
- SLO/CSAT reviews

---

*Pairs with the L4 Case Watch scheduled routines (6PM/11:30PM IST). The watch routines act on *new client activity*; this skill answers "what should I push on proactively".*
