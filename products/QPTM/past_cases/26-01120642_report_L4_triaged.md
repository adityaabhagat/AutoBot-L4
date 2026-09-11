# L4 Triaged — Case 26-01120642

| | |
|---|---|
| **Salesforce Case** | 26-01120642 (`500UH00000uHTztYAG`) |
| **Client / TSP** | Lighthouse Midstream Services, LLC / **PNGTS** (Portland Natural Gas Transmission System) |
| **Contact** | `003UG000007XJKoYAO` |
| **Product / Module** | QPTM / Nominations — Nomination Submission, PAL (Park-and-Loan) business validation |
| **Environment** | DB prefix **HPE**; walkthrough tested in `HPE_UPGA1MID_QPTM`. ADO `FoundinVersion = 2025.10`, `FoundInEnvironment = Production`. **Client's currently-installed build NOT confirmed** — see §7. |
| **Priority** | High (SF) |
| **Classification** | **Software Defect** — confirmed at code level (not bad data, not customer error, not working-as-designed, not a version gap). **Secondary: Contract configuration** — the action-window setup is what makes the defect fire constantly. |
| **L4 / Date** | Auto-Bot (Aditya Bhagat) / 2026-09-11 |

---

## 1. Issue Summary

PAL nominations on PNGTS fail business validation on every submission; the scheduling team overrides each one. The customer expected the nomination to pass against the contract's **daily** limit and asked which limit is actually being evaluated.

Two rules fire on these nominations, and only one of them is correct:

- **`NN00003115`** — *"The nominated quantity must be less than or equal to the contract's daily quantity and the transaction type must match the action code for the nominated gas day."* Firing here is **appropriate** — the nominated gas days fall outside the contract's configured PAL action windows. Calling it *correct* is a design judgment, not a verified fact: see the caveat in §4 before leaning on it.
- **`NN00009604`** (*"LOAN NOMINATION CAN'T EXCEED OVERALL BALANCE."*) — *"You are currently nominating 15,000 DTH and the max you can nominate is **-1 DTH** based on your current inventory balance. Note: Nom may also be out of range."* This is the **defect**: a maximum of -1 DTH cannot be satisfied by any nomination.

Business impact: every out-of-window PAL Loan nomination produces a second, unsatisfiable error. Schedulers are overriding blind, which erodes the signal value of the override mechanism on a rule that is meant to protect an inventory ceiling.

**Direct answer to the customer's question:** the park-and-loan rules do **not** evaluate the daily contract limit. They evaluate **Maximum / Minimum Aggregated Quantity from the PAL/ISS tab**, combined with the **inventory-account ending balance** and **prior business-valid noms**. The daily limit is checked separately, by `NN00003115`.

## 2. Reproduction

Reproducible. Steps from `Case 26-01120642 Before Walkthrough HPE-PALVAL.docx` (author Sara Riano), **independently re-verified against source this session** — the arithmetic reproduces the on-screen message exactly.

Environment `HPE_UPGA1MID_QPTM`:

1. Contract Maintenance → contract **LPNG242** → Retrieve → **PAL/ISS tab**. Confirm Deal Type = **LEND**, Max Aggregated Quantity = **15,000 DTH**. In Dates & Quantities: **WITHDRAWAL 8/6/2026 – 8/6/2026**; **INJECTION 10/1/2026 – 10/31/2026**.
2. Authorization to Post Imbalances → confirm no prior nominations and zero inventory balance.
3. Nomination Submission → Gas Day **8/22/2026**, Def End Gas Day 8/22/2026, Cycle 1 Timely → Svc Req 118638852 / Prop 445 Castleton Commodities → Retrieve. Add a row for LPNG242: Rec Loc **080041** (INVENTORY PNGTS) 15,000; Del Loc **235006** (WESTBROOK M&N) 15,000; TT = **Loan**.
4. Validate.
   - `NN00003115` fires — **correct**, 8/22/2026 is in neither action window. Override it.
   - `NN00009604` fires — *"…the max you can nominate is -1 DTH…"* — **the defect**.
5. **Control:** repeat on Gas Day **8/6/2026** (inside the withdrawal window). The same 15,000 DTH is accepted and `NN00009604` stays silent — 15,000 equals the Max Aggregated Quantity exactly. This proves the quantity and the underlying data are sound and that **only the date window drove the failure**.

## 3. Root Cause (code level)

**When a Loan nomination falls outside the contract's withdrawal action window, `RuleNN00009604` discards the configured Maximum Aggregated Quantity and substitutes the literal `-1` as the ceiling; `-1` is not a valid negated Max AQ under the rule's loan sign convention, so it both forces the comparison to fail and escapes the display clamp, printing "-1 DTH" to the scheduler.**

Repo `Quorum.QPTM.Web`, branch `develop`, commit `4a43ed28a99670e7a0e2342c55641605c1ddd72f`, file `/Quorum.QPTM.Validations.Rules.Nomination/BusinessRules/RuleNN00009604.cs` (cached copy re-read this session; live source confirmed to match):

| Line | Code | Role |
|---|---|---|
| `:59` | `PalCache.GetPalActionbyType(…, Constants.ActionCodeWithdrawal)` | fetch the withdrawal action window |
| `:62` | `nomination.BegGasDay >= PalActionInfo.EffDateFrom && <= PalActionInfo.EffDateTo` | sets `IsNomInRange` |
| `:71-74` | `PalActionInfo == null` → `IsNomInRange = false` | **no withdrawal action row at all takes the same path** |
| `:97` | `nMaxCtrAggQ = resolverMDQ.GetMaxAggPAL(…)` | the real ceiling, 15,000 |
| `:100` | `nMaxCtrAggQ = nMaxCtrAggQ * -1;` | loan sign convention → -15,000 |
| `:107` | `nQtyTowardsParkLoan += (DelQty * -1)` | running total, negative |
| `:109` | `nEndBalCtrDiff = nQtyTowardsParkLoan + endBalQty;` | -15,000 |
| **`:111-114`** | **`if (!IsNomInRange) { nMaxCtrAggQ = -1; }`** | **the fault — real ceiling discarded** |
| `:116` | `if (nMaxCtrAggQ.HasValue && (nMaxCtrAggQ ?? 0) > nEndBalCtrDiff)` | `-1 > -15,000` → **TRUE**, fires |
| `:121` | `nMaxAvailable = (nMaxCtrAggQ ?? 0) - endBalQty;` | `-1 - 0 = -1` |
| `:123-126` | `if (nMaxAvailable > 0) { nMaxAvailable = 0; }` | `-1` is not > 0 → **not clamped** |
| `:128` | `GenericPropertyBag["MAX_CTR_QTY"] = nMaxAvailable…` | **"-1" reaches the screen** |

Verified trace on the step-3 inputs:
```
IsNomInRange = (8/22 >= 8/6) && (8/22 <= 8/6) = true && false = FALSE
:113  nMaxCtrAggQ         = -1                  (configured 15,000 discarded)
:107  nQtyTowardsParkLoan = 0 + (15,000 * -1)   = -15,000
:109  nEndBalCtrDiff      = -15,000 + 0         = -15,000
:116  FIRE?  -1 > -15,000                       = TRUE
:121  nMaxAvailable       = -1 - 0              = -1
:123  -1 > 0 is false -> NOT clamped -> MAX_CTR_QTY = "-1"
```
Had the gas day been 8/6/2026, `:116` evaluates `-15,000 > -15,000` = FALSE and no error is raised.

**The sentinel also defeats the null guard on the line it protects.** `ResolverMdq.GetMaxAggPAL` (`ResolverMDQ.cs:817-820` → `GetAggHelper:832-856`) resolves `KCTRL_PAL_ISS_DEAL.MAX_AGGREGATED_QTY` (`PalIssDealDO.cs:38`, `:2696`) and returns **`null`** when no PAL/ISS row matches — never 0. So:

| case | `nMaxCtrAggQ.HasValue` at `:116` | outcome |
|---|---|---|
| null, nom **in** window | false | rule **silently passes** — no ceiling enforced (fail-open) |
| null, nom **outside** window | **true** — `:113` overwrote it with `-1` | rule **fires with an impossible ceiling** |

`:113` flips `.HasValue` from false to true, so the guard at `:116` is live only in the case that does not need it. This is the sharpest statement of the defect — and it is why the Primary fix's regression risk in §4 is real rather than theoretical.

**Two distinct date gates are collapsed into one boolean.** `GetPalActionbyType` (`ContractCache.cs:1272-1297`) resolves `KCTRL_PAL_ACTN_DT_QTY` (`PALActionDateQtyDO.cs:38`) via `GetPalActionQty` (`:1252-1269`), which filters on **`BEG_FLOW_DT`/`END_FLOW_DT`** (`:1045`/`:1102`); the rule at `:62` then re-checks **`EFF_DT_FROM`/`EFF_DT_TO`** (`:929`/`:1305`). These are four distinct columns, not aliases. `IsNomInRange = false` therefore means "outside the flow window **or** outside the amendment effective window" with no way for the scheduler — or the message — to tell which.

**Correction to the existing walkthrough's root-cause framing — there is no sign-mirror bug.** The walkthrough attributes the defect to the display clamp being "sign-mirrored" from the Park rule `NN00009602` (`if (nMaxAvailable < 0)` at `RuleNN00009602.cs:121`), implying the fix is to flip `:123` to `< 0`. **That would be wrong and would introduce a new bug.**

The two rules run in deliberately different sign conventions, and the proof is a `Math.Abs` asymmetry:

| | `endBalQty` assignment | `nMaxCtrAggQ` negated? | Convention | Correct clamp |
|---|---|---|---|---|
| `9602` (Park) | `:89` `Math.Abs(acctBalance.EndBalQty)` | no | all-positive | `< 0` at `:121` ✓ |
| `9603` (Park wdl) | `:87` `Math.Abs(acctBalance.EndBalQty)` | n/a | all-positive | n/a |
| **`9604` (Loan)** | `:89` `acctBalance.EndBalQty` — **no `Math.Abs`** | **yes**, `:100` | signed/negative | **`> 0` at `:123` ✓** |
| `9605` (Loan inj) | `:89` `acctBalance.EndBalQty` — **no `Math.Abs`** | yes, `:100` | signed/negative | `> 0` at `:123` ✓ |

So in a genuine in-window breach, `nMaxAvailable = -5,000` encodes a real remaining capacity of 5,000 DTH. Flipping the clamp to `< 0` would zero out **every legitimate loan remaining-capacity figure** — turning a correct message into "0 DTH" across the board. The clamp direction at `:123` is right. The foreign object is the `-1` sentinel at `:113`, which is not a valid negated Max AQ under that convention.

**The display defect is a *missing* sign flip, not a wrong clamp.** `:127` flips `nQtyTowardsParkLoan` back to positive for display (`nQtyTowardsParkLoan * -1`) but `nMaxAvailable` receives no equivalent flip before `:128`. That is why a negative reaches the screen at all. Fix the sentinel to stop `-1`; consider flipping `nMaxAvailable` for display to stop legitimate negatives reaching schedulers too.

**What is explicitly NOT at fault:**
- **Contract or inventory data** — the control case accepts the identical quantity inside the window.
- **`KFK016`** — per SF KB 000004765 it validates only duplicate RFS rate and PAL-quantity records; it does not enforce quantity limits.
- **`NN00003115`** — firing correctly; it is the only rule that should be reporting this condition.
- **A version gap** — ADO 1863858 is `New` with no PR and no dev task. There is no build to upgrade to.

## 4. Suggested Code Fix (ranked)

### Primary (Recommended) — delete the sentinel; let the real ceiling be evaluated

`RuleNN00009604.cs:111-114`

```csharp
// BEFORE
if (!IsNomInRange)
{
    nMaxCtrAggQ = -1;
}

if (nMaxCtrAggQ.HasValue && (nMaxCtrAggQ ?? 0) > nEndBalCtrDiff)
```
```csharp
// AFTER  — remove the sentinel block entirely
if (nMaxCtrAggQ.HasValue && (nMaxCtrAggQ ?? 0) > nEndBalCtrDiff)
```

Out-of-window nominations are then judged against the contract's real Max Aggregated Quantity. In the reported scenario `-15,000 > -15,000` is false, so `NN00009604` stays silent and `NN00003115` alone reports the window mismatch — one correct error instead of two contradictory ones. An out-of-window nomination that *does* breach the ceiling still fires, now with a truthful number.

**Regression consideration — now CONFIRMED as a real risk, needs product sign-off before merge.** `GetMaxAggPAL` returns **`null`** (not 0) for a contract with no matching `KCTRL_PAL_ISS_DEAL` row or a blank `MAX_AGGREGATED_QTY` — verified at `ResolverMDQ.cs:832-856` (`decimal? value = null;` with no default) and `PalIssDealDO.cs:2696` (`CanBeNull=true`). Removing the sentinel therefore makes this rule **fail-open** for such contracts: `HasValue` is false and the rule goes silent where the sentinel previously forced a failure.

That is defensible — with no configured ceiling there is nothing for an aggregate-ceiling rule to enforce — **but it is only safe if `NN00003115` is actually wired to this client's TOS/TSP**, since that rule becomes the sole guard on the out-of-window condition.

**And a caveat on leaning on `NN00003115` at all.** Its out-of-window firing appears to come from PDWQ resolving to `0` for an unconfigured contract — `GetPdiqHelper` (`ResolverMDQ.cs:899-930`) returns a non-nullable `decimal` initialised to 0, and `RuleNN00003115.cs:58` casts it unguarded. That is the *same* missing-configuration pattern this report criticises elsewhere. So `NN00003115` may be producing the right outcome for the wrong reason. It is a serviceable backstop, not a principled one — worth a product decision rather than an assumption.

Confirm before shipping:

```sql
-- Is NN00003115 wired for the PNGTS TSP? If not, the Primary fix removes
-- the only remaining error on out-of-window PAL noms.  NOT YET RUN.
SELECT * FROM NNXREF_VALD_RULE_GRP_EFF_RULE
WHERE  VALD_RULE_CD = 'NN00003115';
```

### Alternative (Rejected) — clamp the display only

Change `:123` so a negative sentinel can never populate `MAX_CTR_QTY`. Rejected: it treats the symptom. The scheduler still receives a duplicate error for a condition `NN00003115` already reports correctly, and the stated maximum would read `0 DTH` — still unsatisfiable, merely less obviously absurd. This is precisely the state the Park rule `NN00009602` is already in, and it has not stopped that rule generating the same class of complaint.

### Also Rejected — flip the clamp to mirror `NN00009602`

As set out in §3, this breaks the loan sign convention and would zero out legitimate remaining-capacity figures.

**Recommendation:** take the Primary fix on `NN00009604`. The sibling rules share the *behaviour* (hard-fail when the nom is outside the action window) but **not the mechanism**, so "apply the same edit" is not a valid instruction — each needs a different edit:

| Rule | How it hard-fails out-of-window | Required edit | Display today |
|---|---|---|---|
| **9604** | sentinel `-1` at `:113` → `:116` `-1 > -15,000` true | **delete `:111-114`** | **`-1`** — clamp `:123` (`> 0`) can't catch a negative |
| 9602 | sentinel `-1` at `:111` → `:114` `-1 < nEndBalCtrDiff` true | delete `:109-112` — true analogue | `0` — clamp `:121` (`< 0`) catches it |
| 9603 | **no sentinel** — `nMaxCtrAggQ` does not exist in this file at all. `:105` is `if (nQtyTowardsParkLoan > nEndBalCtrDiff \|\| !IsNomInRange)` | remove `\|\| !IsNomInRange` from `:105` only | `0` — zeroed at `:112` |
| 9605 | sentinel present at `:113` but **irrelevant** — `:116` is `if (0 < nEndBalCtrDiff \|\| !IsNomInRange)`, independent of `nMaxCtrAggQ` | remove `\|\| !IsNomInRange` from `:116`; deleting the sentinel alone fixes nothing | can display a negative via `:121` |

Only **9602** is a true analogue of 9604. Scope the change deliberately; do not hand engineering a blanket "same edit in four files" instruction.

## 5. Expected Result After Fix

| Scenario | Current | After fix |
|---|---|---|
| Loan nom **outside** the withdrawal window | `NN00003115` fires (correct) **and** `NN00009604` fires stating max `-1` DTH | `NN00003115` fires alone |
| Loan nom **inside** the window, within Max Agg Qty | No error | Unchanged — no error |
| Loan nom **inside** the window, breaching Max Agg Qty | Error with a computed remaining quantity | Unchanged — this is the rule's purpose |
| Loan nom **outside** the window, breaching Max Agg Qty | Error stating `-1` | Error stating the true remaining quantity |

Never affected: stored contract data, inventory balances, scheduled quantities, invoicing. This is a validation-message defect only. Nominations already overridden are valid and need no remediation.

## 6. Diagnostic SQL

**All queries `NOT YET RUN`** — the `metadata`, `quorum-metadata-sql` and `quorum-metadata-oracle` MCP servers all failed to connect this session. Full set, with a provenance table for every name, in `verification_sql.md`.

**Important:** the first draft of these queries used table names taken from the QPTM KB skill `SKILL_QPTM_Nomination_Validation.md` — `NNCTRL_NOM_ERROR`, `QARCH_VALD_RULE`, `QARCH_TSP_CONFIG`. **None of those tables exist.** The KB skill is wrong and needs repair (see §7). Names below are anchored to live DDL in `Quorum.QPTM.Database` @ `develop`.

```sql
-- Proves which rules actually fired in PRD and whether they were overridden.
-- ACTV_NO is the same column the customer referenced in their own attachment.
-- Expect NN00003115 + NN00009604 with OVRD_IND = 1 and '-1' in ERROR_MSG.
SELECT d.BEG_GAS_DAY, d.CYCLE_ID, d.ACTV_NO, d.SR_BP_NO, d.SR_CTR_NO,
       d.DEL_QTY, d.NOM_STAT_CD,
       e.VALD_RULE_CD, e.SEVERITY_LVL_CD, e.ERROR_MSG, e.OVRD_IND
FROM   NNCTRL_NOM_DTL_ERR e
JOIN   NNCTRL_NOM_DTL     d  ON  d.NOM_SEQ_NO = e.NOM_SEQ_NO
                             AND d.TSP_NO     = e.TSP_NO
WHERE  e.FUNC_AREA_CD = 'NN'
  AND  e.VALD_RULE_CD IN ('NN00003115','NN00009601','NN00009602',
                          'NN00009603','NN00009604','NN00009605')
  AND  d.BEG_GAS_DAY = '2026-08-22'
ORDER BY e.VALD_RULE_CD;
```

```sql
-- Binds validation code -> .NET class from metadata, which closes the
-- rule-identity gap (see §9 item 2) without needing nomination data.
-- CLASS_NM for NN00009604 should resolve to RuleNN00009604;
-- VALD_RULE_DESCR should read "LOAN NOMINATION CAN'T EXCEED OVERALL BALANCE.";
-- MSG_TITLE_CD should be NNVALD9604.
SELECT vr.VALD_RULE_CD, vr.VALD_RULE_DESCR, vr.VALD_RULE_TYPE_CD,
       vr.MSG_TITLE_CD, vr.NAESB_CD, vr.CONFIGURABLE_IND,
       vr.ASSEMBLY_NM, vr.CLASS_NM
FROM   QCTRL_VALD_RULE vr
WHERE  vr.FUNC_AREA_CD = 'NN'
  AND  vr.VALD_RULE_CD IN ('NN00003115','NN00009602','NN00009604','NN00009605')
ORDER BY vr.VALD_RULE_CD;
```

## 7. Related Items

**An ADO bug for this case already exists. Do not open a duplicate.**

| WI | Title | State | Fixed in |
|---|---|---|---|
| **1863858** | `HPE - 26-01120642 PNGTS - Validation NN00009604 fires with an impossible limit of -1 or 0 DTH when a PAL Loan nomination falls outside the withdrawal action window` | **New**, unassigned, no PR, no child dev task | — (unfixed) |
| 1712405 | `25-00999987 - HPE - Nomination Validation Rule Not Resolving Inventory Account - NN00009602` | Closed, QA-approved | **2023.04.1.19; 2024.04.1.28; 2024.10.1.2; 2025.04.1.0; 2025.10.1.0** — CONFIRMED |
| 1718436 | child DEV task of 1712405 | Closed 2025-04-21 | as above |
| 1716619 | `HPE - 25-01007318 - …Loan Transactions as a Negative Balance - NN00009602` | Closed 2025-03-11 | as above |
| 180934 / 181180 | TEP 103717 PAL Service Min & Max (changeset 71495, *"PALS Min and Max additions to include time range in which noms can be submitted"*) | — | **origin of the `-1` sentinel** |
| 1854735 | `HPE - CWX06 Contract Brief PAL Showing Incorrect Qty` (SF 26-01113115) | New, L4-Investigated | may share the `foreach`-takes-last root below |

**The 1712405 fix is very likely already in the client's build — INFERRED, not confirmed.** It shipped via PR **108225**, branch `feature/RuleNN00009602_OIA_Change`, merged to `develop` 2025-04-08, commit `9ef10f5f`, with `ReleaseVersion = 2023.04.1.19; 2024.04.1.28; 2024.10.1.2; 2025.04.1.0; 2025.10.1.0`.

The inference gap: WI 1863858 records `FoundinVersion = 2025.10`, but **`2025.10` is not the same string as `2025.10.1.0`** — it is a release line, not a build. If the client is on any `2025.10.x` build at or above `2025.10.1.0`, the fix is present. Confirm the exact installed build before treating this as settled. Either way, do not re-file 1712405 and do not re-touch OIA resolution as part of this case.

1863858 fields verified directly: `State = New`, created 2026-08-21, `AreaPath = Quorum\North America\Midstream\Maintenance`, `Custom.SalesforceCase = 26-01120642`, `Custom.FoundinVersion = 2025.10`, `FoundInEnvironment = Production`.

**Action needed on 1863858:** it is unassigned with no dev task 3 weeks after creation, on a High-priority production case. It needs prioritisation, not re-filing. It is also scoped **only to `NN00009604`** — see the latent risks below.

**Port-back scope.** The fix lands on `develop`; the client is on 2025.10. Expect the usual release-branch cherry-picks — PR 108225 for this same rule family required **five** (2023.04 / 2024.04 / 2024.10 / 2025.04 / 2025.10).

**Name to reconcile upstream (does not affect the code finding).** SF Account is `Lighthouse Midstream Services, LLC`; WI 1863858 has `QuorumCMMI.Customer = "Third Coast Midstream LLC"` with title prefix `HPE - … PNGTS`; the walkthrough says `Lighthouse - Third Coast Super Holdings, LLC`. Worth settling so the release note names the right entity.

### Latent risks found during this investigation (neither is in the walkthrough or any ADO item)

**(a) `RuleNN00009605:116` omits `nMaxCtrAggQ` from its own predicate — HYPOTHESIS, probably not a defect.**
`RuleNN00009605.cs:116` reads `if (0 < nEndBalCtrDiff || !IsNomInRange)`. `nMaxCtrAggQ` is computed at `:97`, negated at `:100`, sentinel-set at `:113` — and then absent from the comparison, replaced by a literal `0`.
I initially read this as "fires unconditionally for any positive injection quantity." **That was wrong.** It assumed `endBalQty >= 0`, which is false for this rule: `RuleNN00009605.cs:89` is `endBalQty = acctBalance.EndBalQty;` with **no `Math.Abs`** — unlike `9602:89` and `9603:87`, which both wrap it. On a LEND contract the inventory balance is negative, so `nEndBalCtrDiff = nQtyTowardsParkLoan + endBalQty` is not necessarily positive; a payback that exactly clears the balance gives `nEndBalCtrDiff = 0` → `0 < 0` false → silent.
Read that way the literal `0` is defensible **by design**: for loan payback the ceiling *is* what the shipper owes, so not referencing the contract's Max Aggregated Quantity is arguably correct. **Downgraded to HYPOTHESIS — do not escalate, do not report to the customer.** The only live question is whether the `|| !IsNomInRange` branch belongs there at all, which is the same question as the out-of-window hard-fail covered in §4.

**(b) Inventory state leaks across nominations in `9602`, `9604`, `9605`.**
`idInvAcct` and `endBalQty` are declared **outside** the `foreach (ActivityDetailDO nomination …)` loop and only conditionally reassigned inside it (`:79-82`, `:84-91`), with no `else`. A nomination whose contract has no inventory account or no monthly balance row is therefore evaluated against the **previous nomination's** balance. `RuleNN00009603.cs:73` (`endBalQty = 0;`) is the only one of the four that guards against this — that asymmetry is the evidence it is an oversight, not intent.

| Rule | `endBalQty` reset in loop | `idInvAcct` reset in loop |
|---|---|---|
| `RuleNN00009602` | **no** | no |
| `RuleNN00009603` | yes (`:73`) | no |
| `RuleNN00009604` | **no** | no |
| `RuleNN00009605` | **no** | no |

Not triggered by the single-row walkthrough repro, but live in any multi-row submission — which is how the scheduling team works. The 1712405 `"SYS"` default reduces how often the trigger occurs; it does not remove the leak. Untracked in ADO (searched; 0 hits).

**(c) Supporting-layer defects found while tracing the resolvers.**
- **Dead `else if` — `ContractCache.cs:1283-1287`.** Verified unreachable: `:1283` repeats `:1278`'s condition verbatim. Given `ValidationConstants.cs:46 msc_sPalBothActnCd = "BTH"` exists, it was almost certainly meant to be `else if (item.InjWdCode == Constants.ActionCodeBoth)`. **Caveat:** the follow-on claim that a `'BTH'` row would make every PAL nom hit the sentinel path is **HYPOTHESIS only** — the premise that `KCTRL_PAL_ACTN_DT_QTY.INJ_WD_CD` can hold `'BTH'` is unestablished. The only `BTH` producer found (`ContractCache.cs:2298-2329 GetPalActionCode`) *derives* it from `KCTRL_PAL_ISS_DEAL` first/second-action flow dates; it is computed, not stored. Query `INJ_WD_CD` distribution before repeating this to anyone.
- **`foreach`-takes-last — `ResolverMDQ.cs:832-856` (`GetAggHelper`).** No ordering, no `break`: a multi-amendment contract gets an arbitrary amendment's Max Agg Qty. The sibling `GetCtrDailyQtyHelper:861-882` carries an unanswered reviewer comment, `//BAT CODEREVIEW: this is looping, but returning the last value.  Is this logic correct?`. `GetMaxPdwq`/`GetMinPdwq` (`:800-808`) reuse it without filtering on `InjWdCode`, so withdrawal and injection limits resolve to the same row. Candidate root for WI 1854735.
- **Unchecked location dereference** — `recLoc`/`delLoc` used with no null check (`9602:76-77`, `9603:73-74`, `9604:76-77`, `9605:76-77`); `LocationCache.GetLocation` returns null on a cache miss → `NullReferenceException` inside `Validate`.
- **Duplicate inventory-account rows fail the lookup silently.** The *cache helper* `GetInventoryAccountHeaderByPrimaryCtrNoAndOIA` returns null unless exactly one row matches (`InventoryCache.cs:336-341`, `tempBL.Count != 1`) — so zero matches and two-or-more matches are indistinguishable. To be precise about attribution: the outer method `FindInvAcctIdTiedToContractByAndOIA` does **not** stop there — `InventoryManager.cs:124-143` falls back to child contracts via `INCTRL_ACCT_CTR` before giving up. The silent-null risk is real but sits in the helper, not the outer method.

**(d) Configuration contributor.** On LPNG242 the PAL/ISS action windows do not cover the gas days being nominated (WITHDRAWAL a single day, INJECTION a separate month). Correcting these removes the trigger for most of the noise but does **not** fix the defect — it recurs whenever a Loan nom legitimately falls outside a window, or when a contract has no withdrawal action row at all (`:71-74` takes the same sentinel path).

**(e) Open question for the client.** `FoundinVersion = 2025.10` on WI 1863858 is the version the defect was found in. Treat that as the working assumption for the client's build — it is consistent with the 1712405 release list — but confirm it directly before issuing upgrade guidance.

## 8. ADO Bug — update to existing item 1863858 (do not create new)

| Field | Value |
|---|---|
| Work Item | **1863858** (existing) |
| Type | Bug |
| Title | *(current title is accurate)* — consider widening to note the sibling rules |
| Area Path | `Quorum\North America\Midstream\Maintenance` |
| State | `New` → needs triage/assignment |
| Found in Version | 2025.10 |
| Customer / Case | Lighthouse Midstream Services (PNGTS) / 26-01120642 |
| Root Cause category | Logic error — invalid sentinel value substituted for configured limit |

**Comment to add:**

> L4 code trace complete. Root cause confirmed at `Quorum.QPTM.Web` / `/Quorum.QPTM.Validations.Rules.Nomination/BusinessRules/RuleNN00009604.cs` @ `develop` `4a43ed28a99670e7a0e2342c55641605c1ddd72f`.
>
> `:111-114` substitutes `nMaxCtrAggQ = -1` when `IsNomInRange` is false, discarding the configured Max Aggregated Quantity. `-1` is not a valid negated Max AQ under the loan sign convention, so `:116` (`-1 > -15,000`) always fires and `:123` (`if (nMaxAvailable > 0)`) does not clamp it, putting `-1` on screen via `:128`.
>
> Worse: `GetMaxAggPAL` (`ResolverMDQ.cs:832-856` → `KCTRL_PAL_ISS_DEAL.MAX_AGGREGATED_QTY`, `PalIssDealDO.cs:2696` `CanBeNull=true`) returns **null**, not 0, when no PAL/ISS row matches. The sentinel therefore **flips `.HasValue` from false to true**, defeating the null guard on `:116` in precisely the case it exists to cover. In-window + null → rule silently passes; out-of-window + null → rule fires with an impossible ceiling.
>
> Also note `IsNomInRange` conflates two different date gates: `GetPalActionQty` (`ContractCache.cs:1252-1269`) filters on `KCTRL_PAL_ACTN_DT_QTY.BEG_FLOW_DT`/`END_FLOW_DT`, then `:62` re-checks `EFF_DT_FROM`/`EFF_DT_TO`. Four distinct columns; the scheduler cannot tell which gate rejected the nom.
>
> Note for the implementer: the walkthrough doc attributes this to the `:123` clamp being sign-mirrored from `NN00009602:121` and implies flipping it to `< 0`. That is incorrect — under the loan convention `nMaxAvailable` is legitimately negative and flipping the clamp would zero out every genuine remaining-capacity figure. The fault is the sentinel at `:113`.
>
> **Proposed fix:** delete the `if (!IsNomInRange) { nMaxCtrAggQ = -1; }` block at `:111-114`. Out-of-window noms are then judged against the real ceiling; in the reported scenario `-15,000 > -15,000` is false so the rule goes silent and `NN00003115` alone reports the window mismatch. Confirm the null-return behaviour of `ResolverMdq.GetMaxAggPAL` first — if it returns null for contracts with no PAL row, this rule will stop firing where the sentinel previously forced a failure (believed correct, needs product sign-off).
>
> **Do NOT flip the `:123` clamp.** `9602` and `9604` run in different sign conventions — `9602:89` wraps the balance in `Math.Abs`, `9604:89` does not, and `9604:100` negates the ceiling. In a genuine in-window breach `nMaxAvailable` is legitimately negative and encodes real remaining capacity; flipping the clamp to `< 0` would zero out every valid loan figure. Separately, `:127` flips `nQtyTowardsParkLoan` for display but `nMaxAvailable` gets no equivalent flip before `:128` — the display defect is a *missing* sign flip.
>
> **Scope widening — each sibling needs a DIFFERENT edit, not the same one.** Only `RuleNN00009602.cs:109-112` is a true analogue (delete the sentinel). `RuleNN00009603` has **no `nMaxCtrAggQ` at all** — its out-of-window hard-fail is the `|| !IsNomInRange` term in `:105`. `RuleNN00009605:116` is `if (0 < nEndBalCtrDiff || !IsNomInRange)`, independent of the sentinel, so deleting the sentinel there fixes nothing. See the table in the L4 doc §4.
>
> **One further defect found in the same files, not currently tracked:** `idInvAcct` / `endBalQty` are declared outside the per-nomination loop in 9602/9604/9605 with no per-iteration reset, so a nomination with no inventory account or no monthly balance row inherits the previous nomination's values. `RuleNN00009603.cs:73` is the only sibling that resets `endBalQty`; none reset `idInvAcct`.
>
> **Withdrawn:** an earlier read of `RuleNN00009605:116` as "fires unconditionally" was wrong — it assumed `endBalQty >= 0`, but `9605:89` has no `Math.Abs`, so on a LEND contract the balance is negative and the rule can legitimately stay silent. Treat that as a design question, not a bug.
>
> **Gate before shipping:** removing the sentinel makes the 96xx rules fail-open for out-of-window noms, which is only safe if `NN00003115` is wired to the client's TOS/TSP. Confirm rows exist in `NNXREF_VALD_RULE_GRP_EFF_RULE` for `VALD_RULE_CD = 'NN00003115'` at the PNGTS `TSP_NO` first.
>
> **Regression test:** multi-row Loan submission where row 1 resolves an inventory account with a non-zero balance and row 2 does not — assert row 2's `MAX_CTR_QTY` is not derived from row 1.
>
> **Message text note:** `NNVALD9602` and `NNVALD9604` are byte-identical strings in `Quorum.QPTM.Metadata:/STANDARD 16.0/QARCH_CODE_MSG_TITLE.json`, as are `NNVALD9603`/`NNVALD9605`. Any message rewording must be applied per-code across the Quorum, ONG and per-client metadata repos.

**Release Note (draft, customer-plain):** Corrected a validation message on Park-and-Loan nominations. When a nomination was entered for a gas day outside the contract's configured action window, the system reported an impossible maximum quantity instead of the contract's actual aggregated quantity limit. The out-of-window condition continues to be reported by the existing daily-quantity and action-code validation. Contract data, inventory balances and scheduled quantities were never affected.

## 9. Evidence limits — read before quoting this to anyone

This investigation passed an adversarial verification pass on its second iteration. The code-level root cause in §3 is **CONFIRMED** — every line number was re-verified by direct numbered read, and the arithmetic was independently recomputed. The following gaps remain and are deliberately not papered over:

1. **No database was read.** All three metadata MCP servers (`metadata`, `quorum-metadata-sql`, `quorum-metadata-oracle`) failed to connect. Every SQL statement in §6 and `verification_sql.md` is `NOT YET RUN`. **No PRD data state is asserted as fact anywhere in this document.**
2. **The rule identity is corroborated but not DB-proven.** That `NN00009604` is the rule the customer is hitting rests on two independent sources — the walkthrough doc authored by a Quorum engineer, and the title and description of ADO 1863858, which is filed against this exact Salesforce case with that repro. It does **not** rest on a `NNCTRL_NOM_ERROR` read. §6's first query is what would close this.
3. **The customer's own error screenshot was never opened.** Attachment `069UH00000t2taGYAQ` ("PNGTS - Validation Error") is on the case; the Salesforce connector exposes no file-download tool and no local copy exists. So the link between the customer's *reported* failure and the `-1 DTH` message reproduced in the walkthrough is **inferential**. This is the cheapest remaining verification available and needs no database — open that attachment before sending anything to the customer.
4. **Three other attachments unread** for the same reason: `PAL Contracts.xlsx` (the ACTV_NO query the customer ran, which would identify exactly which contracts and gas days are affected), `NominationSubmissionPTPathView.xlsx`, and `Case Analysis - 26-01120642.html` (a prior automated analysis dated 2026-08-13).
5. **The quoted message strings are metadata-anchored, not screen-captured.** The `NNVALD960x` / `NNVALD3115` texts in §1 and evidence E1/E10 come from `QARCH_CODE_MSG_TITLE.json` in the metadata repo, read by a subagent via ADO. The `NN00003115` string in §1 is the version quoted in the walkthrough/ADO repro, which **differs from the shipped baseline** — the client's metadata row is overridden. Treat the customer-visible wording as INFERRED for that rule.
6. **The `BTH` hypothesis is unverified and its premise is unestablished** — see §7(c). Do not repeat it to the customer or to engineering without running the `INJ_WD_CD` distribution query.
7. **`KTRAN_PAL_ISS_NET_QTY`** (the PDIQ source for `NN00003115`) is anchored only to a code comment at `ResolverMDQ.cs:892`, not a `[Table]` attribute — INFERRED.
8. **The client's exact installed build is unconfirmed** — see §7.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
