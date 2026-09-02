# SKILL: Pending-Customer Follow-Up / Auto-Close Nudge

**Version:** 1.0 | **Created:** 2026-06-10
**Use When:** Drafting the customer-facing follow-up for a case sitting in *Pending Customer* with no response for 7+ days — the "first touch / auto-close warning" message.

Pairs with `SKILL_Queue_Prioritization.md`: the **🟢 Waiting on customer** bucket feeds this skill.

---

## What this skill produces

A short, plain-language note to the customer that:
1. Reminds them the case is waiting on them.
2. Briefly restates what we found / what we're waiting for (no internal jargon).
3. Asks for the **specific** item(s) needed to move forward.
4. Gives the auto-close date (7 business days) and reassures them they can reopen / reference the case.

Default to the **plain/human template (A)**. Use the formal template (B) only if the account clearly prefers it.

---

## Step 1 — Find qualifying cases (SOQL)

```sql
SELECT Id, CaseNumber, Subject, Description, Status,
       CreatedDate, LastModifiedDate, Account.Name,
       Contact.FirstName, Contact.Name, Contact.Email
FROM Case
WHERE Owner.Email = '<consultant-email>'      -- e.g. aditya.bhagat@quorumsoftware.com
  AND Status = 'Pending Customer'
ORDER BY LastModifiedDate ASC
```

A case **qualifies only if the last contact was > 7 days ago.**
- `LastModifiedDate` is the quick proxy — but it changes on *any* edit (internal note, owner change, a status flip). **A case that just moved to Pending Customer is NOT a 7-day nudge — skip it.**
- For accuracy, confirm the real last *outbound* contact:
  ```sql
  SELECT MessageDate, Incoming, Subject FROM EmailMessage
  WHERE ParentId = '<caseId>' ORDER BY MessageDate DESC LIMIT 5
  ```
  ⚠️ The SF MCP connector often returns **0 EmailMessage / CaseComment rows** even when correspondence exists. If so, fall back to the case `Description` and be honest that the "what we found" line is reconstructed, not quoted from the last reply.

---

## Step 2 — Compute the auto-close date (7 business days)

- Start counting from the **next business day** after the send date.
- Exclude **weekends and company holidays.** ⚠️ Watch US federal holidays — **Juneteenth (Jun 19)**, Memorial Day, Independence Day, Labor Day, Thanksgiving, etc.
- Phrase it as **"on or after <Weekday, Month DD, YYYY>"** so a one-day drift isn't a broken promise.
- Always tell the consultant to confirm against Quorum's official SLA/holiday calendar before sending.

---

## Step 3 — Personalize & fill the blanks

| Placeholder | Source |
|-------------|--------|
| First name | `Contact.FirstName` (never send a literal "[First Name]") |
| What we found / are waiting for | last outbound reply if retrievable, else the case `Description` |
| Specific ask(s) | the concrete thing(s) that unblock us — an email address, a log / process-queue ID, a screenshot, a data cut, or confirmation of a proposed change. Keep to **1–3 bullets** |

---

## Template A — Plain / human (preferred)

```
Hi <First Name>,

Thanks for reaching out to Quorum Software Support.

I looked into <one line: the issue + what we found>. <One line: what will fix it / what we need.>

Could you <the specific ask>? As soon as I have that, I'll <next action>.

If I don't hear back, the case will close automatically after 7 business days
(around <Weekday, Mon DD, YYYY>) — no worries though, you can always reopen it
or start a new one referencing <Case #> whenever you're ready.

Thanks,
Aditya Bhagat
Quorum Software Support
```

## Template B — Formal / structured

```
Dear <First Name>,

Thank you for contacting Quorum Software Support.

I have reviewed Case <Case #> – "<Subject>" and <1–2 sentences: investigated / found / did>.

To proceed, I will need the following from you:
  • <Specific item / question 1>
  • <Specific item / question 2>

Please reply at your earliest convenience. Please note that in line with our
support guidelines, this case will be automatically closed after 7 business days
of no response (on or after <Weekday, Mon DD, YYYY>). Should you need to revisit
this, you are always welcome to open a new case referencing <Case #>.

Best regards,
Aditya Bhagat
Quorum Software Support
```

---

## Style rules (customer-facing)

- Plain, friendly, easy to read; short paragraphs; **no internal jargon** — no table names, class names, ADO/bug numbers, repo or environment names.
- **Never** reference other customers or other cases.
- Be honest about status — don't claim a fix is tested or coming if it isn't.
- One clear ask block; don't bury the request in prose.
- The SF connector is **read-only** — always hand back **paste-ready text**; the consultant sends it from the case.

---

## When to use

- User asks: "draft follow-up for my pending-customer cases", "7-day nudge", "auto-close warning", "first touch point", "chase the stale customer cases".
- As the action step for the 🟢 *Waiting on customer* bucket in `SKILL_Queue_Prioritization.md`.
- Flag (don't auto-send) any case with last contact > 14 days as overdue for this nudge.

---

## Worked example — Case 26-01067755 (EQT · QEMAIL → QPEC_SCHEDULER)

- **Found:** QEMAIL finishes with a warning because the QPEC_SCHEDULER account has no email address configured.
- **Fix:** assign an email address to that account (we are updating it, not removing the recipient).
- **Ask:** "What email address would you like assigned to the QPEC_SCHEDULER account?"
- **Auto-close:** sent Wed 2026-06-10 → 7 business days → Fri 2026-06-19 (⚠️ Juneteenth → likely **Mon 2026-06-22**).
- Plain-language send used Template A.
