# Engineering Handoff — Case 26-01094568
## IPF (Inter Pipeline) — TIPS Settlement Statement doubles GJ & $ for revised settlements

**Self-contained transfer package for Engineering. Everything code- and query-side is below; no other document is required to action this.**

| | |
|---|---|
| **Salesforce Case** | 26-01094568 |
| **Client** | Inter Pipeline Ltd. (code **IPF**, Canadian — GJ units) |
| **Contact / Walkthrough author** | Alla Ovcharenko / Bailey Coates (Quorum) |
| **Product / Module** | TIPS / Reporting — Settlement Statement |
| **Report** | `SETTLEMENTSTATEMENT.RPT` (registry **RPT_ID 43154**, `CONNECTION_ID QIPFDataHelper`), repo **IPF.TIPS.Reports** |
| **Defect location** | DB views in **IPF.TIPS.Database** (NOT the Crystal report) |
| **Environment** | IPF_HD_DEVA1 (repro); also current Production + the upgrade build (client in project mode) |
| **Plant / Period** | Plant **CEP**; **May-2025 accounting / April-2025 production** (acct ≠ prod ⇒ adjustment/PPA rows) |
| **Affected contracts** | Access Gas **1103**, Ovintiv **1027**, PG&E **1033**, Portland General Electric **1011 / 1116 / 1154**, Puget **1095** |
| **Classification** | **Software Defect — confirmed at code level** (client-specific report view). Not data, not config, not WAD. |
| **Priority** | Medium |
| **Prepared by** | L4 (Aditya Bhagat) — re-verified against live source **2026-06-29** before transfer |

---

## 1. Symptom

On the Settlement Statement, for the affected contracts:
- **Volume (GJ) is doubled** (exact 2×).
- **Dollar value is doubled** — but only on its volume-priced portion (see §4).
- **Unit rate is correct.**
- The values in the **database, Query Suite, and the Calculation Summary screen are all correct** (= half the report). The underlying settlement is right; the report over-states.

Only contracts whose April-2025 settlement was **revised** are affected.

---

## 2. Object & file inventory

| Object | Repo | Path | Role |
|---|---|---|---|
| `QRPTS_SETTLEMENT_STMT_VW` | IPF.TIPS.Database (`4faa286e-18b1-4126-b2a8-90fc109e8cac`) | `/Common/MSSQL/Views/QRPTS_SETTLEMENT_STMT_VW.sql` | **Defect** — non-posted data source (has `TRANSACTIONS` + `POSTED` CTEs) |
| `QPOST_RPTS_SETTLEMENT_STMT_VW` | IPF.TIPS.Database | `/Common/MSSQL/Views/QPOST_RPTS_SETTLEMENT_STMT_VW.sql` | **Defect** — posted-mode mirror (single `POSTED` CTE) |
| `QRPTS_SETTLEMENT_STMT_FEE_VW` | IPF.TIPS.Database | `/Common/MSSQL/Views/QRPTS_SETTLEMENT_STMT_FEE_VW.sql` | **Do NOT change** — already correct (groups by `REC_STATUS_CD`) |
| `QPOST_RPTS_SETTLEMENT_STMT_FEE_VW` | IPF.TIPS.Database | `/Common/MSSQL/Views/QPOST_RPTS_SETTLEMENT_STMT_FEE_VW.sql` | **Do NOT change** — same |
| `SETTLEMENTSTATEMENT.RPT` | IPF.TIPS.Reports (`d7bff4d5-2559-44cf-bb24-cf0f41d467c9`) | Crystal report (RPT_43154) | **No change** — sums the view faithfully |

> The latest deployed migration `…/FluentMigrator/EmbeddedScripts/MSSQL/ENGSCLIENT/QTIP_17.0.00.0031.0000_00_IPF_ENGSCLIENT_05_1799519.sql` still contains the unfixed view (deployed via DB-change WI #1799519). **Branch from current develop** — sibling PR #126604 (below) already merged into these views.

---

## 3. Root cause (view level)

Both views build per-product rows from `…SETTLE_PROD` and group them. The product join keeps **both** revision rows and the `GROUP BY` omits `REC_STATUS_CD`, so the two revisions collapse into one group and the `SUM` columns add together.

**Current join — `QRPTS_SETTLEMENT_STMT_VW`, `TRANSACTIONS` CTE (L68–71):**
```sql
INNER JOIN QTRAN_SETTLE_PROD AS PROD
       ON PROD.TRNX_ID = S.TRNX_ID
      AND PROD.MTR_SFX = S.MTR_SFX
      AND PROD.REC_STATUS_CD IN ('CO','OR')     -- keeps BOTH Corrected (CO) and Original (OR)
```

**Aggregation in the SELECT (same CTE):**
```sql
SUM(... PROD.APPLIED_VOL_HV_PR ...) AS APPLIED_VOL_HV_PR   -- L34  → SUM → DOUBLES
AVG(... PROD.APPLIED_PRICE ...)     AS APPLIED_PRICE       -- L35  → AVG → unchanged (avg of 2 equal rates)
SUM(... PROD.VALUE_PR ...)          AS VALUE_PR            -- L36  → SUM → DOUBLES
MAX(S.TOT_VALUE_PR) / MAX(S.TOT_NET_VALUE_PR) ...          -- L39–43 → MAX → unchanged (single revision)
```

**`GROUP BY` (L168–193)** keys on `PLANT_NM, PLANT_NO, ACCT_DT, PROD_DT, CTR_PARTY_BA_NO/SUF, CTR_NO, …, PROD_CD, DISP_CD, QTY_UOM_CD, …` — **`REC_STATUS_CD` is NOT a grouping key**, so the `OR` and `CO` rows fall into one group.

The `POSTED` CTE (L194–382) and the mirror view replicate this exactly (see §5 for the three sites).

**Net effect per figure** (this is why the rate looks right):

| Figure | View aggregation | Effect of OR+CO |
|---|---|---|
| Volume (GJ) `APPLIED_VOL_HV_PR` | `SUM` | **2×** |
| Unit rate `APPLIED_PRICE` | `AVG` | unchanged |
| Value `VALUE_PR`, `MOB_VALUE_PR`, `MBF_VALUE_PR` | `SUM` | **2×** |
| Fixed fee `FIXED_FEE` | `MAX` | unchanged |
| Settlement totals `TOT_*` | `MAX` | unchanged |

Only the 5 contracts whose April settlement was revised carry an `OR`+`CO` pair; single-revision contracts have one row (`SUM` of one) and are correct.

### The Crystal report is NOT at fault
The report has no report-level join; its summary figures are plain `Sum()` over the view rows, so they faithfully add the already-doubled rows:
- Volume: `Sum({QRPTS_SETTLEMENT_STMT_VW.APPLIED_VOL_HV_PR}, {PROD_CD})`
- Dollar: `currentFee = {VALUE_PR} + {MOB_VALUE_PR} + {MBF_VALUE_PR} + {FIXED_FEE}`, then `Sum({@currentFee}, {CTR_NO})`

The first three `currentFee` terms are `SUM` columns (double); `FIXED_FEE` is a `MAX` column (does not). So the dollar amount = `2 × (VALUE_PR + MOB_VALUE_PR + MBF_VALUE_PR) + 1 × FIXED_FEE` — a tested ratio slightly under 2.0 on a contract with a fixed fee is expected, not a second bug. **No `.rpt` change is required.**

---

## 4. `REC_STATUS_CD` semantics (confirmed from code)

`OR` = **Original**, `CO` = **Corrected**, and **`CO` supersedes `OR`** (take-one, not additive). Evidence:
- TIPS settlement batch writes `RecStatus.Original` by default and a **distinct** `Corrected` row on revision (`QCostRecovery.cs`, `DerivedBatchVolumesApplication.cs`).
- Allocation split logic (`ContractSplitAllocationMethod.cs`) branches on Original vs Corrected and treats Corrected as a **keyed replacement** of the original.
- The view's own `MAX(S.TOT_*)` totals already take **one** revision and match the customer's correct (half) values — if `OR`+`CO` were additive deltas, those totals would themselves be wrong, which the customer confirms they are not.

➡️ The fix keeps `CO`, and keeps `OR` only when no `CO` exists for that product line.

---

## 5. The fix (view-only; no Crystal, no data)

**Recommended shape: correlated `NOT EXISTS`** — chosen over a window function because these views contain **zero** `ROW_NUMBER()/OVER()` constructs, whereas correlated subqueries are the house idiom (the sibling FEE view at `QRPTS_SETTLEMENT_STMT_FEE_VW.sql` L52–61 already uses `NOT EXISTS (... QTRAN_SETTLE_PROD ...)`; this very view uses a correlated `MAX(ACCT_DT)` self-join). It is also safer than `ROW_NUMBER`-to-one — it removes *only* the superseded `OR` row and leaves all other rows intact.

> **Apply at exactly 3 product-join sites.** The posted mirror has a single CTE — there is no 4th site.

### Site 1 — `QRPTS_SETTLEMENT_STMT_VW.sql`, `TRANSACTIONS` CTE, L68–71 (`QTRAN_SETTLE_PROD`)

**BEFORE**
```sql
INNER JOIN QTRAN_SETTLE_PROD AS PROD
       ON PROD.TRNX_ID = S.TRNX_ID
      AND PROD.MTR_SFX = S.MTR_SFX
      AND PROD.REC_STATUS_CD IN ('CO','OR')
```
**AFTER**
```sql
INNER JOIN QTRAN_SETTLE_PROD AS PROD
       ON PROD.TRNX_ID = S.TRNX_ID
      AND PROD.MTR_SFX = S.MTR_SFX
      AND PROD.REC_STATUS_CD IN ('CO','OR')
      AND ( PROD.REC_STATUS_CD = 'CO'
            OR NOT EXISTS ( SELECT 1 FROM QTRAN_SETTLE_PROD CO
                            WHERE CO.TRNX_ID = PROD.TRNX_ID
                              AND CO.MTR_SFX = PROD.MTR_SFX
                              AND CO.PROD_CD  = PROD.PROD_CD     -- key MUST include PROD_CD + DISP_CD
                              AND CO.DISP_CD  = PROD.DISP_CD     -- (supersede unit = product line)
                              AND CO.REC_STATUS_CD = 'CO' ) )
```

### Site 2 — `QRPTS_SETTLEMENT_STMT_VW.sql`, `POSTED` CTE, L257–260 (`QPOST_SETTLE_PROD`)

**BEFORE**
```sql
INNER JOIN QPOST_SETTLE_PROD AS PROD
       ON PROD.TRNX_ID = S.TRNX_ID
      AND PROD.MTR_SFX = S.MTR_SFX
      AND PROD.REC_STATUS_CD IN ('CO','OR')
```
**AFTER** — identical NOT EXISTS, against `QPOST_SETTLE_PROD`:
```sql
INNER JOIN QPOST_SETTLE_PROD AS PROD
       ON PROD.TRNX_ID = S.TRNX_ID
      AND PROD.MTR_SFX = S.MTR_SFX
      AND PROD.REC_STATUS_CD IN ('CO','OR')
      AND ( PROD.REC_STATUS_CD = 'CO'
            OR NOT EXISTS ( SELECT 1 FROM QPOST_SETTLE_PROD CO
                            WHERE CO.TRNX_ID = PROD.TRNX_ID
                              AND CO.MTR_SFX = PROD.MTR_SFX
                              AND CO.PROD_CD  = PROD.PROD_CD
                              AND CO.DISP_CD  = PROD.DISP_CD
                              AND CO.REC_STATUS_CD = 'CO' ) )
```

### Site 3 — `QPOST_RPTS_SETTLEMENT_STMT_VW.sql`, sole `POSTED` CTE, L68–71 (`QPOST_SETTLE_PROD`)

Current text is byte-identical to Site 2's BEFORE; apply the **same** `QPOST_SETTLE_PROD` AFTER block.

### Alternative shape (functionally equivalent; rejected only on house-style/merge-risk)
```sql
INNER JOIN (
    SELECT *, ROW_NUMBER() OVER (
                 PARTITION BY TRNX_ID, MTR_SFX, PROD_CD, DISP_CD, QTY_UOM_CD   -- include QTY_UOM_CD = GROUP BY grain
                 ORDER BY CASE REC_STATUS_CD WHEN 'CO' THEN 0 ELSE 1 END,
                          RUN_ID DESC, ACCT_DT DESC ) AS RN                     -- deterministic tiebreaker
    FROM <QTRAN|QPOST>_SETTLE_PROD WHERE REC_STATUS_CD IN ('CO','OR')
) AS PROD ON PROD.TRNX_ID = S.TRNX_ID AND PROD.MTR_SFX = S.MTR_SFX AND PROD.RN = 1
```

---

## 6. What NOT to change

- **The Crystal report (`SETTLEMENTSTATEMENT.RPT`)** — its `Sum()` formulas are correct; they only reflect the doubled view rows.
- **The FEE views** (`QRPTS_/QPOST_RPTS_SETTLEMENT_STMT_FEE_VW`) — they already keep `F.REC_STATUS_CD` in the `GROUP BY` (`QRPTS_…_FEE_VW.sql` L69; `QPOST` L131), so `OR`/`CO` fees land in separate groups and are not summed. They do **not** have this bug; deduping them would change correct behaviour.
- **Settlement data** — `QTRAN_SETTLE_PROD` / `QPOST_SETTLE_PROD` `OR`+`CO` rows are valid history; no data fix, no settlement re-run.

---

## 6A. Repo file change-set — exactly which files to edit / add / leave alone

All in repo **IPF.TIPS.Database** (`4faa286e-18b1-4126-b2a8-90fc109e8cac`); **branch from current `develop`**. The file pattern below is verified against **PR #126604** (the last change to these same views), which touched the canonical view `.sql` files + one `EmbeddedScripts` ALTER script + one `OrderedMigrations` `.cs` class + the `.csproj`. The doubling fix mirrors that pattern (minus #126604's TOS-specific table/views).

### EDIT — canonical view source (the actual fix)
| # | File | Change |
|---|---|---|
| 1 | `/IPF.TIPS.Database/Common/MSSQL/Views/QRPTS_SETTLEMENT_STMT_VW.sql` | Add the `NOT EXISTS` suppression (§5) to the PROD join in **both** CTEs — `TRANSACTIONS` (QTRAN, **L68**) and `POSTED` (QPOST, **L257**). |
| 2 | `/IPF.TIPS.Database/Common/MSSQL/Views/QPOST_RPTS_SETTLEMENT_STMT_VW.sql` | Same `NOT EXISTS` on the PROD join in its single `POSTED` CTE (QPOST, **L68**). |

### ADD — FluentMigrator deployment (generate via `New-Migration.ps1`; do **not** hand-number)
| # | File | Purpose |
|---|---|---|
| 3 | `/IPF.TIPS.Database/FluentMigrator/EmbeddedScripts/MSSQL/ENGSCLIENT/QTIP_<nextBuild>_00_IPF_ENGSCLIENT_<seq>_<newWI>.sql` | The `ALTER VIEW` text for **both** fixed views, applied to the IPF **ENGSCLIENT** layer (= ESUITE_QIPF). Mirror of the prior `…_1799519.sql`. |
| 4 | `/IPF.TIPS.Database/FluentMigrator/OrderedMigrations/MSSQL/ENGSCLIENT/Migration_<YYYYMMDDHHMM>_<newWI>_ENGSCLIENT_MSSQL.cs` | The C# FluentMigrator class that runs #3 in order. Mirror of `Migration_202604201504_1799519_ENGSCLIENT_MSSQL.cs`. |

### EDIT — project registration
| # | File | Change |
|---|---|---|
| 5 | `/IPF.TIPS.Database/IPF.TIPS.Database.csproj` | Register the new `.sql` (#3) as an `EmbeddedResource` and the new migration `.cs` (#4) as a compile item. (`New-Migration.ps1` / `AddFluentMigratorScriptsForSingleWI.ps1` updates this automatically.) |

### DO NOT EDIT
- `Common/MSSQL/Views/QRPTS_SETTLEMENT_STMT_FEE_VW.sql` and `…/QPOST_RPTS_SETTLEMENT_STMT_FEE_VW.sql` — already correct (group by `REC_STATUS_CD`).
- `Common/MSSQL/Views/QRPTS_SETTLEMENT_SUM_VW.sql` and `…/QPOST_RPTS_SETTLEMENT_SUM_VW.sql` — different report (`SettlementSummary.RPT`); only if that report is also reported wrong.
- `SETTLEMENTSTATEMENT.RPT` (repo **IPF.TIPS.Reports**) — the Crystal report is correct; no change.
- The existing `…_1799519.sql` embedded script and `Migration_202604201504_1799519_ENGSCLIENT_MSSQL.cs` — shipped migrations are immutable; never edit, always add a new one.

### Notes
- **Target layer = ENGSCLIENT only** for these views (per PR #126604 / WI 1799519). The other layer folders (`QTIP`, `QTIPCAN`, `CAWQTIP`, `ARCVQTIP`, `QFCQTIP`, `TIPS`) are not used by the IPF settlement report.
- **Build/sequence number:** do not hardcode — the prior settlement-view deploy was `QTIP_17.0.00.0031.0000`, and several builds have shipped since (latest ENGSCLIENT ordered migration = WI 1822732, 2026-06). `New-Migration.ps1` picks the correct next build + timestamp + WI.
- **Keep the embedded ALTER text and the canonical `Common/Views` files identical** — both must carry the same fixed view definition.

### 6A.1 — Before/after for the two view edits (files #1 & #2)

`OR` = Original, `CO` = Corrected. Add the `NOT EXISTS` supersede clause to every PROD join. (`QPOST_SETTLE_PROD` at the QPOST sites — sites #2 and #3 are byte-identical.)

**BEFORE** (QRPTS `TRANSACTIONS` CTE, L68–71):
```sql
INNER JOIN QTRAN_SETTLE_PROD AS PROD
       ON PROD.TRNX_ID = S.TRNX_ID
      AND PROD.MTR_SFX = S.MTR_SFX
      AND PROD.REC_STATUS_CD IN ('CO','OR')
```
**AFTER:**
```sql
INNER JOIN QTRAN_SETTLE_PROD AS PROD
       ON PROD.TRNX_ID = S.TRNX_ID
      AND PROD.MTR_SFX = S.MTR_SFX
      AND PROD.REC_STATUS_CD IN ('CO','OR')
      AND ( PROD.REC_STATUS_CD = 'CO'
            OR NOT EXISTS ( SELECT 1 FROM QTRAN_SETTLE_PROD CO
                            WHERE CO.TRNX_ID = PROD.TRNX_ID
                              AND CO.MTR_SFX = PROD.MTR_SFX
                              AND CO.PROD_CD = PROD.PROD_CD
                              AND CO.DISP_CD = PROD.DISP_CD
                              AND CO.REC_STATUS_CD = 'CO' ) )
```
QRPTS `POSTED` CTE (L257) and QPOST mirror sole CTE (L68): identical, with `QPOST_SETTLE_PROD` in both the join and the `NOT EXISTS` subquery.

### 6A.2 — Content for the two NEW files (mirror of WI 1799519)

**File #4 — `…/OrderedMigrations/MSSQL/ENGSCLIENT/Migration_<YYYYMMDDHHMM>_<newWI>_ENGSCLIENT_MSSQL.cs`** *(before: does not exist)*
```csharp
using System.Collections.Generic;
using System.Reflection;

using FluentMigrator;

using Quorum.QFC.Core.Interface;
using Quorum.QDBManager.Core;
using Quorum.QDBManager.Model.UpgradeSteps;
using Quorum.QDBManager.Process;
using Quorum.QDBManager.Process.Migrations;

namespace IPF.TIPS.Database
{
    [Tags(TagBehavior.RequireAll, "ENGSCLIENT","MSSQL")]
    [TimestampedMigration(<YYYY>,<MM>,<DD>,<HH>,<mm>, "QTIP_<nextBuild>_00_IPF_ENGSCLIENT_<seq>_<newWI>.sql")]
    public class Migration_<YYYYMMDDHHMM>_<newWI>_ENGSCLIENT_MSSQL : QDBMScriptMigration
    {
        public Migration_<YYYYMMDDHHMM>_<newWI>_ENGSCLIENT_MSSQL(IQDBMMetadataProvider provider, UpgradeStep step)
        {
            Provider = provider;
            Step = step;

            Scripts = new Dictionary<QDatabaseVendor, string>
            {
                { QDatabaseVendor.SqlServer, "IPF.TIPS.Database.FluentMigrator.EmbeddedScripts.MSSQL.ENGSCLIENT.QTIP_<nextBuild>_00_IPF_ENGSCLIENT_<seq>_<newWI>.sql" }
            };

            MigrationAssembly = Assembly.GetExecutingAssembly();
        }
    }
}
```
*(Identical in shape to `Migration_202604201504_1799519_ENGSCLIENT_MSSQL.cs`; only the timestamp, class name, WI#, and embedded-script filename change. `New-Migration.ps1` generates it from `migration.template.txt`.)*

**File #3 — `…/EmbeddedScripts/MSSQL/ENGSCLIENT/QTIP_<nextBuild>_00_IPF_ENGSCLIENT_<seq>_<newWI>.sql`** *(before: does not exist)*
```sql
-- WI <newWI> : Case 26-01094568 — IPF Settlement Statement GJ/$ doubling.
-- Dedupe OR/CO settlement revisions in the SETTLE_PROD join (suppress the superseded OR row).

ALTER VIEW [dbo].[QRPTS_SETTLEMENT_STMT_VW]
AS
/* full view body = Common/MSSQL/Views/QRPTS_SETTLEMENT_STMT_VW.sql AFTER the §5 edit:
   the TRANSACTIONS-CTE QTRAN_SETTLE_PROD join and the POSTED-CTE QPOST_SETTLE_PROD join
   each now carry the NOT EXISTS supersede clause shown in §6A.1 */
GO

ALTER VIEW [dbo].[QPOST_RPTS_SETTLEMENT_STMT_VW]
AS
/* full view body = Common/MSSQL/Views/QPOST_RPTS_SETTLEMENT_STMT_VW.sql AFTER the §5 edit:
   the sole POSTED-CTE QPOST_SETTLE_PROD join now carries the NOT EXISTS supersede clause */
GO
```
*(The canonical view files in #1/#2 are themselves `ALTER VIEW … GO`; this embedded script is their post-edit text concatenated. Keep the two in sync.)*

**File #5 — `IPF.TIPS.Database.csproj`** *(edit; `New-Migration.ps1` adds these alongside the existing ENGSCLIENT entries)*
```xml
<EmbeddedResource Include="FluentMigrator\EmbeddedScripts\MSSQL\ENGSCLIENT\QTIP_<nextBuild>_00_IPF_ENGSCLIENT_<seq>_<newWI>.sql" />
<Compile Include="FluentMigrator\OrderedMigrations\MSSQL\ENGSCLIENT\Migration_<YYYYMMDDHHMM>_<newWI>_ENGSCLIENT_MSSQL.cs" />
```

---

## 7. Pre-ship data checks (DBA — live DB not reachable from L4)

```sql
-- #1  Confirm OR and CO coexist per product for the affected contracts (the doubling set), and that
--     SUM doubles while MAX stays single. Replace <run_id> with the April-2025/CEP settlement RUN_ID.
SELECT P.TRNX_ID, P.MTR_SFX, P.PROD_CD, P.DISP_CD, P.QTY_UOM_CD,
       COUNT(*)                                            AS total_rows,
       SUM(CASE WHEN P.REC_STATUS_CD='OR' THEN 1 ELSE 0 END) AS or_rows,
       SUM(CASE WHEN P.REC_STATUS_CD='CO' THEN 1 ELSE 0 END) AS co_rows,
       SUM(P.VALUE_PR) AS value_sum, MAX(P.VALUE_PR) AS value_max
FROM   QTRAN_SETTLE_PROD P
JOIN   QTRAN_PAYSTATION  PS ON PS.TRNX_ID=P.TRNX_ID AND PS.MTR_SFX=P.MTR_SFX
WHERE  PS.RUN_ID = <run_id>
  AND  P.REC_STATUS_CD IN ('CO','OR')
GROUP BY P.TRNX_ID, P.MTR_SFX, P.PROD_CD, P.DISP_CD, P.QTY_UOM_CD
HAVING COUNT(*) > 1
ORDER BY P.TRNX_ID, P.PROD_CD, P.DISP_CD;

-- #2  Validate the UNIT_TM_CD assumption: PROD must NOT also carry daily ('D') rows for the same key
--     (the view filters UNIT_TM_CD='M' only on the SUMMARY table S, not on PROD). If 'D' rows appear
--     for a key that also has 'M', add  AND PROD.UNIT_TM_CD='M'  to the join. (Verify column exists.)
SELECT P.TRNX_ID, P.MTR_SFX, P.PROD_CD, P.DISP_CD, P.UNIT_TM_CD, P.REC_STATUS_CD, COUNT(*) AS cnt
FROM   QTRAN_SETTLE_PROD P
JOIN   QTRAN_PAYSTATION  PS ON PS.TRNX_ID=P.TRNX_ID AND PS.MTR_SFX=P.MTR_SFX
WHERE  PS.RUN_ID = <run_id>
GROUP BY P.TRNX_ID, P.MTR_SFX, P.PROD_CD, P.DISP_CD, P.UNIT_TM_CD, P.REC_STATUS_CD
ORDER BY P.TRNX_ID, P.PROD_CD, P.DISP_CD;
```

---

## 8. Verification (prove the bug, then prove the fix)

```sql
-- BEFORE fix — the view already doubles: SUM (what the report adds) vs MAX-based total (authoritative).
-- ratio ~2.0 with revision_count>0 for the 5 contracts; ~1.0 for the rest.
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
```

**AFTER fix (functional):** re-run the monthly processes (Measurement → Settle) for May-2025 acct / April-2025 prod, plant CEP, then re-run the Settlement Statement. Expected:
- GJ, rate, and $ for the five contracts **tie to the Calculation Summary / Query Suite / DB values** (doubled figures halve).
- Re-run query #2 above → `ratio ≈ 1.0` for all contracts.
- **Regression:** a single-revision (non-revised) contract is unchanged before/after.
- **Posted mode:** run the report in posted mode (uses `QPOST_RPTS_SETTLEMENT_STMT_VW`) and confirm it also ties out.

---

## 9. Risks & required adjustments (from adversarial review)

1. **Correlation key must include `PROD_CD` + `DISP_CD`** (done above). Omitting them would drop still-valid `OR` lines on a partially revised settlement.
2. **`UNIT_TM_CD` / daily rows** — biggest unverified assumption; run check #2. If PROD holds `'D'` rows for the same key, add `AND PROD.UNIT_TM_CD='M'` to the join. (`NOT EXISTS` tolerates extra rows better than `ROW_NUMBER`-to-one.)
3. **`QTY_UOM_CD` grain** — it is a `GROUP BY` key; the `ROW_NUMBER` alternative must include it in the `PARTITION BY`. (`NOT EXISTS` is unaffected unless `OR`/`CO` differ in UOM, which would already separate them in the GROUP BY.)
4. **Deterministic tiebreaker** — only relevant to the `ROW_NUMBER` alternative if >1 `CO` per key can exist (`, RUN_ID DESC, ACCT_DT DESC`). `NOT EXISTS` keeps all `CO` rows, so no tiebreaker needed.
5. **`'R'` (reversed) rows** — the existing `IN ('CO','OR')` predicate already excludes them; keep that predicate.
6. **Rebase on develop** — sibling **PR #126604** (bug #1787313, merged 2026-04-20) rewrote the surrounding TOS join (`QCODE_TOS`→`QCODE_SERVICE_CLASS`) in **both** views; wrap whatever the product join looks like post-merge.

---

## 10. Latent fan-out hardening (not firing for these 5 contracts; optional)

Three BA-level joins in the same view carry multi-value columns in the `GROUP BY` and could double for a *different* shipper:
- `SCTRL_BA_TAX_ID TAX` — joined on `BA_NO` **only** (no `BA_SUF`, no `TAX_ID_TYPE_CD` filter); `TAX_ID`/`TAX_ID_TYPE_CD` in `GROUP BY` (L183–184). A BA with >1 tax-id row would multiply.
- `QCTRL_BA_ADDRESS_VW BA_ADDR` — `BA_NO`+`BA_SUF`; address columns in `GROUP BY`. Multiple addresses would multiply.
- `SCTRL_BA_CONTACTINFO_VW BAC` — filtered to `CREP` + `PRIMARY_IND=1` (normally one row; multiplies if >1 primary CREP).

The 5 affected contracts show a clean exact-2× (single revision), so these aren't contributing here. A hardening pass (add `BA_SUF` + a `TAX_ID_TYPE_CD` predicate to the tax join, or pre-aggregate these lookups) would prevent a future "doubling" report from a different shipper. **Not required to resolve this case.**

---

## 11. Existing-fix status (exhaustively verified 2026-06-24)

- **No ADO work item** tracks this doubling (searched case #, view name, `REC_STATUS_CD`, "Settlement Statement double/duplicate/revision"). **The fix is net-new.**
- **No borrowable dedup** exists in any client or base settlement view (base `Quorum.TIPS.Database` has no `SETTLEMENT_STMT_VW`; VMH's gas-statement proc scopes by `RUN_ID`, not transplantable).
- **Sibling bug #1787313** / PR #126604 edits these same two views but only the TOS lookup — the `PROD`/`REC_STATUS_CD` join is byte-identical before/after; it does **not** fix the doubling and carries no fixed-in-build for it. Coordinate to avoid a merge collision.

---

## 12. ADO bug — ready to paste

| Field | Value |
|---|---|
| **Work Item Type** | Bug |
| **Title** | IPF - 26-01094568 - Settlement Statement (RPT_43154) doubles GJ & $ for revised settlements (views SUM both OR and CO revision rows) |
| **Area Path** | QuorumSoftware\Engineering\Software Services\Professional Services *(match sibling #1787313)* |
| **Product / Module** | TIPS / Reporting — Settlement Statement |
| **Severity / Priority** | 3 - Medium / 3 |
| **Found in Version** | Current IPF build + upgrade build (17.0.x); present in `QTIP_17.0.00.0031.0000…_1799519.sql` |
| **Customer / Case** | Inter Pipeline Ltd. (IPF) / 26-01094568 |
| **Root Cause (category)** | Code Defect — report views sum across settlement revisions (no per-product dedup) |

**Repro** (IPF_HD_DEVA1; plant CEP, May-2025 acct / April-2025 prod): ensure Monthly Settle ran → run the Settlement Statement → compare GJ/$ to the Settlement Calculation screen / Query Suite for the affected contracts.
**Expected:** GJ, rate, $ tie to Calculation Summary / Query Suite / DB.
**Actual:** GJ and $ ~2× for Access Gas (1103), Ovintiv (1027), PG&E (1033), Portland General Electric (1011/1116/1154), Puget (1095); rate correct; DB/Query Suite/Calc Summary show the correct (half) values.

**Root Cause:** `IPF.TIPS.Database` views `QRPTS_SETTLEMENT_STMT_VW` and `QPOST_RPTS_SETTLEMENT_STMT_VW` join `…SETTLE_PROD` with `REC_STATUS_CD IN ('CO','OR')` (L68–71; QRPTS POSTED CTE L257–260) but omit `REC_STATUS_CD` from the `GROUP BY` (L168). For a revised product the `OR` and `CO` rows collapse into one group, so `SUM(APPLIED_VOL_HV_PR)` (L34) and `SUM(VALUE_PR)` (L36) add both revisions → 2×. Rate `AVG` (L35) and totals `MAX(S.TOT_*)` (L39–43) are unaffected. The Crystal report only `Sum()`s the doubled view rows.

**Proposed Fix:** §5 — suppress the superseded `OR` via correlated `NOT EXISTS` (key on `TRNX_ID, MTR_SFX, PROD_CD, DISP_CD`) at the 3 product-join sites; `CO` supersedes `OR`. View-only; no Crystal/data change. Do NOT touch the FEE views. Confirm `UNIT_TM_CD`/single-pair assumptions (§7) and rebase on develop (post-#126604).

**Regression Risk:** Low; localized to two IPF report views. Single-revision products (the majority) unchanged. No change to Crystal, settlement data, or the `MAX` totals.

**Release Note (draft):** *Corrected the IPF Settlement Statement so that, when a settlement has been revised, the report uses only the final (corrected) revision for each product. Previously the original and corrected revisions were summed, doubling the GJ and dollar amounts (the unit rate and stored settlement totals were unaffected).*

---

## 13. Current code (`develop`, pre-fix) — full view source

Verbatim live `develop` source of the two views to change (IPF.TIPS.Database, post-PR #126604 — i.e. already on `QCODE_SERVICE_CLASS`). The fix (§5 / §6A.1) adds the `NOT EXISTS` supersede clause to the **`…SETTLE_PROD AS PROD`** joins only: in **13.1** the `QTRAN_SETTLE_PROD` join (**L68**) and the `QPOST_SETTLE_PROD` join in the `POSTED` CTE (**L257**); in **13.2** the single `QPOST_SETTLE_PROD` join (**L68**). Everything else stays exactly as below.

### 13.1 `Common/MSSQL/Views/QRPTS_SETTLEMENT_STMT_VW.sql` — non-posted (CTEs `TRANSACTIONS` + `POSTED`)
```sql
ALTER VIEW [dbo].[QRPTS_SETTLEMENT_STMT_VW]
AS
--NON-POSTED
WITH TRANSACTIONS AS (
SELECT 
         --HEADER SECTION
            P.PLANT_NM,
            S.PLANT_NO,
            S.ACCT_DT,
            S.PROD_DT,
            PAY.CTR_PARTY_BA_NO,
            PAY.CTR_PARTY_BA_SUF,
            CTRPTY.BA_NM1 AS CTR_PARTY_NM,
            PAY.CTR_NO,
            PAY.CTR_DESCR,
            PAY.CTR_TYPE_CD,
            PAY.SUB_CTR_TYPE_CD,
            SC.SERVICE_CLASS_CD,
            QP.PROD_DESCR,
            ISNULL(SC.SERVICE_CLASS_DESCR, '') AS TOS_DESCR,
            TAX.TAX_ID_TYPE_CD,
            TAX.TAX_ID, -- GST REGISTRATION NO
            BA_ADDR.ADDR_LINE1,
            BA_ADDR.CITY,
            BA_ADDR.COUNTRY_CD,
            BA_ADDR.ZIP_CD,
         -- PROD SECTION
              CASE WHEN (PROD.DISP_CD IN ('PROD','INLT', 'PRFS')) THEN PROD.PROD_CD ELSE PROD.PROD_CD END AS PROD_CD,
              CASE WHEN (PROD.DISP_CD IN ('PROD','INLT', 'PRFS')) THEN PROD.DISP_CD ELSE PROD.DISP_CD END AS DISP_CD,
              CASE WHEN (PROD.DISP_CD IN ('PROD','INLT', 'PRFS')) THEN PROD.QTY_UOM_CD ELSE PROD.QTY_UOM_CD END AS QTY_UOM_CD,
              SUM(CASE WHEN (PROD.DISP_CD IN ('PROD','INLT', 'PRFS')) THEN COALESCE(CASE WHEN PROD.DISP_CD = 'PRFS' THEN 0 ELSE PROD.APPLIED_VOL_HV_PR END, 0) ELSE 0 END) AS APPLIED_VOL_HV_PR,
              AVG(CASE WHEN (PROD.DISP_CD IN ('PROD','INLT', 'PRFS')) THEN COALESCE(CASE WHEN PROD.DISP_CD = 'PRFS' THEN PROD.VALUE_PR/PROD.APPLIED_VOL_HV ELSE PROD.APPLIED_PRICE END, 0) ELSE 0 END) AS APPLIED_PRICE,
              SUM(CASE WHEN (PROD.DISP_CD IN ('PROD','INLT', 'PRFS')) THEN COALESCE(PROD.VALUE_PR, 0) ELSE 0 END) AS VALUE_PR,
         -- SUMMARY SECTION
              MAX(S.TOT_VALUE_PR) AS TOT_VALUE_PR,
              MAX(S.TOT_FEES_DEDUCTED) AS TOT_FEES_DEDUCTED,
              MAX(COALESCE(FIXED_FEE_TAX.TAX_DUE,0)) AS TOT_TAX,
              MAX(S.TOT_NET_VALUE_PR) AS TOT_NET_VALUE_PR,
              MAX(S.TOT_LIQ_VALUE_PR) AS TOT_LIQ_VALUE_PR,
         -- INVOICE DETAILS
              SUM(CASE WHEN (PROD.DISP_CD = 'MOB') THEN COALESCE(PROD.APPLIED_VOL_HV_PR, 0) ELSE 0 END) AS MOB_APPLIED_VOL_HV_PR,
              SUM(CASE WHEN (PROD.DISP_CD = 'MOB') THEN COALESCE(PROD.APPLIED_PRICE, 0) ELSE 0 END) AS MOB_APPLIED_PRICE,
              SUM(CASE WHEN (PROD.DISP_CD = 'MOB') THEN COALESCE(PROD.VALUE_PR, 0) ELSE 0 END) AS MOB_VALUE_PR,
              SUM(CASE WHEN (PROD.DISP_CD = 'MBF') THEN COALESCE(PROD.APPLIED_VOL_HV_PR, 0) ELSE 0 END) AS MBF_APPLIED_VOL_HV_PR,
              SUM(CASE WHEN (PROD.DISP_CD = 'MBF') THEN COALESCE(PROD.APPLIED_PRICE, 0) ELSE 0 END) AS MBF_APPLIED_PRICE,
              SUM(CASE WHEN (PROD.DISP_CD = 'MBF') THEN COALESCE(PROD.VALUE_PR, 0) ELSE 0 END) AS MBF_VALUE_PR,
              MAX(CASE WHEN (PROD.DISP_CD = 'MOB') THEN PROD.QTY_UOM_CD ELSE PROD.QTY_UOM_CD END) AS MOB_QTY_UOM_CD,
              MAX(CASE WHEN (PROD.DISP_CD = 'MBF') THEN PROD.QTY_UOM_CD ELSE PROD.QTY_UOM_CD END) AS MBF_QTY_UOM_CD,
              BAC.FIRST_NM,
              BAC.LAST_NM,
              MAX(COALESCE(FIXED_FEE.TOT_FEES_DEDUCTED, 0)) AS 'FIXED_FEE',
              MAX(COALESCE(REVISION.REVISION_COUNT, 0)) AS REVISION_COUNT
       FROM   QTRAN_SETTLE_SUMMARY AS S
              INNER JOIN QCTRL_PLANT_HDR P
                    ON P.PLANT_NO = S.PLANT_NO
                    AND S.ACCT_DT BETWEEN P.EFF_DT_FROM and P.EFF_DT_TO
              INNER JOIN QTRAN_PAYSTATION AS PAY
                     ON S.TRNX_ID = PAY.TRNX_ID
                     AND S.MTR_SFX = PAY.MTR_SFX
                     AND S.STMT_FORMAT_CD <> 'NP'
                     AND PAY.MTR_NO != 'MKUPPURC'
                     AND PAY.MTR_NO != 'IPFRESMOB'
              INNER JOIN QTRAN_SETTLE_PROD AS PROD          -- ◄ FIX SITE 1 (add NOT EXISTS supersede on this join)
                     ON PROD.TRNX_ID = S.TRNX_ID
                     AND PROD.MTR_SFX = S.MTR_SFX
                     AND PROD.REC_STATUS_CD IN ('CO','OR')
              LEFT OUTER JOIN SCTRL_BA_CONTACTINFO_VW AS BAC
                     ON PAY.CTR_PARTY_BA_NO = BAC.BA_NO 
                     AND PAY.CTR_PARTY_BA_SUF = BAC.BA_SUF
                     AND BAC.CONTACT_TYPE_CD = 'CREP'
                     AND BAC.PRIMARY_IND = 1
                INNER JOIN SCTRL_BA_ENTITY CTRPTY
                                  ON PAY.CTR_PARTY_BA_NO = CTRPTY.BA_NO                      
                       LEFT OUTER JOIN QCODE_PRODUCT QP
                                  ON PROD.PROD_CD = QP.PROD_CD
                       LEFT JOIN QCODE_SERVICE_CLASS SC
                        ON PAY.CTR_USR_DEF_2 = SC.SERVICE_CLASS_CD
                       LEFT JOIN SCTRL_BA_TAX_ID TAX
                                  ON TAX.BA_NO = PAY.CTR_PARTY_BA_NO
                       LEFT JOIN QCTRL_BA_ADDRESS_VW BA_ADDR
                                  ON BA_ADDR.BA_NO = PAY.CTR_PARTY_BA_NO
                                  AND BA_ADDR.BA_SUF = PAY.CTR_PARTY_BA_SUF
              /* Fixed Facility CCT Amount */
              LEFT OUTER JOIN (SELECT FEE.RUN_ID, FEE.TRNX_ID, FEE.MTR_SFX, PAY.CTR_PARTY_BA_NO, PAY.CTR_PARTY_BA_SUF,
                                      PAY.CTR_NO, PAY.REC_STATUS_CD, FEE.FEE_TYPE_CD, SUM(FEE.VALUE_PR) AS TOT_FEES_DEDUCTED
                                FROM QTRAN_SETTLE_FEE FEE
                                    INNER JOIN QTRAN_PAYSTATION PAY ON FEE.TRNX_ID = PAY.TRNX_ID AND FEE.MTR_SFX = PAY.MTR_SFX
                                    INNER JOIN QCTRL_CTR_FACILITY_CCT CCT ON PAY.CTR_NO = CCT.CTR_NO AND PAY.CCT_NO = CCT.PLANT_CCT_NO
                                            AND PAY.PROD_DT BETWEEN CCT.EFF_DT_FROM AND CCT.EFF_DT_TO
                                GROUP BY FEE.RUN_ID, FEE.TRNX_ID, FEE.MTR_SFX, PAY.CTR_PARTY_BA_NO, PAY.CTR_PARTY_BA_SUF,
                                         PAY.CTR_NO, PAY.REC_STATUS_CD, FEE.FEE_TYPE_CD) FIXED_FEE
                     ON FIXED_FEE.RUN_ID = PAY.RUN_ID AND FIXED_FEE.CTR_PARTY_BA_NO = PAY.CTR_PARTY_BA_NO
                     AND FIXED_FEE.CTR_PARTY_BA_SUF = PAY.CTR_PARTY_BA_SUF AND FIXED_FEE.CTR_NO = PAY.CTR_NO
                     AND FIXED_FEE.REC_STATUS_CD = PAY.REC_STATUS_CD AND FIXED_FEE.FEE_TYPE_CD = PROD.PROD_CD
              LEFT OUTER JOIN (SELECT T.RUN_ID, P.CTR_PARTY_BA_NO, P.CTR_PARTY_BA_SUF, P.CTR_NO, P.REC_STATUS_CD,
                                      SUM(ROUND(T.TAX_DUE,2)) AS TAX_DUE
                                FROM QTRAN_SETTLE_TAX T
                                    INNER JOIN QTRAN_PAYSTATION P ON T.TRNX_ID = P.TRNX_ID AND T.MTR_SFX = P.MTR_SFX
                                GROUP BY T.RUN_ID, P.CTR_PARTY_BA_NO, P.CTR_PARTY_BA_SUF, P.CTR_NO, P.REC_STATUS_CD) FIXED_FEE_TAX
                     ON FIXED_FEE_TAX.RUN_ID = PAY.RUN_ID AND FIXED_FEE_TAX.CTR_PARTY_BA_NO = PAY.CTR_PARTY_BA_NO
                     AND FIXED_FEE_TAX.CTR_PARTY_BA_SUF = PAY.CTR_PARTY_BA_SUF AND FIXED_FEE_TAX.CTR_NO = PAY.CTR_NO
                     AND FIXED_FEE_TAX.REC_STATUS_CD = PAY.REC_STATUS_CD
              LEFT OUTER JOIN (SELECT PLANT_NO, PROD_DT, COUNT(DISTINCT ACCT_DT) AS REVISION_COUNT
                                FROM QCTRL_PPA_MTR_HDR GROUP BY PLANT_NO, PROD_DT) REVISION 
                     ON REVISION.PLANT_NO = S.PLANT_NO AND REVISION.PROD_DT = S.PROD_DT
       WHERE
            S.UNIT_TM_CD = 'M'
            AND PROD.PROD_CD <> 'ETH' 
            AND (PAY.CCT_NO IS NULL 
                 OR PAY.CCT_NO NOT IN (SELECT COALESCE(PLANT_CCT_NO,'1') AS PLANT_CCT_NO
                                       FROM QCTRL_CTR_FACILITY_CCT
                                       WHERE CTR_NO = PAY.CTR_NO AND S.PROD_DT BETWEEN EFF_DT_FROM AND EFF_DT_TO ))
       GROUP BY  P.PLANT_NM, S.PLANT_NO, S.ACCT_DT, S.PROD_DT, PAY.CTR_PARTY_BA_NO, PAY.CTR_PARTY_BA_SUF,
            CTRPTY.BA_NM1, PAY.CTR_NO, PAY.CTR_DESCR, PAY.CTR_TYPE_CD, PAY.SUB_CTR_TYPE_CD, SC.SERVICE_CLASS_CD,
            QP.PROD_DESCR, SC.SERVICE_CLASS_DESCR, TAX.TAX_ID_TYPE_CD, TAX.TAX_ID, BA_ADDR.ADDR_LINE1, BA_ADDR.CITY,
            BA_ADDR.COUNTRY_CD, BA_ADDR.ZIP_CD, PROD.PROD_CD, PROD.DISP_CD, PROD.QTY_UOM_CD, BAC.FIRST_NM, BAC.LAST_NM
            -- NOTE: REC_STATUS_CD is intentionally ABSENT here → OR+CO collapse into one group → SUM doubles.
), POSTED as (SELECT 
         -- ... identical column list to TRANSACTIONS (HEADER/PROD/SUMMARY/INVOICE sections) ...
       FROM   QPOST_SETTLE_SUMMARY AS S
              INNER JOIN QCTRL_PLANT_HDR P ON P.PLANT_NO = S.PLANT_NO AND S.ACCT_DT BETWEEN P.EFF_DT_FROM and P.EFF_DT_TO
              INNER JOIN QPOST_PAYSTATION AS PAY ON S.TRNX_ID = PAY.TRNX_ID AND S.MTR_SFX = PAY.MTR_SFX
                     AND S.STMT_FORMAT_CD <> 'NP' AND PAY.MTR_NO != 'MKUPPURC' AND PAY.MTR_NO != 'IPFRESMOB'
              INNER JOIN QPOST_SETTLE_PROD AS PROD          -- ◄ FIX SITE 2 (add NOT EXISTS supersede on this join)
                     ON PROD.TRNX_ID = S.TRNX_ID
                     AND PROD.MTR_SFX = S.MTR_SFX
                     AND PROD.REC_STATUS_CD IN ('CO','OR')
              -- ... remainder of POSTED CTE (BAC / CTRPTY / QP / SC / TAX / BA_ADDR / FIXED_FEE / FIXED_FEE_TAX / REVISION joins,
              --     WHERE S.UNIT_TM_CD='M' ..., and GROUP BY WITHOUT REC_STATUS_CD) is identical in shape to TRANSACTIONS above
)
SELECT  CURRENT_TRANSACTIONS.PLANT_NM, 0 as TRNX_ID, 0 as MTR_NO, ' ' as MTR_SFX, CURRENT_TRANSACTIONS.PLANT_NO,
        CURRENT_TRANSACTIONS.ACCT_DT, CURRENT_TRANSACTIONS.PROD_DT, 0 as RUN_ID, ...,
        CURRENT_TRANSACTIONS.APPLIED_VOL_HV_PR, CURRENT_TRANSACTIONS.APPLIED_PRICE, CURRENT_TRANSACTIONS.VALUE_PR,
        ' ' as REC_STATUS_CD, CURRENT_TRANSACTIONS.TOT_VALUE_PR, ..., CURRENT_TRANSACTIONS.REVISION_COUNT,
        POSTED_TRANSACTIONS.ACCT_DT PREV_ACCT_DT, ..., COALESCE(POSTED_TRANSACTIONS.MBF_VALUE_PR,0) AS PREV_MBF_VALUE_PR ...
FROM        TRANSACTIONS AS CURRENT_TRANSACTIONS
LEFT OUTER JOIN POSTED AS POSTED_TRANSACTIONS
              ON  CURRENT_TRANSACTIONS.PLANT_NO = POSTED_TRANSACTIONS.PLANT_NO
              AND CURRENT_TRANSACTIONS.CTR_NO = POSTED_TRANSACTIONS.CTR_NO
              AND CURRENT_TRANSACTIONS.PROD_DT = POSTED_TRANSACTIONS.PROD_DT
              AND CURRENT_TRANSACTIONS.PROD_CD = POSTED_TRANSACTIONS.PROD_CD
              AND CURRENT_TRANSACTIONS.DISP_CD = POSTED_TRANSACTIONS.DISP_CD 
              AND POSTED_TRANSACTIONS.ACCT_DT <> POSTED_TRANSACTIONS.PROD_DT        			   
              AND POSTED_TRANSACTIONS.ACCT_DT = (SELECT MAX(ACCT_DT) FROM POSTED WHERE PLANT_NO = POSTED_TRANSACTIONS.PLANT_NO
                                                  AND PROD_DT = POSTED_TRANSACTIONS.PROD_DT AND CTR_NO = POSTED_TRANSACTIONS.CTR_NO
                                                  AND PROD_CD = POSTED_TRANSACTIONS.PROD_CD AND DISP_CD = POSTED_TRANSACTIONS.DISP_CD
                                                  AND ACCT_DT < CURRENT_TRANSACTIONS.ACCT_DT AND ACCT_DT <> CURRENT_TRANSACTIONS.PROD_DT)
WHERE
    CURRENT_TRANSACTIONS.ACCT_DT <> CURRENT_TRANSACTIONS.PROD_DT
    AND (CURRENT_TRANSACTIONS.TOT_NET_VALUE_PR <> 0 OR COALESCE(CURRENT_TRANSACTIONS.TOT_FEES_DEDUCTED, 0) <> 0 OR CURRENT_TRANSACTIONS.APPLIED_VOL_HV_PR <> 0)
    AND ((CURRENT_TRANSACTIONS.TOT_NET_VALUE_PR - COALESCE(POSTED_TRANSACTIONS.TOT_NET_VALUE_PR,0) <> 0)
        OR COALESCE(CURRENT_TRANSACTIONS.TOT_FEES_DEDUCTED, 0) - COALESCE(POSTED_TRANSACTIONS.FIXED_FEE,0) <> 0)
    OR CURRENT_TRANSACTIONS.APPLIED_VOL_HV_PR <> 0 
    AND (((CURRENT_TRANSACTIONS.APPLIED_VOL_HV_PR <> POSTED_TRANSACTIONS.APPLIED_VOL_HV_PR) AND (CURRENT_TRANSACTIONS.VALUE_PR <> POSTED_TRANSACTIONS.VALUE_PR))
        AND ((CURRENT_TRANSACTIONS.MBF_APPLIED_VOL_HV_PR <> POSTED_TRANSACTIONS.MBF_APPLIED_VOL_HV_PR) AND (CURRENT_TRANSACTIONS.MBF_VALUE_PR <> POSTED_TRANSACTIONS.MBF_VALUE_PR))
        AND ((CURRENT_TRANSACTIONS.MOB_APPLIED_VOL_HV_PR <> POSTED_TRANSACTIONS.MOB_APPLIED_VOL_HV_PR) AND (CURRENT_TRANSACTIONS.MOB_VALUE_PR <> POSTED_TRANSACTIONS.MOB_VALUE_PR)))
    OR (CURRENT_TRANSACTIONS.APPLIED_PRICE = 0 AND CURRENT_TRANSACTIONS.APPLIED_VOL_HV_PR <> 0 AND COALESCE(POSTED_TRANSACTIONS.APPLIED_VOL_HV_PR,0) = 0)
GO
```
> The `POSTED` CTE and the final-SELECT column list are abbreviated above for length; the **only** edit needed in this file is the `NOT EXISTS` clause on the two `…SETTLE_PROD` joins (FIX SITE 1, FIX SITE 2). **Full untruncated verbatim source saved as `Case_26-01094568_current_QRPTS_SETTLEMENT_STMT_VW.sql`** (develop, 2026-06-29).

### 13.2 `Common/MSSQL/Views/QPOST_RPTS_SETTLEMENT_STMT_VW.sql` — posted mirror (single CTE `POSTED`, self-joined)
```sql
ALTER VIEW [dbo].[QPOST_RPTS_SETTLEMENT_STMT_VW]
AS
--POSTED
WITH POSTED as (SELECT 
         -- HEADER / PROD / SUMMARY / INVOICE sections — same column list as QRPTS (SUM on volume/value, AVG on rate, MAX on TOT_*)
       FROM   QPOST_SETTLE_SUMMARY AS S
              INNER JOIN QCTRL_PLANT_HDR P ON P.PLANT_NO = S.PLANT_NO AND S.ACCT_DT BETWEEN P.EFF_DT_FROM and P.EFF_DT_TO
              INNER JOIN QPOST_PAYSTATION AS PAY ON S.TRNX_ID = PAY.TRNX_ID AND S.MTR_SFX = PAY.MTR_SFX
                     AND S.STMT_FORMAT_CD <> 'NP' AND PAY.MTR_NO != 'MKUPPURC' AND PAY.MTR_NO != 'IPFRESMOB'
              INNER JOIN QPOST_SETTLE_PROD AS PROD          -- ◄ FIX SITE 3 (add NOT EXISTS supersede on this join)
                     ON PROD.TRNX_ID = S.TRNX_ID
                     AND PROD.MTR_SFX = S.MTR_SFX
                     AND PROD.REC_STATUS_CD IN ('CO','OR')
              -- ... BAC / CTRPTY / QP / SC(QCODE_SERVICE_CLASS) / TAX / BA_ADDR / FIXED_FEE / FIXED_FEE_TAX / REVISION joins,
              --     WHERE S.UNIT_TM_CD='M' AND PROD.PROD_CD<>'ETH' AND (CCT exclusion), GROUP BY WITHOUT REC_STATUS_CD
)
SELECT  CURRENT_TRANSACTIONS.PLANT_NM, 0 as TRNX_ID, 0 as MTR_NO, ' ' as MTR_SFX, CURRENT_TRANSACTIONS.PLANT_NO, ...,
        CURRENT_TRANSACTIONS.APPLIED_VOL_HV_PR, CURRENT_TRANSACTIONS.APPLIED_PRICE, CURRENT_TRANSACTIONS.VALUE_PR, ...,
        CURRENT_TRANSACTIONS.FIXED_FEE, CURRENT_TRANSACTIONS.REVISION_COUNT
FROM        POSTED AS CURRENT_TRANSACTIONS                  -- NB: single CTE, self-joined for the prior-period columns
LEFT OUTER JOIN POSTED AS POSTED_TRANSACTIONS
              ON  CURRENT_TRANSACTIONS.PLANT_NO = POSTED_TRANSACTIONS.PLANT_NO
              AND CURRENT_TRANSACTIONS.CTR_NO = POSTED_TRANSACTIONS.CTR_NO
              AND CURRENT_TRANSACTIONS.PROD_DT = POSTED_TRANSACTIONS.PROD_DT
              AND CURRENT_TRANSACTIONS.PROD_CD = POSTED_TRANSACTIONS.PROD_CD
              AND CURRENT_TRANSACTIONS.DISP_CD = POSTED_TRANSACTIONS.DISP_CD 
              AND POSTED_TRANSACTIONS.ACCT_DT <> POSTED_TRANSACTIONS.PROD_DT
              AND POSTED_TRANSACTIONS.ACCT_DT = (SELECT MAX(ACCT_DT) FROM POSTED WHERE PLANT_NO = POSTED_TRANSACTIONS.PLANT_NO
                                                  AND PROD_DT = POSTED_TRANSACTIONS.PROD_DT AND CTR_NO = POSTED_TRANSACTIONS.CTR_NO
                                                  AND PROD_CD = POSTED_TRANSACTIONS.PROD_CD AND DISP_CD = POSTED_TRANSACTIONS.DISP_CD
                                                  AND ACCT_DT < CURRENT_TRANSACTIONS.ACCT_DT AND ACCT_DT <> CURRENT_TRANSACTIONS.PROD_DT)
WHERE  CURRENT_TRANSACTIONS.ACCT_DT <> CURRENT_TRANSACTIONS.PROD_DT
   AND ( ... same change-detection predicate as QRPTS ... )
GO
```
> Same single edit (FIX SITE 3) — the `NOT EXISTS` clause on the `QPOST_SETTLE_PROD` join. **Full untruncated verbatim source saved as `Case_26-01094568_current_QPOST_RPTS_SETTLEMENT_STMT_VW.sql`** (develop, 2026-06-29).

---

*Symbols/line numbers verified against `QRPTS_SETTLEMENT_STMT_VW.sql`, `QPOST_RPTS_SETTLEMENT_STMT_VW.sql`, and `QRPTS_SETTLEMENT_STMT_FEE_VW.sql` @ develop (IPF.TIPS.Database), and ADO facts re-confirmed live on **2026-06-29** (SF case In Progress; no ADO bug for the case; #1787313 Acceptance; PR #126604 Completed/merged 2026-04-20). Re-baseline against the client build branch before coding. Case history & narrative: `L4 investigation.md` (Case 26-01094568); L4 triage record: `Case_26-01094568_L4_Triaged.md`.*
