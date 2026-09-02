# L4 Triaged — Case 26-01094568

| | |
|---|---|
| **Salesforce Case** | 26-01094568 |
| **Client** | Inter Pipeline Ltd. (client code **IPF**, Canadian — GJ units) |
| **Contact** | Alla Ovcharenko · walkthrough by Bailey Coates (Quorum) |
| **Product / Module** | TIPS / Reporting — **Settlement Statement** (`SETTLEMENTSTATEMENT.RPT`, RPT_ID 43154) |
| **Environment** | IPF_HD_DEVA1 (repro); also reproduces in current Production **and** the upgrade build (client is in project mode) |
| **Plant / Period** | Plant **CEP** · **May-2025 accounting / April-2025 production** (acct ≠ prod ⇒ adjustment/PPA records) |
| **Affected contracts** | Access Gas **1103**, Ovintiv **1027**, PG&E **1033**, Portland General Electric **1011 / 1116 / 1154**, Puget **1095** |
| **Priority** | Medium |
| **Classification** | **Software Defect — confirmed at code level** (client-specific IPF report view). NOT data, NOT configuration, NOT working-as-designed. |
| **L4 / Date** | Aditya Bhagat · 2026-06-29 (all symbols & ADO facts re-verified against live source before Engineering transfer) |

---

## 1. Issue Summary

On IPF's **Settlement Statement**, the **volume (GJ) and dollar value are doubled** for five shippers in the April-2025 settlement, while the **unit rate is correct**. Because the dollar value is rate × volume, the value doubles purely as a consequence of the doubled volume (customer's note on Ovintiv #1027: *"price is right, vol is doubled, therefore price × vol is wrong as vol is wrong"*).

The doubling is in the **report's data view, not the settlement data**. The customer verified that the values in the **database, Query Suite, and the Calculation Summary screen are all correct** (exactly half of what the report shows). No settlement needs to be re-run; the underlying volumes, rates, and amounts are right.

Only contracts whose April settlement was **revised** are affected — that is the common thread across the five shippers.

---

## 2. Reproduction (from client walkthrough — IPF_HD_DEVA1)

1. Ensure the **Monthly Settle job** has run on the Facility Batch Job Submittal screen.
2. Use **May 2025 accounting / April 2025 production**, plant **CEP** (already run in DEV).
3. Go to **Reports** → run the **Settlement Statement** with those parameters.
4. Compare against the **Settlement Calculation** screen (or Query Suite) for each contract on the same dates.

**Observed:** the report's GJ and $ are ~2× the Calculation Summary / Query Suite / DB values for the five affected contracts; the unit rate matches. Contracts without a revision in the period report correctly.

Attachment on case: *"Walkthrough – IPF Doubling GJ's – Settlement Statement"* (Bailey Coates), the five shipper settlement PDFs, and the package PDF.

---

## 3. Root Cause (code level)

**Report:** `SETTLEMENTSTATEMENT.RPT` (RPT_ID 43154, `CONNECTION_ID QIPFDataHelper`) — repo **IPF.TIPS.Reports**. The report has **no report-level joins**; its data source is a single view and the first/summary page totals are Crystal `Sum(...)` group aggregates over that view's rows (`Sum({…APPLIED_VOL_HV_PR},{PROD_CD})`, `Sum({…VALUE_PR},{PROD_CD})`).

**Defect view:** **`QRPTS_SETTLEMENT_STMT_VW`** (non-posted) and its posted-mode mirror **`QPOST_RPTS_SETTLEMENT_STMT_VW`** — repo **IPF.TIPS.Database**, branch develop. `QRPTS_SETTLEMENT_STMT_VW` is built from **two** CTEs — `TRANSACTIONS` (current, from `QTRAN_*`) and `POSTED` (prior, from `QPOST_*`) — joined in its final SELECT as `CURRENT_TRANSACTIONS LEFT JOIN POSTED_TRANSACTIONS` (**L452–453**). The mirror `QPOST_RPTS_SETTLEMENT_STMT_VW` has a **single** `POSTED` CTE (from `QPOST_*`, GROUP BY **L168**, closes **L193**) that its final SELECT self-joins for the same current-vs-previous columns. Both return only adjustment rows (`WHERE … ACCT_DT <> PROD_DT`; QRPTS **L471**).

**The doubling mechanism (line numbers per `QRPTS_SETTLEMENT_STMT_VW.sql` @ develop):**

- The product join keeps **both** revision rows:
  `INNER JOIN QTRAN_SETTLE_PROD AS PROD ON PROD.TRNX_ID = S.TRNX_ID AND PROD.MTR_SFX = S.MTR_SFX AND PROD.REC_STATUS_CD IN ('CO','OR')` (**L68–71**). `OR` = original, `CO` = corrected. The `POSTED` CTE has the identical join over `QPOST_SETTLE_PROD` (**L257–260**).
- `REC_STATUS_CD` is **not** in the `GROUP BY` (QRPTS `TRANSACTIONS` CTE **L168**, `POSTED` CTE **L357**; mirror view **L168**), so for a revised product the `OR` and `CO` rows collapse into **one** group.
- The GJ and $ columns are **`SUM`**, so they add both revisions → **exactly 2×**:
  - `SUM(… PROD.APPLIED_VOL_HV_PR …) AS APPLIED_VOL_HV_PR` (**L34**)
  - `SUM(… PROD.VALUE_PR …) AS VALUE_PR` (**L36**)
- The unit rate is **`AVG`**, so the average of two near-identical rates is **unchanged** — this is exactly why the rate stays correct while GJ/$ double:
  - `AVG(… PROD.APPLIED_PRICE …) AS APPLIED_PRICE` (**L35**)
- The settlement totals are **`MAX`** off `QTRAN_SETTLE_SUMMARY` (`S`), so they pick a single value and are **immune** to the fan-out — which is why the stored net total is right but the summed statement lines double:
  - `MAX(S.TOT_VALUE_PR)`, `MAX(S.TOT_NET_VALUE_PR)`, `MAX(S.TOT_LIQ_VALUE_PR)` (**L39–43**)

Crystal then re-sums these already-doubled view rows on the first/summary page → the page shows 2× GJ and 2× $.

**$ figure breakdown (report formula):** the dollar amount on the page is `currentFee = {VALUE_PR} + {MOB_VALUE_PR} + {MBF_VALUE_PR} + {FIXED_FEE}`. Three of the four terms are `SUM` columns and therefore double — `VALUE_PR` (**L36**), `MOB_VALUE_PR` (**L48**), `MBF_VALUE_PR` (**L51**) — while `FIXED_FEE` is `MAX(COALESCE(FIXED_FEE.TOT_FEES_DEDUCTED,0))` (**L56**) and does **not** double. So the $ is overstated only on its volume-priced portion: `displayed $ = 2 × (VALUE_PR + MOB_VALUE_PR + MBF_VALUE_PR) + 1 × FIXED_FEE`. For a contract carrying a fixed facility fee the displayed total is therefore *less than* an exact 2× — expected, not a separate defect. The dedup fix corrects all three `SUM` terms (and the GJ) at once; `FIXED_FEE` is already correct.

**Why only the five shippers:** only their April settlement was revised, so only they carry two product rows (`OR` + `CO`) per line. Single-revision contracts have one row → `SUM` of one → correct.

**Confirmed three independent ways:** (1) the view DDL itself (above); (2) the customer's "rate right / volume doubled / DB & Query Suite & Calc Summary at half"; (3) the `AVG`-rate-unchanged-vs-`SUM`-volume-doubled split matches the walkthrough exactly.

---

## 4. Suggested Fix (ranked)

> View-only change in **IPF.TIPS.Database** (client-specific). **No Crystal change, no data fix** — the underlying settlement values are correct. Ships as an IPF client patch. Line numbers per develop; **re-baseline against the client's build branch before coding.**

**`REC_STATUS_CD` semantics — confirmed from code:** `OR` = Original, `CO` = Corrected, and **`CO` supersedes `OR`** (take-one). Evidence: TIPS settlement batch writes `Original` by default and a distinct `Corrected` row on revision (`QCostRecovery.cs`, `DerivedBatchVolumesApplication.cs`); the allocation split logic (`ContractSplitAllocationMethod.cs`) treats `Corrected` as a keyed *replacement* of `Original`; and the view's `MAX(S.TOT_*)` totals already take one revision and match the customer's correct (half) values. No additive-delta path exists. So: keep `CO`; keep `OR` only when there is no `CO` for that product line.

### Recommended — suppress the superseded `OR` via correlated `NOT EXISTS`

Chosen over a window function on **house-style** grounds: there are **zero `ROW_NUMBER()`/`OVER()` window functions anywhere** in the IPF/base TIPS view DDL, whereas correlated subqueries are the established idiom (used 7× in the sibling `…_FEE_VW`, 67× across the codebase, and in *this* view's own current-vs-posted self-join). Smallest diff against the in-flight sibling PR, and it is also **safer** than `ROW_NUMBER`-to-one — it removes *only* superseded `OR` rows and leaves every other row intact (see the `UNIT_TM_CD` risk below).

```sql
-- TRANSACTIONS CTE, L68–71 (use QPOST_SETTLE_PROD at the QPOST sites)
INNER JOIN QTRAN_SETTLE_PROD AS PROD
    ON  PROD.TRNX_ID = S.TRNX_ID
    AND PROD.MTR_SFX = S.MTR_SFX
    AND PROD.REC_STATUS_CD IN ('CO','OR')
    AND ( PROD.REC_STATUS_CD = 'CO'
          OR NOT EXISTS ( SELECT 1 FROM QTRAN_SETTLE_PROD CO
                          WHERE CO.TRNX_ID = PROD.TRNX_ID
                            AND CO.MTR_SFX = PROD.MTR_SFX
                            AND CO.PROD_CD = PROD.PROD_CD   -- MUST include PROD_CD + DISP_CD
                            AND CO.DISP_CD = PROD.DISP_CD   -- (the supersede unit is the product line)
                            AND CO.REC_STATUS_CD = 'CO' ) )
```

⚠️ **The correlation key MUST include `PROD_CD` and `DISP_CD`** (not just `TRNX_ID`/`MTR_SFX`) — otherwise a *partially* revised settlement (only some product lines got a `CO` row) would wrongly drop the still-valid `OR` lines. (Adding `QTY_UOM_CD` too is harmless and matches the GROUP BY grain.)

### Alternative — `ROW_NUMBER()` dedup (functionally equivalent; rejected only on house-style/merge-risk)
```sql
INNER JOIN (
    SELECT *, ROW_NUMBER() OVER (
                 PARTITION BY TRNX_ID, MTR_SFX, PROD_CD, DISP_CD, QTY_UOM_CD   -- include QTY_UOM_CD = GROUP BY grain
                 ORDER BY CASE REC_STATUS_CD WHEN 'CO' THEN 0 ELSE 1 END,
                          RUN_ID DESC, ACCT_DT DESC ) AS RN                     -- deterministic tiebreaker
    FROM QTRAN_SETTLE_PROD WHERE REC_STATUS_CD IN ('CO','OR')
) AS PROD ON PROD.TRNX_ID = S.TRNX_ID AND PROD.MTR_SFX = S.MTR_SFX AND PROD.RN = 1
```

After the fix: `SUM` over the single surviving revision = the true volume/value; `AVG` rate and `MAX` totals unchanged → all three figures tie to Query Suite / Calculation Summary.

### Apply at exactly **3** PROD-join sites (the posted mirror has only ONE CTE — there is no 4th)

| File | CTE | Table | Join @ |
|---|---|---|---|
| `QRPTS_SETTLEMENT_STMT_VW.sql` | `TRANSACTIONS` | `QTRAN_SETTLE_PROD` | **L68–71** |
| `QRPTS_SETTLEMENT_STMT_VW.sql` | `POSTED` | `QPOST_SETTLE_PROD` | **L257–260** |
| `QPOST_RPTS_SETTLEMENT_STMT_VW.sql` | `POSTED` (sole CTE) | `QPOST_SETTLE_PROD` | **L68–71** |

> **Do NOT touch the FEE views** (`QRPTS_/QPOST_RPTS_SETTLEMENT_STMT_FEE_VW`): they already keep `F.REC_STATUS_CD` in the `GROUP BY` (L69 / L131), so `OR`/`CO` fees fall into separate groups and are **not** summed — they don't have this bug, and deduping them would change correct behaviour.

### Pre-ship checks (DBA — live DB unreachable from L4; see diagnostic #1)
- Confirm `QTRAN_SETTLE_PROD` holds at most one `OR` + one `CO` per `(TRNX_ID, MTR_SFX, PROD_CD, DISP_CD, QTY_UOM_CD)` for the affected period, and is **not** also storing daily (`UNIT_TM_CD='D'`) rows for the same key — the view filters `UNIT_TM_CD='M'` only on the summary table `S` (L161), **not** on `PROD`. If daily rows can appear, add `AND PROD.UNIT_TM_CD='M'` to the join.
- **Rebase on develop:** sibling PR **#126604 is already merged** (it swapped `QCODE_TOS`→`QCODE_SERVICE_CLASS` in these two views, 2026‑04‑20). Branch from **current develop**, not the cached DDL, and wrap whatever the product join looks like post-merge.

### Why not just add `REC_STATUS_CD` to the `GROUP BY`
That splits the revised product into two output lines (one per status) instead of collapsing to the final value — duplicate lines instead of a doubled total. Suppress-the-superseded-`OR` is the correct shape.

**Recommendation:** ship the `NOT EXISTS` fix at the 3 sites. Lowest risk, encodes the supersede rule directly, matches house conventions, and aligns the breakdown with the already-correct `MAX` totals.

---

## 5. Expected Result After Fix

Re-running the walkthrough (plant CEP, May-2025 acct / April-2025 prod) produces a Settlement Statement whose GJ, rate, and $ for the five contracts **tie to the Calculation Summary / Query Suite / DB values** (i.e. the previously doubled figures halve to the correct single-revision value). Non-revised contracts are unchanged.

---

## 6. Diagnostic SQL (run in the IPF client DB — confirms signature before logging to dev)

```sql
-- 1. KEY CHECK: do OR and CO coexist per product for the doubling shippers? (drives the fix)
SELECT P.TRNX_ID, P.MTR_SFX, P.PROD_CD, P.DISP_CD,
       COUNT(*)                                          AS TOTAL_ROWS,
       SUM(CASE WHEN P.REC_STATUS_CD='OR' THEN 1 ELSE 0 END) AS OR_ROWS,
       SUM(CASE WHEN P.REC_STATUS_CD='CO' THEN 1 ELSE 0 END) AS CO_ROWS,
       SUM(P.VALUE_PR) AS VALUE_SUM, MAX(P.VALUE_PR) AS VALUE_MAX
FROM   QTRAN_SETTLE_PROD P
JOIN   QTRAN_PAYSTATION  PS ON PS.TRNX_ID = P.TRNX_ID AND PS.MTR_SFX = P.MTR_SFX
WHERE  PS.RUN_ID = <april_2025_CEP_settlement_run_id>
  AND  P.REC_STATUS_CD IN ('CO','OR')
GROUP BY P.TRNX_ID, P.MTR_SFX, P.PROD_CD, P.DISP_CD
HAVING COUNT(*) > 1            -- rows here = product summed across >1 revision = the doubling set
ORDER BY P.TRNX_ID, P.PROD_CD, P.DISP_CD;

-- 2. Prove the view already doubles: SUM (what the report adds) vs MAX-based total (authoritative). ratio ~2.0 = doubled.
SELECT v.CTR_PARTY_NM, v.CTR_NO, v.ACCT_DT,
       MAX(v.REVISION_COUNT)    AS revision_count,
       MAX(v.TOT_VALUE_PR)      AS stored_total_value,       -- authoritative ($)
       SUM(v.VALUE_PR)          AS statement_summed_value,   -- what the report sums ($)
       SUM(v.APPLIED_VOL_HV_PR) AS statement_summed_gj,
       CASE WHEN MAX(v.TOT_VALUE_PR)=0 THEN NULL
            ELSE SUM(v.VALUE_PR)/NULLIF(MAX(v.TOT_VALUE_PR),0) END AS ratio
FROM   QRPTS_SETTLEMENT_STMT_VW v
WHERE  v.ACCT_DT = '2025-05-01' AND v.PROD_DT = '2025-04-01'   -- adjust to the sample PDFs
GROUP BY v.CTR_PARTY_NM, v.CTR_NO, v.ACCT_DT
ORDER BY ratio DESC;
-- Five affected shippers ≈ 2.0 with revision_count > 0; the rest ≈ 1.0 → confirms doubling AND the revision trigger.
```

---

## 7. Related Items

- **No ADO work item tracks this doubling, and no fix exists or is in flight** — exhaustively verified, and re-confirmed live 2026-06-29 (WIQL on the case/view → 0 hits; #1787313 still *Acceptance*; PR #126604 *Completed*): WIQL/work-item search on the case #, view name, `REC_STATUS_CD`, and "Settlement Statement double/duplicate/revision" → 0 relevant hits; ADO code search for a borrowable `OR`/`CO` dedup in any client or base settlement view → none (base `Quorum.TIPS.Database` has no `SETTLEMENT_STMT_VW`; VMH's gas-statement proc scopes by `RUN_ID`, not transplantable). **The fix is net-new.**
- **Coordinate — sibling bug #1787313 / PR #126604 (already MERGED to develop 2026-04-20)** *"IPF - 26-01084662 - Settlement Report Package Differences"* (dev **Snehal Thorat**, area `QuorumSoftware\Engineering\Software Services\Professional Services`). PR #126604 swapped `QCODE_TOS`→`QCODE_SERVICE_CLASS` in **these same two views** but left the `PROD`/`REC_STATUS_CD` join byte-identical (doubling intact). **Branch from current develop (post-#126604), not the cached DDL**, to avoid a merge collision.
- The latest deployed script (`QTIP_17.0.00.0031.0000…_1799519.sql`) still has the unfixed PROD join with no `REC_STATUS_CD` in `GROUP BY` → defect fully present in the current build.
- **Latent fan-out hardening (not firing for these 5 contracts, but real):** three BA-level joins in the same view carry multi-value columns in the `GROUP BY` and could double for a *different* shipper — `SCTRL_BA_TAX_ID` (joined on `BA_NO` only, no `BA_SUF`, no `TAX_ID_TYPE_CD` filter), `QCTRL_BA_ADDRESS_VW` (`BA_NO`+`BA_SUF`), and `SCTRL_BA_CONTACTINFO_VW` (`CREP`/`PRIMARY_IND=1`). The 5 affected contracts show a clean exact-2× (single revision), so these aren't contributing here, but a hardening pass (add `BA_SUF` + a `TAX_ID_TYPE_CD` predicate to the tax join, or pre-aggregate these lookups) would prevent a future "doubling" for a shipper with >1 tax-id/address/primary contact.
- **Secondary latent gap (separate report, not this case):** `QRPTS_SETTLEMENT_SUM_VW` (used by `SettlementSummary.RPT`) has product joins with **no `REC_STATUS_CD` filter** and no `GROUP BY` — could fan out similarly. Same in `QPOST_RPTS_SETTLEMENT_SUM_VW`. Fix only if that report is also reported wrong.
- **Internal analog:** DFCT-1566 (#1646230) — a settlement-statement doubling traced to the report/view side (different customer; same defect family).

**Suggested ADO bug title:**
`IPF - 26-01094568 - Settlement Statement (RPT_43154) doubles GJ & $ for revised settlements — QRPTS/QPOST_RPTS_SETTLEMENT_STMT_VW SUMs both OR and CO revision rows`

---

## 8. ADO Bug — ready to paste (Engineering handoff)

| Field | Value |
|---|---|
| **Work Item Type** | Bug |
| **Title** | IPF - 26-01094568 - Settlement Statement (RPT_43154) doubles GJ & $ for revised settlements (SUMs both OR and CO revision rows) |
| **Area Path** | QuorumSoftware\Engineering\Software Services\Professional Services *(match sibling #1787313)* |
| **Product / Module** | TIPS / Reporting — Settlement Statement |
| **Severity / Priority** | 3 - Medium / 3 |
| **Found in Version** | Current IPF build **and** the upgrade build (17.0.x) — confirm exact client build; defect present in `QTIP_17.0.00.0031…_1799519.sql` |
| **Customer** | Inter Pipeline Ltd. (IPF) |
| **Salesforce Case** | 26-01094568 |
| **Root Cause (category)** | Code Defect — report view sums across settlement revisions (no per-product dedup) |

**Repro Steps** (IPF_HD_DEVA1; plant **CEP**, May-2025 accounting / April-2025 production):
1. Ensure the Monthly Settle job has run for the period.
2. Run the **Settlement Statement** report for those parameters.
3. Compare report GJ/$ against the **Settlement Calculation** screen / Query Suite for the affected contracts.

**Expected:** report GJ, rate, and $ tie to the Calculation Summary / Query Suite / DB values.
**Actual:** GJ and $ are ~2× for Access Gas (1103), Ovintiv (1027), PG&E (1033), Portland General Electric (1011/1116/1154), Puget (1095); the unit rate is correct. DB / Query Suite / Calculation Summary show the correct (half) values — data is right, the report over-sums.

**Root Cause:** `IPF.TIPS.Database` views `QRPTS_SETTLEMENT_STMT_VW` and posted-mode mirror `QPOST_RPTS_SETTLEMENT_STMT_VW` join `…SETTLE_PROD` with `REC_STATUS_CD IN ('CO','OR')` (L68–71; POSTED CTE L257–260) but do not include `REC_STATUS_CD` in the `GROUP BY` (L168). For a revised product the original (`OR`) and corrected (`CO`) rows collapse into one group, so the per-product `SUM(APPLIED_VOL_HV_PR)` (L34) and `SUM(VALUE_PR)` (L36) add both revisions → 2×. The rate uses `AVG` (L35) so it is unaffected; the settlement totals use `MAX(S.TOT_*)` (L39–43) so they remain correct, isolating the symptom to the summed GJ/$. Crystal re-sums the doubled rows on the first/summary page.

**Proposed Fix:** see §4 — suppress the superseded `OR` row when a `CO` exists for the same product line, via a correlated `NOT EXISTS` (preferred over a `ROW_NUMBER()` dedup on house-style grounds — these views contain no window functions). Apply at **exactly 3** product-join sites: `QRPTS_SETTLEMENT_STMT_VW` L68 (QTRAN) + L257 (QPOST), and `QPOST_RPTS_SETTLEMENT_STMT_VW` L68 (its sole CTE). **Do NOT** dedupe the FEE views — they already keep `REC_STATUS_CD` in the GROUP BY and are correct. View-only; no Crystal/data change. `CO`-supersedes-`OR` is confirmed from code (still verify against data). Rebase on develop — sibling PR #126604 (bug #1787313) already merged into these two views.

**Regression Risk:** Low, localized to two IPF report views. The dedup only suppresses the duplicate revision row; single-revision products (the majority) are unchanged. No change to Crystal, settlement data, or the `MAX`-based totals.

**Test / Verification:**
- Re-run the repro → report GJ/$ for the five contracts halve to the correct value and tie to Query Suite / Calculation Summary; rate unchanged.
- Positive: a contract with a single (non-revised) settlement is unchanged before/after.
- Posted-mode: run the report in posted mode (uses `QPOST_RPTS_SETTLEMENT_STMT_VW`) and confirm it also ties out.

**Release Note (draft):** *Corrected the IPF Settlement Statement so that, when a settlement has been revised, the report uses only the final (corrected) revision for each product. Previously both the original and corrected revisions were summed, doubling the GJ and dollar amounts on the statement (the unit rate and the stored settlement totals were unaffected).*

---

*Prepared by L4 (Aditya Bhagat). **Re-verified against live source 2026-06-29 prior to Engineering transfer** — all confirmed: QRPTS line numbers (`SUM` L34, `AVG` L35, `SUM` L36, `MAX` L39–43, `MOB_VALUE_PR` L48, `MBF_VALUE_PR` L51, `FIXED_FEE`/MAX L56, PROD join L68–71, `UNIT_TM_CD='M'` on S L161, GROUP BY L168, QPOST PROD join L257–260, POSTED GROUP BY L357, final join L452–453, `ACCT_DT<>PROD_DT` L471); QPOST mirror = single `POSTED` CTE, PROD join L68–71, GROUP BY L168 (incl. `QTY_UOM_CD` L191); FEE views keep `REC_STATUS_CD` in GROUP BY (L69/L131); SF case still **In Progress** (owner A. Bhagat); **no ADO work item** for the case/view; #1787313 **Acceptance** (area `…\Professional Services`); PR **#126604 Completed**, squash-merged to develop **2026-04-20** (`QCODE_TOS`→`QCODE_SERVICE_CLASS`, PROD join untouched). Re-baseline line numbers against the client build branch before coding. Full RCA history in `L4 investigation.md` (Case 26-01094568).*
