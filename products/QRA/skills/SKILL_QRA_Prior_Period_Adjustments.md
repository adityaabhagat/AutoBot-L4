# SKILL: QRA Prior Period Adjustments (PPA / PPN) Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-06-14 | **Product:** QRA (My Quorum Revenue Accounting — upstream oil-&-gas revenue distribution / owner accounting)
**Scope:** The **Prior Period Adjustment** pipeline — how QRA reverses already-distributed revenue and re-books it to corrected owners/decimals/tiers. Covers **PPN** (Prior Period Notification — the row that flags "this prior month needs adjusting") generation in **SP025 / VL031 / VL40**, **PPN processing** through **VL100 → JE100** (valuation, distribution, posting/clean), **reverse / rebook** tracking, **recoup** PPNs, **DRI** (Direct Revenue Interest) tier changes, **impairment** reason codes (301/302/305/310/311/314), **MEG / Market Group** PPNs, **tax / severance / SOD** PPAs, and PPA **performance / timeouts**.
**Companion skills (to be built):** owner suspense / check-write → SKILL_QRA_Suspense_CheckWrite; DOI / decimal-interest master setup → SKILL_QRA_DOI_Ownership; valuation (non-PPA) → SKILL_QRA_Revenue_Valuation; severance/production-tax engine → SKILL_QRA_Severance_Tax. **PPA is downstream of DOI ownership + valuation** — when the *number* is wrong (not the process crashing), verify the underlying DOI decimals, tier/DRI-link setup, and the original valuation run first; the PPA is usually faithfully reversing/rebooking whatever the original deck said.

> **Evidence base:** 563 closed QRA Prior-Period-Adjustment cases. Root-cause split: **Software Defect 131**, (blank) 135, Customer Error 70, Training 29, Customer Cancelled 28, **Application Configuration 25**, Performance 21, Other 16, Hardware/SW Change 14, DB Refresh 14, … **ChangeConfig 2**. This skill mines the **158 actionable** cases (Software Defect 131 + Application Configuration 25 + ChangeConfig 2) for fix recipes, plus ~35 Training/Customer-Error cases for the Expected-Behavior FAQ. Every root-cause claim cites a real SF case number and/or ADO work item observed during mining. Where a cluster's resolution could not be confirmed from the mined cases it is flagged "resolution pattern unclear from mined cases."

---

## TABLE OF CONTENTS

1. [Quick Triage Table](#1-quick-triage-table)
2. [Pipeline & Concepts](#2-pipeline--concepts)
3. [Decision Tree](#3-decision-tree)
4. [Cluster A — Impairment reason codes 301/302/305/310/311/314 (HIGH FREQUENCY)](#4-cluster-a--impairment-reason-codes)
5. [Cluster B — Reverse / Rebook not tying (missing reversal source rows)](#5-cluster-b--reverse--rebook-not-tying)
6. [Cluster C — Recoup PPNs (not recouping / perpetual recoup / WI-transfer)](#6-cluster-c--recoup-ppns)
7. [Cluster D — DRI tier change PPNs not reversing/rebooking](#7-cluster-d--dri-tier-change-ppns)
8. [Cluster E — BKRVNU / RONL_MI_STAT RRID-not-updated (PPN selection)](#8-cluster-e--bkrvnu--ronl_mi_stat)
9. [Cluster F — MEG / Market Group PPN failures](#9-cluster-f--meg--market-group-ppn-failures)
10. [Cluster G — SP025 / VL40 over-generating PPNs (pay-code, product, DRI links)](#10-cluster-g--sp025--vl40-over-generating-ppns)
11. [Cluster H — JE100 won't clean / SQL errors posting](#11-cluster-h--je100-wont-clean--sql-errors-posting)
12. [Cluster I — Tolerant-decimal & rounding on PPNs](#12-cluster-i--tolerant-decimal--rounding)
13. [Cluster J — PPA performance / timeouts / out-of-memory](#13-cluster-j--ppa-performance--timeouts)
14. [Cluster K — SOD / tax PPA volume & amount errors](#14-cluster-k--sod--tax-ppa)
15. [Known ADO Items](#15-known-ado-items)
16. [Diagnostic SQL](#16-diagnostic-sql)
17. [Expected-Behavior / User-Education FAQ](#17-expected-behavior--user-education-faq)
18. [Key Code, Config Keys & Repos](#18-key-code-config-keys--repos)
19. [Escalation Guidance](#19-escalation-guidance)

---

## 1. Quick Triage Table

| Symptom (what the user reports) | Likely cause | First check |
|---|---|---|
| PPN fails in VL100/JE100 with **"Impaired reason code = 302 … remaining amount is not zero"** | Tolerant-decimal floor too tight **OR** Market Group / RRV deck not in Completed status | §4 / §12 — check **MG004/MG005/MG006** status first; if all Completed, raise `DISTRIBUTION.TOLERANTDEC` (26-01079330) |
| **301 Impairment** "No owner records found" / "Missing RRV Record" | Missing owner row on the historical RRV deck (often after an owner transfer) | §4 — fix the missing row in `RTRN_VL_RVSL_SRC` / RRV deck (24-00994919) |
| **311 Impairment** "remaining Total Tax Decimal is not zero" | Market Group pending (MG005/MG006) **or** tolerant-decimal | §4 / §9 — complete the market group (25-01035382, 25-01018233) |
| **314 rejection** when cleaning a batch / entering Ad Valorem | Usually batch-too-large timeout, RRV DOIs present | §11 / §13 — break into smaller batches; raise QPEC timeout (25-01037076) |
| PPN **reversing but not rebooking** / reversal doesn't tie to original | Missing rows in the **reversal source table**; or wrong DOI accounting rule (CUR vs HIS) | §5 — insert missing reversal-source rows (25-01061140); check accounting rule (25-01031081) |
| **Recoup PPN not recouping** / perpetually recoups | RD recoup logic only saw rebooks, not reversals; full-recoup transfer where from-owner gone | §6 — fixed in code; confirm patch (23-00910947 / ADO #1554250) |
| **DRI tier change**: results reverse Tier 1 but don't rebook Tier 2 (or double) | Missing Tier-2 **DRI link**; or RV40 (Deleted Link) PPNs not generated | §7 — create the Tier-2 DRI link & rerun (25-01035020); manual RV40 workaround (26-01099863) |
| **BKRVNU** picks up too many / wrong PPNs; "Could not generate PROP-DO selection table" | `RONL_MI_STAT.RRID` not updated → selection thinks more PPNs exist | §8 — script to update RRID (24-00988324 / ADO long-term WI); `QPSVLBuildSelection.cpp` |
| **SP025 / VL40** creates a PPN for every product / unnecessary DRI links / opens unrelated grids | Over-generation defect (FSTR-era) | §10 — confirm fix build (22-00512601, 22-00512603, 22-00512823) |
| **JE100 will not clean** / "SPE" / SQL error posting | Bad SPEd run / data; long-term in upgrade | §11 — RRV cleanup script short-term (22-00684022); upgrade long-term (24-00947756) |
| "**Remaining Tolerant Decimal exceeded**… consider increasing TOLERANTDEC" | Distribution tolerance floor | §12 — modify `DISTRIBUTION.TOLERANTDEC` (24-00942325, 24-00952106) |
| PPA/PPN **times out** / DO Tracking timeout / out-of-memory on large batch | Batch too large / timeout setting | §13 — raise QPEC.ini timeout; smaller batches (25-01005326, 25-01037076) |
| **SOD amounts multiplying** / MEG owner getting marketing / DRI gross volumes doubled on PPA | Distribution/tracking defect (SOD/MEG/DRI doubling family) | §14 — confirm patch (22-00705244, 24-00949405, 25-01008737) |
| **Tax / severance PPA** off by large $ after upgrade; MK (marketing) disappeared from VL031 | Marketing/source rows dropped on reverse-rebook | §14 — re-upload/restore the source files (26-01084407); long-term WI |

---

## 2. Pipeline & Concepts

```
[Original valuation already distributed]  →  something changed for a PRIOR month
        (DOI decimal change, owner transfer, tier/DRI change, tax-rate change, pay-code change, price correction)
        │
        ▼  TRIGGER A PPN
   SP025 (DOI accounting-rule / deck change)  •  VL031 (rev-detail edit)  •  VL40 (deleted-link / DRI)  •  PD41 (Mkt-Group rep change)  •  LD45/LD64/LD65 (DO owner exception / recoup)
        │   creates PPN rows; PN020 = PPN Creation, PN025 = PPN Query (select which to include)
        ▼
   VL100  — PPA/PPN VALUATION  → builds RRV reversal decks (RD010/RD031) + rebook decks
        │   (reverses the original distribution, recomputes, rebooks to corrected owners/decimals)
        ▼
   JE100  — POST / CLEAN the run   →  owner balances, suspense, journal
        └── BKRVNU = the back-out/reversal revenue process that selects which PPNs to include
```

### Key terms (Quorum / QRA vocabulary)
- **PPN** = *Prior Period Notification* — the system-generated flag/row that says "this prior production month needs a prior-period adjustment." Created automatically when you change a deck/DOI/tier/tax/pay-code for an already-distributed month, or manually. Lives in `RONL_MI_STAT` (the PPN/MI-status table) keyed by **RRID**.
- **PPA** = *Prior Period Adjustment* — the actual reverse-and-rebook run that processes one or more PPNs.
- **RRID** = Revenue Run / Reversal-Rebook ID — the batch identifier for a PPA. You clean it from **JE100** and rerun from **VL100**.
- **RRV** = *Reversal Revenue (deck)* — the historical deck the PPA reverses. RRV DOIs / RRV decks must exist and be **Completed** for the PPN to process; a missing RRV owner row is the classic **301** cause.
- **DRI** = *Direct Revenue Interest* — tiered ownership links. A **tier change** (Tier 1 → Tier 2) generates **RV40 "Deleted Link" PPNs**; the matching **Tier-2 DRI link must be set up** or the rebook side silently does nothing (25-01035020).
- **MEG / Market Group** = grouping of owners/DOIs for distribution. Statuses on **MG004 / MG005 / MG006** must be **Completed**; a *Pending* market group or RRV deck causes **302 / 311** impairments (25-01035382).
- **Impairment reason codes** (PPN rejects): **301** = no owner records found / missing RRV record; **302** = remaining (entitlement) amount not zero; **305**, **310**; **311** = remaining *tax* decimal not zero; **314** = batch/RRV-DOI reject. Code/message titles live in `QARCH_CODE_MSG_TITLE.json`.
- **Recoup** = recovering a prior overpayment from an owner across a transfer. LD65 = "Recoupment 'Y' Flag Non-WI Transfer." Recoup tracking historically looked at **rebooks**; fixed to look at **reversals** so *full*-recoup transfers (from-owner no longer on the historical deck) recoup correctly (23-00910947).
- **SOD** = *Split-of-Deck* / Special Owner Distribution arrangement (owner-level overrides). SOD amounts multiplying / MEG owner receiving marketing are distribution-tracking defects (25-01008737, 24-00949405).
- **Accounting rule CUR vs HIS** — a DOI deck flagged **Current** vs **Historical**. PPN tracking expects HIS for many client business models; a deck mistakenly left **CUR** produces incorrect owner-level distribution on PPNs (25-01031081).
- **BKRVNU** = the back-out reversal-revenue batch process that selects PPNs (`RONL_MI_STAT`) to include. Over-selection traces to an RRID not being updated (24-00988324).
- **TOLERANTDEC** (`DISTRIBUTION.TOLERANTDEC` in `QARCH_CNFG_CTRL`) = the rounding tolerance for owner distribution; too tight → "remaining tolerant decimal exceeded" / 302 (24-00942325).
- **QPEC** = the QRA processing/calc engine service; `QPEC.ini` holds the batch **timeout** (default 3600s). PPA timeouts are usually batch-size + timeout, not a code bug (25-01005326, 25-01037076).
- **VL031 / VL100 / JE100 / PN020 / PN025 / RD010 / RD031 / MG004-006 / SP025 / DO105 / LD45 / LD64 / LD65 / PD41 / TX021 / RC015 / JE020 / RD030 / JE110** = the QRA screens referenced throughout (PPN creation, query, valuation, post/clean, decks, market groups, DOI history, exception/recoup, tax rate, price input, account map, manual JE).

---

## 3. Decision Tree

```
QRA Prior-Period-Adjustment (PPN/PPA) case
│
├─ PPN failing with an IMPAIRMENT reason code?  →  GET the reason code + RRID + PROP_NO/DOI from the error
│   ├─ 301  "no owner records / missing RRV record"      → §4  (missing owner row on RRV deck; fix RTRN_VL_RVSL_SRC)
│   ├─ 302  "remaining amount not zero"                   → §4/§9/§12 (Market Group pending? else TOLERANTDEC)
│   ├─ 311  "remaining Total Tax Decimal not zero"        → §4/§9 (Market Group / RRV deck pending — complete it)
│   ├─ 314  reject when cleaning batch / Ad Valorem       → §11/§13 (batch too big → smaller batches + timeout)
│   └─ 305 / 310 / other                                  → §4 (verify RRV deck + owners; resolution may be unclear)
│
├─ PPN processes but the NUMBER is wrong?
│   ├─ Reverses but doesn't rebook / reversal ≠ original  → §5 (missing reversal-source rows; or CUR-vs-HIS rule)
│   ├─ Recoup PPN not recouping / perpetually recoups      → §6 (recoup logic; confirm patch)
│   ├─ DRI tier change won't rebook to new tier / doubles  → §7 (missing Tier-2 DRI link; RV40 not generated)
│   ├─ SOD multiplying / MEG marketing / DRI gross doubled  → §14 (distribution-doubling defect; confirm patch)
│   └─ Tax/severance PPA off after upgrade; MK gone VL031   → §14 (source rows dropped; restore/re-upload)
│
├─ PPN over-GENERATED (too many)?
│   ├─ One PPN per product when one product changed / unnecessary DRI links / unrelated grids opened → §10 (SP025/VL40 defect)
│   └─ BKRVNU pulls more PPNs than real / "PROP-DO selection table" error → §8 (RONL_MI_STAT RRID not updated)
│
├─ Process CRASHES (not impairment)?
│   ├─ JE100 won't clean / SPE / SQL error posting        → §11 (RRV cleanup script; upgrade long-term)
│   ├─ Times out / out-of-memory / DO-tracking timeout    → §13 (QPEC.ini timeout; smaller batches)
│   └─ "intolerant / remaining tolerant decimal"           → §12 (TOLERANTDEC)
│
└─ "How do I…", audit, vague error, only ran half the PPNs → §17 Expected-Behavior FAQ (Training / Customer Error)
```

---

## 4. Cluster A — Impairment reason codes 301/302/305/310/311/314

**The single largest PPA signature.** A PPN drops to **CE-Rejects / Impaired** status in VL100 or fails to clean in JE100 with a reason code. The code tells you where to look. Verbatim examples:

```
Sales input impaired: RVNU_RUN_ID = 25753, RD_SEQ_NO = 374563, PROP_NO = 420460.122. Impaired reason code = 302   (22-00618314)
301 Impaired Reason — No owner records were found for the current transaction.             (22-00667672, 24-00994919)
311 Impairment - The remaining Total Tax Decimal is not zero for Tax Type FE on DOI …/RRV/200/1 …  (25-01019939)
314 rejections as the result of there being RRV DOIs                                        (25-01037076)
```

**Root causes & fixes seen (ranked):**

| Reason | Most common root cause | Fix | Case |
|---|---|---|---|
| **302** "remaining amount not zero" | (1) **Market Group / RRV deck in PENDING** on MG004/MG005/MG006; (2) **tolerant-decimal** floor too tight | (1) Complete the market group & RRV deck → PPNs process (25-01035382, 25-01042276); (2) raise `DISTRIBUTION.TOLERANTDEC` (e.g. 0 → 1E-9) in `QARCH_CNFG_CTRL` (26-01079330) | 22-00618314, 22-00523796, 26-01079330, 25-01035382 |
| **301** "no owner records / missing RRV record" | A required owner row is **missing on the historical RRV deck**, usually after an owner **transfer** (e.g. 13808→26027) | Update/insert the missing row in **`RTRN_VL_RVSL_SRC`** (change old owner to new) (24-00994919); or confirm the PPA truly has no owners and can be posted (22-00667672 — was safe to post) | 24-00994919, 22-00667672 |
| **311** "remaining Total Tax Decimal not zero" | RRV/Market-Group **pending** status (MG005/MG006), or tolerant-decimal on the tax leg | Complete the market group & RRV deck (25-01018233, 25-01035382); else raise TOLERANTDEC (§12) | 25-01019939, 25-01018233 |
| **314** reject cleaning a batch | **Batch too large** (selecting every LD64/LD65 batch into one) → timeout while RRV DOIs present | Break into **smaller batches**; raise QPEC.ini timeout as a temporary unblock; A&P (Acquisition & Property) is the long-term path (25-01037076) | 25-01037076 |
| **302/311 family, NGL/Plant** | Tax mis-applied to **Plant Products** (Major Prod 400) | Remove **FE tax** from Major-Product-400 DOI Accounting Rules — FE should not calc on plant products (25-01061052) | 25-01061052, 26-01079330 (10-GAS) |

**Fix recipe:**
1. Get the **reason code + RRID + PROP_NO/DOI + production date** from the VL100/JE100 error log.
2. **301** → look on the RRV deck for the owner; if a transfer happened, fix the owner reference in `RTRN_VL_RVSL_SRC` (verify-SELECT first).
3. **302 / 311** → **check MG004/MG005/MG006 first** (market group + RRV deck must be **Completed**). This is the most common and is *customer-fixable*. Only if all groups are Completed and the residual is a tiny rounding figure do you raise `DISTRIBUTION.TOLERANTDEC` (§12).
4. **314** → batch sizing + timeout (§13), and check for stray RRV DOIs from sold assets.
5. Reason-code text/titles are defined in `QARCH_CODE_MSG_TITLE.json` (per-client `*.Upstream.Metadata`).

---

## 5. Cluster B — Reverse / Rebook not tying

PPNs that **reverse the original distribution but don't rebook correctly**, or where the reversal amount doesn't tie to the original payment. The recurring technical root cause is **missing rows in the reversal source table** or a **wrong DOI accounting rule**.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| PPN reverses but **rebook is missing / doesn't tie** | Missing records in the **Reversal Source Table** for the RRID | Script to **insert the missing reversal-source rows** (tested in DEV; gated on patches 10/11/12) | 25-01061140 |
| Reversal/rebook **decimals don't match** owner-level | Decks set up as **CUR** when the client's business model requires **HIS** → PPN tracking breaks | Long-term: change deck accounting rule to HIS; short-term: **RD030/JE110 manual JE** to pay owners correctly (SQL provided to identify TRANS_AMT/tax) | 25-01031081 |
| **WI transfer to RI** PPNs reverse incorrectly (reversed marketing never charged to the RI owner) | Recoup-remediation logic didn't account for **workspace transfers** | Updated the **Recoup Remediation script** to handle workspace transfers (`02_GLE_UPG_QRA_RECOUP_REMEDIATION_WS_Groups.sql`) + set config **`WRITE_TO_DB_ONLY_AT_END = 1`** | 25-01028434 |
| **PPN reversal doubled** (variance in JE100, product 400) | Reversal-doubling defect | **Software update** (package also covered 20-00076412, 20-00086023) | 22-00560573 |
| Reversal amount **doesn't tie to original payment** | Reverse/rebook tracking defect | Included in **July 2021 Patch** | 22-00674497, 22-00674496 |
| Reverse-rebook PPA **partially failed** | Reverse-rebook tracking defect (BP UPS) | Code fix — ADO **#1702863** / **#1742495** (Patch 4 family); confirm build | 24-00988053 |
| PPNs **reverse & rebook to historical / old owner** | Reversal-to-old-owner defect (Parsley/Permian-era) | Closed as part of broader reverse-rebook fixes | 22-00690455, 22-00705246 |

**Fix recipe:** confirm whether the **reversal side is correct** (it usually is). If the rebook is missing or owner decimals don't match: (a) check the **DOI accounting rule (CUR vs HIS)** for the affected deck — a CUR deck that should be HIS is the most common *config* root cause and is fixed by re-flagging + a manual JE for already-processed runs (25-01031081); (b) check the **reversal source table** for missing rows for that RRID and backfill via script (25-01061140); (c) for WI→RI / workspace-transfer scenarios use the updated recoup-remediation script (25-01028434). True reversal-*doubling* is a code defect — confirm the patch (22-00560573, ADO #1702863/#1742495).

---

## 6. Cluster C — Recoup PPNs

A distinct defect family around **recoup** (recovering prior overpayments across an owner transfer).

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **Recoup PPN not recouping** | RD recoup logic checked **rebooks**, so it only recognized recoup on *partial*-recoup transfers where the from-owner still existed on the historical REV deck | **Modified RD recoup logic to look at REVERSALS instead of rebooks** — now recognizes recoup on *full*-recoup transfers where the from-owner is gone | 23-00910947 ("Issue Log 167"); long-term 23-00921774 |
| PPNs with an old recoup transfer **perpetually recoup** instead of one-time | One-time-vs-perpetual recoup defect | Code fix — ADO **#1643472** (ERF, Closed) | (ERF) |
| **Recoup PPN system timeout** / out-of-memory in BKRVNU | Large recoup batch | Code/perf — ADO **#1613436** (MAC), **#1616978** (MEWU, 23-00914215) | 23-00894739 (DO-tracking timeout) |
| **WI transfer to RI** recoup reversing wrong | Recoup remediation didn't handle workspace transfers | Updated remediation script + `WRITE_TO_DB_ONLY_AT_END=1` | 25-01028434 (also §5) |
| Generic **recoup reversal errors** | Recoup tracking | Resolution pattern unclear from mined cases (closed without a recorded resolution) — escalate with the RRID | 23-00912753 |
| Recoup PPN processing error (QRA) | Recoup selection defect | Code fix — ADO **#1554250** (Closed), research task #1554252 | (PA) |

**Fix recipe:** modern builds contain the reversals-based recoup logic (23-00910947). If a client on an older build reports recoup-not-recouping, confirm the fix is in their build before scripting. For perpetual recoup, ADO #1643472. For WI→RI / workspace-transfer recoup, use the workspace-aware remediation script and set `WRITE_TO_DB_ONLY_AT_END=1` (25-01028434). Recoup timeouts → §13.

---

## 7. Cluster D — DRI tier change PPNs

DRI (tiered ownership) **tier changes** are a recurring high-severity PPA scenario: changing a DOI from Tier 1 to Tier 2 generates **RV40 "Deleted Link" PPNs** for the affected months, but the rebook side fails.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| Results **reverse Tier 1 but won't rebook Tier 2** (no rebook at all) | The new **Tier-2 DRI link was never set up** for those DOIs | **Create the Tier-2 DRI links** and rerun all the PPNs → results correct | 25-01035020 (Herminie) |
| DRI Tier-change PPNs **not reversing — just rebooking Tier 2 and doubling** | Deleting the link in **SP025 did not generate RV40 PPNs** for that well | Workaround: **manually create the RV40 reversal PPNs** (case 26-01100136 logged) | 26-01099863 |
| DRI PPN **validation error** on creation | DRI link/validation defect | Software Defect — confirm build | 26-01084560 |
| DRI **gross volumes doubled** on PPA records | DRI doubling defect | **Software update corrected it** | 22-00705244 |
| DRI defect: valuation picked up gross value/volume from an **unprocessed DRI link** for the same property during PPA | Unprocessed-DRI-link bleed-through | Software Defect (DRI valuation) — confirm build | 23-00917708 |
| DRI VLA PPN error "requires additional PPN selection" | Related-PPN selection (must include all related) | Documentation/training (24-00995450) — see §17 | 24-00995450 |

**Fix recipe:** for any DRI tier-change PPN that reverses but won't rebook, the #1 cause is a **missing Tier-2 DRI link** — set it up and rerun (25-01035020). If SP025 link deletion **didn't generate the RV40** PPNs at all, manually create the RV40 reversal PPNs as a workaround (26-01099863). DRI *doubling* (gross volume / value from unprocessed links) is a code defect — confirm the fix build (22-00705244, 23-00917708).

---

## 8. Cluster E — BKRVNU / RONL_MI_STAT

The **BKRVNU** back-out reversal process selects which PPNs to include from **`RONL_MI_STAT`**. When the RRID on that table isn't maintained, BKRVNU over-selects.

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| BKRVNU **includes more PPNs than really exist** / errors processing a PPN-PPA | **`RONL_MI_STAT.RRID` not updated correctly** → the system thinks there are more PPNs to include in BKRVNU | Short-term **script to update the RRID in `RONL_MI_STAT`**; long-term WI **#1683728** family | 24-00988324, 24-00989980 (RCA), 25-01044039, 25-01050026 (related), 24-00990002 (another script for similar 24-00988324) |
| **VL031 DRI PPN records don't show in VL100** | **RRID not populated on `RONL_MI_STAT`** | Defect (FSTR4-era) — populate RRID | 22-00512598 |
| "**Could not generate the PROP-DO selection table** for PPN records" | PPN selection-table build failure | Software Defect — escalate with RRID; selection logic in `QPSVLBuildSelection.cpp` | 22-00672667 |
| BKRVNU errors | Selection/processing defect | Software Defect — confirm build | 24-00951407 (BKRVNU Errors) |

**Fix recipe:** the signature is **BKRVNU pulling in more PPNs than the user expects** or VL031 PPNs not surfacing in VL100. Root cause is the **RRID column on `RONL_MI_STAT`**. Short-term, deploy the script to correct the RRID (24-00988324). The selection logic lives in **`QPDllRevenueAcctgBR/QPSVLBuildSelection.cpp`** (repo `Quorum.Upstream.QRA.ClassicBatch`). Escalate the long-term WI; this family recurred across 24-00988324 → 24-00989980 → 25-01044039 → 25-01050026.

---

## 9. Cluster F — MEG / Market Group PPN failures

Market Groups (MEGs) gate PPN processing. A pending or mis-configured group is the most common *config/expected* cause of 302/311 impairments and transfer failures.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **PPN Failure when removing a MEG group** | MEG/exempt-flag data left behind | Script **`QRA - SRC_UPDATE_DONL_MKT_EXMPT`** run in PRD (clears the marketing-exempt flag) | 26-01071059 |
| **302 / 311 impairment** on RRV DOI type, failing multiple steps | **Market Group (MG006) and associated RRV deck (MG005) in PENDING** | Update MG status + RRV deck to **Completed** → VL100 PPNs process | 25-01035382, 25-01018233 |
| **MEG owner receiving marketing** in a PPA | MEG distribution defect | Software Defect — confirm build (resolution detail not recorded) | 24-00949405 |
| **PD41 Market Group Rep Change** PPNs incorrectly generated / burdening NWI owner with SOD; incorrect owner payments | Market-group rep-change PPN defect | Software Defect — ADO family for PD41 mkt-grp PPNs; confirm build | 23-00929090, 23-00927247 |
| **MG004 error** on Reversal/Tax PPN; JE100 won't clean | Market-group state vs the PPN | Short-term **RRV script** to clean the SPEd run | 22-00684022, 22-00684013, 22-00684032 |
| PPN transfer failure | **Market group wasn't completed** | Complete the market group | 25-01046553 |
| PPNs **journalizing to the wrong product** (BP GOM) | Market-group/product mapping defect | Software Defect — confirm build | 22-00672016 |

**Fix recipe:** for 302/311 impairments and "PPN transfer failure," **always check MG004/MG005/MG006 first** — a *Pending* market group or RRV deck is the most common cause and is customer-fixable by completing the group (25-01035382, 25-01046553). For removing a MEG that leaves a stuck exempt flag, the `SRC_UPDATE_DONL_MKT_EXMPT` script clears it (26-01071059). PD41 market-group-rep-change over-generation and MEG-marketing bleed are genuine code defects — confirm the build.

---

## 10. Cluster G — SP025 / VL40 over-generating PPNs

A historical (FSTR-numbered) defect family where a deck/DOI change **generates far more PPNs than intended** — one per product, unnecessary DRI links, or PPNs on unrelated grids.

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **SP025 creates a PPN for every product** when only one product changed in an ALL DOI | Over-generation in PPN staging | Software Defect (FSTR4479) — confirm fix build | 22-00512603 |
| **VL40 creates unnecessary DRI links** | Link-generation defect | Software Defect (FSTR4432) | 22-00512601 |
| **Change on SP025 forces CA to be opened for unrelated grids** | Close/CA dependency defect | Software Defect (FSTR4572) | 22-00512823 |
| **PD41 PPNs incorrectly created after Pay Code Change with Funds** | Pay-code-change PPN defect | **Customer must upgrade** (fix is in a later build) | 25-01030578 |
| **RV40 PPNs incorrectly created** on upgrade | RV40 generation defect | Hotfix (March; MEW upgrade) | 22-00546249, 22-00659999 |
| **Well-completion 99 cross-references** create unnecessary PPNs | Cross-reference generation | Software Defect | 22-00653773 |

**Fix recipe:** these are generation-side defects — the fix is almost always **a specific build/hotfix**, not a script. Identify the client's build and confirm the FSTR/WI is included. For the **pay-code-change** family (25-01030578) the resolution was explicitly "customer will have to upgrade."

---

## 11. Cluster H — JE100 won't clean / SQL errors posting

The PPA process crashes or refuses to clean a run in **JE100** (distinct from §4 where it rejects with an impairment code).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **JE100 won't clean** / **MG004 error on Tax PPN** | SPEd (errored) run left behind; market-group state | Short-term: **RRV script to clean the SPEd run** | 22-00684022, 22-00684013 |
| **Unable to process oil rebookings for SP025 changes — JE100 finishes with SPE** | Rebooking-processing defect | **Fixed in the latest upgrade** (long-term) | 24-00947756 |
| **SQL Errors Posting and Cleaning in JE100** | Data/SQL error during post-clean | Software Defect / data — escalate (resolution detail not recorded) | 24-00973645 |
| **"Cannot insert duplicate key row in dbo.TONL_TAX_INPUT (UIX_TONL_TAX_INPUT)"** | Duplicate tax-input row on the tax-PPA path | Software Defect — escalate with RRID (resolution pattern unclear from mined cases) | 26-01067531 |
| **QRA SQL errors attempting to clean a batch** (314) | Batch too large → timeout | Raise QPEC timeout temporarily; smaller batches (also §4/§13) | 25-01037076 |

**Fix recipe:** if JE100 won't clean an errored/SPEd run, the short-term unblock is the **RRV cleanup script** to remove the bad run (22-00684022). For SP025 oil-rebooking SPE, the long-term fix is in the upgrade (24-00947756). Duplicate-key on `TONL_TAX_INPUT` and generic SQL post errors are escalation candidates — capture the RRID and exact SQL error.

---

## 12. Cluster I — Tolerant-decimal & rounding

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **"Remaining Tolerant Decimal exceeded for owner distribution. Tolerant Decimal: 2E-09, Remaining Total Entitlement Decimal: 3.5E-09. Consider increasing TOLERANTDEC"** on VL100 (massive tier-to-tier PPA, many owners) | Distribution tolerance floor too tight for the owner count / decimals | **Modify `DISTRIBUTION.TOLERANTDEC`** (raise the tolerance) in `QARCH_CNFG_CTRL` | 24-00942325 |
| **302 impairment** that is really a tiny rounding residual (10-GAS Big Pool) | TOLERANTDEC = 0 | Set **`DISTRIBUTION.TOLERANTDEC` 0 → 0.000000001 (1E-9)** | 26-01079330 |
| **Tolerant-decimal error on NEPSU00 PPN** | Tolerance + a stuck 302; needed transfer rework | Delete the CE runs from VL100, transfer the IR back to original per DO105 history, reprocess PPNs to clear 302, then redo the recoup transfer | 24-00952106 |
| **Progressive rounding errors on LD17 PPN** | Rounding accumulation defect | Software Defect — confirm build | 22-00655375 |

**Fix recipe:** when VL100 says "consider increasing TOLERANTDEC" or a 302 residual is a sub-nano-decimal, raise **`DISTRIBUTION.TOLERANTDEC`** in `QARCH_CNFG_CTRL` (typical safe value 1E-9). Confirm the residual is genuinely a rounding artifact and not a real out-of-balance (a large residual is a real distribution error, not a tolerance problem — go to §4/§5). Progressive rounding (22-00655375) is a code defect.

---

## 13. Cluster J — PPA performance / timeouts

| Issue | Root cause | Fix | Case / ADO |
|---|---|---|---|
| **PPA times out** (default 3600s) on large batch | QPEC batch timeout too low | Raise **`QPEC.ini` timeout** (e.g. 3600 → 7200, or 14400 as a temporary unblock); break into smaller batches | 25-01005326, 25-01037076 |
| **QRA/QDO DO-Tracking timeouts** processing large PPN batches | DO-tracking query performance on big batches | Perf work; smaller batches; ADO recoup-timeout family (#1613436, #1616978) | 23-00894739 |
| **Recoupment PPN system timeout** / **out-of-memory in BKRVNU** | Large recoup dataset | Code/perf — ADO **#1613436** (MAC), **#1616978** (MEWU) | (MAC/MEWU) |
| **System Out of Memory** on screen | App-tier memory / session | Often transient — **log out and back in**; batch the work | 24-00984941 |
| **Long processing times / PPN timeouts** post-patch | Batch sizing + timeout | Smaller batches; raise timeout (also §4) | 22-00560571, 25-01029678 (post-June-patch timeouts) |

**Fix recipe:** PPA/PPN timeouts are **overwhelmingly batch-size + the `QPEC.ini` 3600s default**, not a code bug. First lever: split the PPNs into smaller batches (the 314/clean cases were caused by selecting *every* LD64/LD65 batch at once). Second lever: raise the QPEC timeout (7200 typical; 14400 only as a temporary unblock). Recoup-specific OOM/timeouts have dedicated WIs (#1613436, #1616978).

---

## 14. Cluster K — SOD / tax PPA

Distribution-level defects where the **amount or volume on the PPA is wrong** (as opposed to the process failing).

| Issue | Root cause | Fix | Case |
|---|---|---|---|
| **SOD amounts multiplying in PPAs** | SOD distribution-tracking defect | Software Defect — confirm build (resolution detail not recorded) | 25-01008737 |
| **MEG owner receiving marketing** in a PPA | MEG/marketing distribution defect | Software Defect | 24-00949405 |
| **DRI gross volumes doubled** on PPA records | DRI doubling | **Software update corrected it** | 22-00705244 |
| **Tax/severance PPA off by ~$900K after upgrade; MK (marketing) disappeared from VL031** for specific properties | Marketing source rows **dropped on reverse-rebook around the upgrade** → severance PPA reverses *with* MK, rebooks *without* | Workaround: **re-upload the (marketing) files** to restore the source rows; long-term WI **26-01088288** | 26-01084407 |
| **WI Transfer not tracking on SOD DOIs** (MEW 2024.04 upgrade) | WI-transfer-on-SOD tracking defect | Software Defect — confirm build | 24-00986067 |
| **Sev-tax PPA** (RRID 6378) wrong | Tax-PPA calc defect | Software Defect — confirm build | 22-00818706 |
| Negative transfer to old owner (PPA reversal/rebook) | Reverse-rebook to old owner | Software Defect (also §5) | 22-00705246 |

**Fix recipe:** for "amounts multiplying / doubled" (SOD, DRI gross, MEG marketing) the pattern is a **distribution-tracking code defect** — reproduce, capture the RRID + owner + product, and confirm the fix build (several were corrected by software updates: 22-00705244). For **tax/severance PPA wrong after an upgrade with marketing missing from VL031** (26-01084407), the data root cause is **dropped marketing source rows** — restoring them (re-upload) is the workaround while the long-term WI is delivered.

---

## 15. Known ADO Items

| ADO # | Type / State | Title (abbrev.) | Cluster | SF Case |
|---|---|---|---|---|
| **#1554250** | Bug / **Closed** | QRA: Recoup PPN Processing Error (research task #1554252) | §6 | (PA) |
| **#1643472** | Bug / **Closed** | ERF — PPNs with old recoup transfer perpetually recoup instead of one-time | §6 | (ERF) |
| **#1613436** | Bug / **Closed** | MAC — Recoupment PPN System Timeout Error | §6/§13 | (MAC) |
| **#1616978** | Bug / **Closed** | MEWU 2021.04 — Out-of-memory / SQL timeout processing Recoup PPNs in BKRVNU | §6/§13 | 23-00914215 |
| **#1577228** | Bug / **Closed** | GECU — Jones PPN, non-recoup transfers from DO105 don't track properly | §5/§6 | 23-00882506 |
| **#1643472 / #1683731 / #1760759 / #1772747 / #1764232** | Bug/Req / **Closed** | GEC — non-recoup / RRV-not-tracking on recoup PPN; LD65 Recoupment 'Y' Flag Non-WI Transfer staging | §5/§6 | (GEC) |
| **#1683728** | Bug / **Closed** | SGY — PRD PPN & Business Unit Code updates (RONL_MI_STAT RRID family; ScriptReview) | §8 | 24-00988324 |
| **#1702863 / #1742495** | Bug / **Closed** | BP UPS — Reverse-rebook PPA partially failed (Patch 4 family) | §5 | 24-00988053 |
| **#1387993** | Bug / **Closed** | ENCU — RV20 Value Allocation PPN not generating any reversals | §5 | — |
| **#1724455** | Bug / **Closed** | MOM — Invoice displays incorrect reversal/corrected volumes upon PPA/rerun | §5/§14 | 25-01004724 |
| **#1659156 / #1659162** | Requirement / **Proposed** | PPA Edit (Reverse-Rebook) — Meter Tickets / Tank Run Tickets against FBDB | §5 | — |
| **26-01088288** | (SF long-term case) | Tax PPA — marketing dropped from VL031 on reverse-rebook | §14 | 26-01084407 |

> Many actionable cases were dispositioned **operationally** (data/config script) with no single product WI: TOLERANTDEC raises (24-00942325, 26-01079330), `RONL_MI_STAT` RRID scripts (24-00988324 family), recoup-remediation workspace script + `WRITE_TO_DB_ONLY_AT_END=1` (25-01028434), `SRC_UPDATE_DONL_MKT_EXMPT` (26-01071059), reversal-source backfill (25-01061140), DRI Tier-2 link setup (25-01035020). Confirm exact build/patch in **`Quorum.Upstream.QRA.ReleaseNotes`** when stating fix availability. (The WIQL title search also surfaces a large body of generic "PPN/PPA reversal" bugs — filter by client prefix + the cluster term before citing.)

---

## 16. Diagnostic SQL

> **Caveat:** QRA is **SQL Server** (`dbo.*` objects, e.g. `dbo.TONL_TAX_INPUT`), per-client database. Table/column names below come from case repro text + code search; **verify against the client DB before scripting**, and always run a verify-SELECT before any DELETE/UPDATE, wrapped in a transaction.

```sql
-- A. PPN rows + status for an RRID (which PPNs are in the run, what state)  (§4/§8)
SELECT RRID, PROP_NO, MAJ_PROD, PROD_DATE, MI_STATUS, RVNU_RUN_ID
FROM   RONL_MI_STAT
WHERE  RRID = @RRID
ORDER BY PROP_NO, PROD_DATE;
-- Red flag (§8): RRID null/stale here → BKRVNU over-selects. The RONL_MI_STAT RRID-not-updated family (24-00988324).

-- B. Market Group / RRV deck status — the #1 cause of 302/311 impairments (§4/§9)
--    PPNs will NOT process while a market group (MG006) or RRV deck (MG005) is Pending.
SELECT MKT_GRP_NO, STATUS, RRV_DECK_NO, DECK_STATUS
FROM   <market-group status table behind MG004/MG005/MG006>
WHERE  MKT_GRP_NO = @MEG;   -- confirm STATUS = 'Completed' for the group AND the RRV deck

-- C. Reversal source rows for an RRID — missing rows = reverse-without-rebook / 301 (§5)
SELECT *
FROM   RTRN_VL_RVSL_SRC
WHERE  RRID = @RRID;        -- after an owner transfer, the old owner may need updating to the new owner

-- D. Tolerant-decimal config (the 302 / "remaining tolerant decimal exceeded" lever)  (§12)
SELECT CNFG_KEY, CNFG_VALUE
FROM   QARCH_CNFG_CTRL
WHERE  CNFG_KEY = 'DISTRIBUTION.TOLERANTDEC';   -- 0 → 1E-9 (0.000000001) per 26-01079330 / 24-00942325
-- Related write-batching key seen in recoup remediation:
SELECT CNFG_KEY, CNFG_VALUE FROM QARCH_CNFG_CTRL WHERE CNFG_KEY = 'WRITE_TO_DB_ONLY_AT_END';  -- set 1 (25-01028434)

-- E. DOI accounting rule CUR vs HIS — wrong rule breaks PPN tracking (§5)
SELECT DOI_NO, ACCT_RULE   -- expect HIS for clients whose business model needs historical tracking
FROM   <DOI accounting-rule table behind SP025>
WHERE  DOI_NO IN (@dois);

-- F. DRI links for a property/DOI — a missing Tier-2 link = reverse-without-rebook on tier change (§7)
SELECT DOI_NO, TIER_NO, DRI_LINK_ID, EFF_DT, END_DT
FROM   <DRI link table>
WHERE  PROP_NO = @prop
ORDER BY TIER_NO, EFF_DT;   -- confirm a Tier-2 link exists for the months that won't rebook (25-01035020)

-- G. Impairment reason-code text (what does 305/310 mean for this client)
--    Definitions live in QARCH_CODE_MSG_TITLE.json in <CLIENT>.Upstream.Metadata (not always a DB table).

-- H. Duplicate tax-input rows (the dbo.TONL_TAX_INPUT unique-index violation, §11)
SELECT <key cols of UIX_TONL_TAX_INPUT>, COUNT(*) dup
FROM   dbo.TONL_TAX_INPUT
WHERE  RRID = @RRID
GROUP BY <key cols> HAVING COUNT(*) > 1;
```

---

## 17. Expected-Behavior / User-Education FAQ

~29 Training + ~70 Customer-Error cases. Recognize these to avoid needless scripts/escalations.

| Reported as | Reality / answer | Case |
|---|---|---|
| "PPN fails with **302 / 311 impairment**" | **Most common cause = Market Group / RRV deck in PENDING.** Check MG004/MG005/MG006 — once Completed, the PPN processes. Not a defect. | 25-01035382, 25-01018233, 25-01042276, 25-01046553 |
| "**VL100 submission/prelim error**" / "PPN won't process" | Client is **only processing HALF of related PPNs.** Related PPNs **must be run together** in the same run. | 25-01046303, 25-01003848, 25-01047805 (PPNs excluded in PN025) |
| "**Tier-to-tier rebooking incomplete**" | Process the **FROM-tier PPNs first, then the TO-tier** PPNs (order matters); and confirm the new tier's DRI link exists. | 24-00951224, 25-01035020 |
| "Reversals/rebooks have **decimals that don't match**" | Deck was set up **CUR when it should be HIS** for the client's model — re-flag; use RD030/JE110 manual JE for runs already processed. | 25-01031081 |
| "**Out of Memory** on the screen" / system error | Often transient — **log out and back in**; for batch jobs, **break into smaller batches**. | 24-00984941 |
| "**PPA times out**" | Batch too large + 3600s QPEC default — smaller batches; raise QPEC.ini timeout. | 24-00943699, 25-01005326 |
| "**540 / VL100 errors from transfers**" booked to the wrong (back-dated) month | Add a PPA for a production month that **predates the transfer**; or safely delete the RRV via an additional PPA. | 25-01053861 |
| "Tax calculating on **Plant Products (Major Prod 400)**" | **Remove FE tax** from the Major-Product-400 DOI Accounting Rules — FE should not calc on plant products. | 25-01061052 |
| "**SOD contract terms ignored**" / SOD volume balance off | Missing **price/index record (RC015)** that a formula needs; input it and rerun. | 25-01015404, 23-00934075 |
| "**Account could not be matched for group ##**" during PPN | **JE020 account map** missing the account(s); set them up. (A QPEC restart will NOT fix it.) | 25-01029609, 25-01029132 |
| "How do I … RRVs / PN025 source / reconcile" / audit / documentation requests | Training/docs, not defects. | 23-00915644, 23-00915823, 23-00922738 |

**Tell-tale it's user/expected:** a 302/311 that clears once the **market group/RRV deck is Completed**; a PPN error because only **part of a related PPN set** was run; a tier rebook done out of order; decimals off because the deck is **CUR not HIS**; "account not matched" because **JE020** isn't set up; or an out-of-memory/timeout that clears with a smaller batch or a re-login. **Verify market-group status, the full related-PPN set, the DOI accounting rule, and JE020 mapping before treating it as a defect.**

---

## 18. Key Code, Config Keys & Repos

### Screens / processes
| Screen / process | Purpose |
|---|---|
| **PN020 / PN025** | PPN Creation / PPN Query (select which PPNs to include — excluding here causes "only ran half" errors) |
| **SP025** | DOI accounting-rule / deck change — triggers PPNs (over-generation defects, §10) |
| **VL031 / VL40** | Revenue-detail edit / Deleted-Link (DRI) PPN generation |
| **VL100** | PPA/PPN **valuation** — builds RRV reversal + rebook decks; where impairments surface |
| **JE100** | Post / **clean** a PPA run (won't-clean / SPE, §11) |
| **BKRVNU** | Back-out reversal-revenue **PPN selection** process (`RONL_MI_STAT`, §8) |
| **MG004 / MG005 / MG006** | Market-group + RRV-deck status (must be Completed, §4/§9) |
| **RD010 / RD031 / RD030 / JE110 / JE020** | Reversal decks / manual JE / account map |
| **DO105 / LD45 / LD64 / LD65 / PD41 / TX021 / RC015** | DOI history / DO owner exception / recoup / mkt-grp rep change / tax rate / price input |

### Config keys (`QARCH_CNFG_CTRL`)
- **`DISTRIBUTION.TOLERANTDEC`** — owner-distribution rounding tolerance; raise (0 → 1E-9) for 302/"tolerant decimal exceeded" (24-00942325, 26-01079330).
- **`WRITE_TO_DB_ONLY_AT_END`** — set 1 alongside the recoup-remediation workspace-transfer fix (25-01028434).
- **`QPEC.ini` timeout** — batch timeout (default 3600s); raise to 7200 (14400 temporary) for large PPAs (25-01005326, 25-01037076).

### Key tables
- **`RONL_MI_STAT`** — PPN / MI-status rows keyed by **RRID** (the BKRVNU over-selection root, §8).
- **`RTRN_VL_RVSL_SRC`** — reversal source rows; missing rows → reverse-without-rebook / 301 (§5).
- **`dbo.TONL_TAX_INPUT`** (unique index `UIX_TONL_TAX_INPUT`) — tax-input; duplicate-key on tax PPA (§11).
- **`QARCH_CODE_MSG_TITLE.json`** — impairment reason-code / message-title definitions (per-client `*.Upstream.Metadata`).

### Code & repos (confirmed via ADO code search)
| Symbol / file | Repo / path | Cluster |
|---|---|---|
| `QPSVLBuildSelection.cpp` (PPN/VL build-selection) | **`Quorum.Upstream.QRA.ClassicBatch`** `/QPDllRevenueAcctgBR/` | §8 BKRVNU/RONL_MI_STAT selection |
| `QSQL_VLSnapShot.cpp` | `Quorum.Upstream.QRA.ClassicBatch` `/QPDllRevenueAcctgBR/` | §5/§8 VL snapshot |
| `QARCH_CODE_MSG_TITLE.json` (reason codes) | `SUM.Upstream.Metadata` / `<CLIENT>.Upstream.Metadata` `/STANDARD 16.0/` | §4 |
| BKRVNU / VLMI test data + `BKRVNU-SQL.md` analysis | `Quorum.QRA.AT`, `Quorum.QDO.AT`, `Quorum.Upstream.Tools/documentation/Analysis/BatchProcesses/BKRVNU/` | §8 |
| Release notes (fix-availability) | **`Quorum.Upstream.QRA.ReleaseNotes`** (e.g. `Quorum-QRA-2020.09.1.0.xml`) | all |

> **Repo families:** `Quorum.Upstream.QRA.ClassicBatch` (C++ revenue/PPA batch — `QPDllRevenueAcctgBR`), `Quorum.QRA.AT` / `Quorum.QDO.AT` (automated tests), `*.Upstream.Metadata` (per-client metadata incl. reason codes & screens), `Quorum.Upstream.Tools` (batch-process analysis docs). QDO (Division Order / DO tracking) is the sibling product that feeds PPN tracking — many recoup/transfer defects span QRA + QDO.

---

## 19. Escalation Guidance

**Route to Engineering (Software Defect) when:**
- PPN **reversal doubles** or **rebooks to the wrong/old owner** on correct inputs (22-00560573, 22-00705246, ADO #1702863/#1742495).
- **Recoup** logic wrong (not recouping / perpetual) on a supported build (23-00910947/#1554250, #1643472).
- **DRI** gross volume/value doubled or bleeding from unprocessed links (22-00705244, 23-00917708).
- **SOD multiplying / MEG marketing / WI-transfer-on-SOD not tracking** (25-01008737, 24-00949405, 24-00986067).
- **Generation** over-firing (one PPN per product, unnecessary DRI links, pay-code-change PPNs) (22-00512603, 22-00512601, 25-01030578).
- **BKRVNU / RONL_MI_STAT** over-selection and "PROP-DO selection table" failures (24-00988324, 22-00672667).
- Provide: **RRID + reason code (if any) + PROP_NO/DOI + production date + client build**, a repro, and the VL100/JE100 error log. Confirm fix availability in `Quorum.Upstream.QRA.ReleaseNotes` and the WI's target build.

**Handle as Configuration / data script (Cloud Ops or L4) when:**
- **TOLERANTDEC** too tight → raise `DISTRIBUTION.TOLERANTDEC` (24-00942325, 26-01079330).
- **RONL_MI_STAT RRID** stale → RRID-correction script (24-00988324 family).
- **Reversal source rows** missing → backfill `RTRN_VL_RVSL_SRC` (25-01061140); **WI→RI / workspace transfer** → recoup-remediation script + `WRITE_TO_DB_ONLY_AT_END=1` (25-01028434).
- **Missing Tier-2 DRI link** → create the link & rerun (25-01035020).
- **Stuck MEG exempt flag** → `SRC_UPDATE_DONL_MKT_EXMPT` (26-01071059).
- **Marketing source dropped** on tax PPA → re-upload the files (26-01084407).
- Always verify-SELECT in a transaction; QRA is SQL Server (`dbo.*`).

**Handle as Training / Expected behavior (no fix):** see §17 — **complete the market group/RRV deck** (302/311), **run all related PPNs together**, process **FROM-tier before TO-tier**, fix **CUR-vs-HIS** deck rule, set up **JE020** accounts, **smaller batches / re-login** for timeouts/OOM, and don't calc **FE tax on Plant Products (Maj Prod 400)**. Verify market-group status, the full related-PPN set, the DOI accounting rule, and JE020 mapping before escalating.

**Batch-size / timeout first (no code):** PPA "times out / won't clean / 314 / out-of-memory" — break the PPNs into smaller batches and raise the `QPEC.ini` timeout (3600 → 7200) before assuming a defect (25-01005326, 25-01037076, 23-00894739).

---

*Skill created: 2026-06-14.*
*Based on: 563 closed QRA Prior-Period-Adjustment SF cases — 158 actionable (Software Defect 131 + Application Configuration 25 + ChangeConfig 2) mined for fix recipes, plus ~35 Training/Customer-Error cases for the FAQ. ADO work items #1554250/#1554252, #1643472, #1613436, #1616978, #1577228, #1683728, #1683731/#1760759/#1772747/#1764232, #1702863/#1742495, #1387993, #1724455, #1659156/#1659162.*
*Companion (planned): SKILL_QRA_Suspense_CheckWrite, SKILL_QRA_DOI_Ownership, SKILL_QRA_Revenue_Valuation, SKILL_QRA_Severance_Tax, REPO_REFERENCE.md.*
