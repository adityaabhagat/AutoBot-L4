# SKILL — FLOWCAL Family: Licensing & CrypKey (FLOWCAL · TESTit · PROVEit)

> **Auto-Bot skill — built by Aditya Bhagat.**
> Sources: Salesforce all-history mining (Product_list__c IN 'FLOWCAL','TESTit','PROVEit'; ~9,100 licensing/CrypKey-family cases, 37 resolved cases detail-sampled 2026-09-02) + ADO org `QuorumSoftware` (projects `Quorum`, `QuorumSoftware`, `myQuorum Cloud`).
> Scope: CrypKey licensing engine, site codes/site keys, license transfer, concurrent license counts, license modules, "Error authorizing" / policy-file errors, CrypKey Bypass. PII redacted; client codes retained.
> Licensing is the single biggest raw-volume category in the family (~9.1k cases) but most are routine site-key issuance (Root_Cause__c = `Licenses`). This skill is primarily a **fast-recipe** skill: match the symptom, run the recipe, close. Defect-class outcomes are rare and concentrated in §3.5/§3.6.

---

## 1. Quick Triage

| Symptom (verbatim from cases) | Likely cause | § |
|---|---|---|
| "All Licenses in Use" / "All licenses in use." at login | Stale CrypKey license state, hung sessions, or genuine count exhaustion | §3.1 |
| "All N licenses in use" in UAT but count looks like PRD's | Environment relicensed with wrong count; relicense that env | §3.1 |
| "All Licenses in Use" after server reboot / on a VM | Non-VM `crp32002.ngn` in use; swap VM-friendly NGN + rekey | §3.2 |
| "Error initializing CrypKey" | CrypKey service stopped/blocked (often antivirus) | §3.2 |
| "Unable to start Kernel service" (CrypKey kernel) | Antivirus blocked/delayed CrypKey driver/service | §3.2 |
| `Ckldrv.sys` lacks valid non-expired digital signature | Expired CrypKey NetworkX driver signature — needs signed driver from vendor | §3.2 |
| "Error authorizing the application" (TESTit/PROVEit/FLOWCAL) | CrypKey failure → relicense; on hosted envs can also be AD/OKTA group gap | §3.3 |
| "the program moved or sitekey password is bad" | License invalidated (program moved / hardware fingerprint changed) → relicense | §3.3 |
| "Date in policy file is out of sync with database" | TESTit/PROVEit local policy files deleted/stale → FCADMIN security-policy sync | §3.3 |
| Lost admin privileges after policy-file sync (Cloud) | Policy sync overwrote security → restore admin access | §3.3 |
| New laptop / new server / DR server needs license | Standard site-code → site-key issuance | §3.4 |
| User moved to new machine, old license stranded | License transfer: de-authorize old machine (or delete CrypKey files), key new one | §3.4 |
| Non-persistent Citrix/VDI invalidates license every deploy | CrypKey unsupported in non-persistent images → CrypKey Bypass | §3.5 |
| CrypKey bypass suddenly stops working | Bypass build expiry / signing certificate — check bypass build version | §3.5 |
| Read-only install acts read-write (or editor grayed out unexpectedly) | "VIEW ONLY USER" module flag set/omitted on the site key | §3.6 |
| FLOWCAL↔TESTit integration won't enable | License missing "TESTit Integrated = Yes" module → relicense with module added | §3.6 |

---

## 2. Decision Tree

```
Login/startup blocked with licensing error?
├─ Message = "All Licenses in Use"
│   ├─ Count in message matches contract & users genuinely max? → G1 Expected Behavior: free sessions / buy seats (§3.1)
│   ├─ Count looks wrong for that env (e.g., UAT showing PRD count)? → relicense that env with correct count (§3.1)
│   ├─ After reboot / VM / Citrix host? → swap VM-friendly crp32002.ngn + relicense (§3.2 recipe B)
│   └─ Intermittent / false "all in use" with few real users? → stale CrypKey state → full relicense recipe A;
│       persistent → reinstall CrypKey (§3.1/§3.2)
├─ Message mentions CrypKey init / kernel service / Ckldrv.sys
│   ├─ Antivirus/EDR recently changed? → AV exclusion + recipe A (§3.2)
│   └─ Driver signature expired? → signed Ckldrv.sys from CrypKey vendor via engineering (§3.2)
├─ Message = "Error authorizing the application" or "program moved or sitekey password is bad"
│   ├─ Hosted (QCloud/Citrix)? → check OKTA/AD groups FIRST, then have Cloud team relicense (§3.3)
│   └─ On-prem desktop/server? → relicense (recipe A); if repeats, uninstall/reinstall (§3.3)
├─ Message = "Date in policy file is out of sync with database" (TESTit/PROVEit)
│   └─ FCADMIN → File > Security > Security Options → synchronize policy (§3.3 recipe D)
└─ No error — user requests key/transfer/count → issuance & transfer recipes (§3.4)

Client on non-persistent VDI/Citrix or repeated invalidations by design of their infra?
└─ CrypKey Bypass path (§3.5) — versioned delivery, has expiry; FieldApps bypass exists too (1.19.1.0).
```

Gate mapping: §3.1–§3.4 are overwhelmingly **G2 Config** (CrypKey state/config) or **G1 Expected Behavior** (issuance requests). §3.2 driver-signature and §3.5 bypass-expiry are **G3 Version** (fixed/handled in specific builds). Genuine G5 code-change outcomes are rare.

---

## 3. Symptom clusters

### 3.1 "All Licenses in Use"

**Signature.** Login rejected with "All Licenses in Use" (FLOWCAL desktop or Citrix-published). Variants: false positives with only 1-2 real users; per-environment (RO vs RW, UAT vs PRD); after reboots; intermittent. The count shown comes from the site key applied to THAT app server — each server (e.g., `TULPWFCAP01`, `TULPWFCAP02`) is licensed separately (SF 26-01111009).

**Root causes seen (in observed frequency order):**
1. Stale/corrupt CrypKey license state on the app/Citrix server — fixed by relicensing (SF 26-01108804, 26-01109161, 26-01087007, 26-01104557).
2. Hung user sessions holding seats (SF 26-01101683 — suspected hung session; SF 25-01004359-family "sessions closing randomly" is the mirror symptom).
3. Environment keyed with the wrong count — UAT showing PRD's 10-seat count; relicensing FC RW HVM UAT fixed it (SF 26-01097402, client Harvest Midstream).
4. Intermittent failures from a damaged CrypKey install — full CrypKey reinstall resolved (SF 25-01040556).
5. Hosted env: QCloud team must relicense — raised as ADO ticket to Cloud team (SF 25-00995779; ADO 1788761 = SF 26-01087007 "Can we please run the FCInit utility and relicense"; ADO 1818569/1818946 = SF 26-01105935 Dominion WEXPRO FC_DOWP, relicensed from `QCPDOWFCTXZA01.qcloud.com`).

**Fix recipe A — standard relicense (on-prem, confirmed verbatim from resolutions):**
1. Have all users exit; end the `crp32002.ngn` process in Task Manager if present (SF 26-01109161, 26-01121506).
2. Stop the CrypKey service.
3. Delete the CrypKey license files ("the 7 crypkey files" per SF 26-01108804, 26-01109161; RO+RW both if two installs — SF 26-01087007, took 20-30 min for both).
4. Restart the CrypKey service (SF 26-01108804).
5. Run `FCInit.exe` in the FLOWCAL install directory → generates a **Site Code** (SF 25-01015239; ADO 1788761). FCInit dialog: "This location is not currently authorized to access FLOWCAL. Please email the Site Code to FLOWCAL.Support@QuorumSoftware.com to obtain a Site Key" (ADO 1658988/1655717).
6. Support generates the **Site Key** from the site code (format seen: site code `2552 6313 3839 9F71 E4`, site key `C0FE 0DCE 84C4 5F1C 0A2D 9BD3 0F` — SF 26-01120651, 26-01111009). Enter it; app launches.

**Escalation variant (hosted):** QCloud-hosted envs — support does NOT touch the server; open a Cloud Ops work item ("Problem/Incident Global Cloud Ops" in project `myQuorum Cloud`) referencing the SF case; Cloud team relicenses (ADO 1788761, 1818569, 1816405 — MOM UAT FLOWCAL+TESTit both relicensed; ADO 1867827/1868617 — SCR relicense to unlimited, servers `QCPSCRFCTXZA01.qcloud.com` / `QCUSCRFCTX501.qcloud.com`).

**Prevention note:** when relicensing, preserve the module set — the "About" file lists every module (see §3.6). Relicensing with a wrong module list creates the §3.6 symptoms.

### 3.2 CrypKey engine failures — service, kernel, driver, VM

**Signatures.**
- "Error initializing CrypKey" at TESTit/FLOWCAL launch (SF 26-01100016, 25-01037947).
- "Crypkey error - Unable to start Kernel service" (SF 26-01104805).
- Windows blocks `Ckldrv.sys` (CrypKey NetworkX driver, lives in `C:\Windows\System32`): "lacks a valid, non-expired digital signature" — blocked proving operations 9 days at ConocoPhillips (SF 25-01024840).
- CrypKey failure after system reboot (SF 25-01005422); "all licenses in use" on VMs/Remote Desktop (SF 26-01069308, 26-01102451).

**Root causes (anchored):**
- **Antivirus/EDR interference** — "Antivirus delayed or broke crypkey service" (SF 25-01015239, Root_Cause = Software Defect as coded, but the fix is config/AV); "The issue was with their anti virus. fixed on their side." (SF 26-01104805). AV kills or delays the CrypKey kernel service → init/kernel errors.
- **Non-VM NGN binary on a VM** — the standard `crp32002.ngn` is not VM-friendly; a VM-friendly `crp32002.ngn` variant exists and must be swapped in on virtual machines / RDS hosts (SF 25-01005422 "advised customer to use VM friendly crp32002.ngn"; SF 26-01069308 "swapped the crp32002.ngn file with the one for virtual machines"; SF 26-01104557 full sequence).
- **Expired driver signature** — `Ckldrv.sys` signing lapse is a vendor-side (CrypKey/NetworkX) issue; resolution requires an updated signed driver, not a relicense (SF 25-01024840).
- **Damaged CrypKey install** — full uninstall/reinstall of CrypKey needed when relicense alone fails (SF 25-01040556, 25-01014131 "re installed Crypkey, deleted all related files", 25-01004131 — uninstall guide provided; SF 26-01102451: deleted files, gave folder permissions, reinstall, finally re-ran the FLOWCAL installer on RDS 2019).

**Fix recipe B — CrypKey service/VM recovery (composite of SF 25-01015239 + 26-01104557):**
1. Stop the CrypKey service; kill `crp32002.ngn` process if running.
2. Delete existing `crp32002.ngn` files / CrypKey license files.
3. On a VM or RDS/Citrix host: place the **VM-friendly** `crp32002.ngn`.
4. Add AV/EDR exclusions for the FLOWCAL install dir + CrypKey service binaries (root-cause prevention; SF 25-01015239, 26-01104805).
5. Start the CrypKey service; run `FCInit.exe`; issue new site key (recipe A steps 5-6).
6. If still failing → uninstall CrypKey completely, delete residue, reinstall, then relicense (SF 25-01014131, 25-01040556); last resort re-run the product installer (SF 26-01102451).

**Ckldrv.sys signature path:** no support-side fix — escalate to Measurement engineering/product for the current signed driver build; interim is machine-level trust policy on the client side (their call). Anchor SF 25-01024840.

### 3.3 "Error authorizing the application" / "program moved" / policy-file out of sync

**Signatures.**
- "Error authorizing the application." — TESTit (SF 26-01119900, 25-01058218, 25-01036701, 24-00964595), PROVEit (SF 25-01023793, 24-00977974), FLOWCAL combined with all-licenses (SF 24-00989717).
- "the program moved or sitekey password is bad" — TESTit 2 (SF 25-01030416).
- "Date in policy file is out of sync with database." — TESTit/PROVEit (SF 26-01107496, 26-01093426, 25-00999098, 24-00989956, 24-00978690, 24-00969496).
- Combination event: Citrix ICA double-launch drove license count over limit AND corrupted policy sync — "Error authorizing the application" + "date in policy file is out of sync with database" both cleared by relicensing after Citrix fix (SF 24-00994231, GPL/Golden Pass; ADO 1705054).

**Root causes (anchored):**
- CrypKey license invalidation (moved install, changed hardware fingerprint, corrupted state) → **relicense** (SF 26-01119900 "Relicensed TESTit with a new site key", 25-01030416 "Re-licensed TESTit application", 25-01006251/ADO — QCloud relicensed).
- Deleted local app-data — users removing `C:\ProgramData\Flowcal` (also `Flow-Cal, Inc`) and `%LocalAppData%\Flowcal` folders breaks the policy file (TESTit 3.15 — SF 24-00978690, 24-00989956).
- Wrong module set on the key — PROVEit keyed with the Security module it shouldn't have: deleted `fieldapplications.pf` + `fieldapplications.dat` in `C:\ProgramData\Flow-Cal, Inc\Field Apps`, deleted the PROVEit license folder under `C:\ProgramData\CrypKey`, re-licensed WITHOUT the Security module (SF 24-00969496).
- Hosted red herring: "Error authorizing" resolved by adding the user to the right **AD groups** — not a CrypKey problem at all (SF 25-01020548, INS/Ineos).
- Policy sync side effect in Cloud: after policy-file sync, admin privileges vanished; had to restore admin access (SF 26-01107982).

**Fix recipe C — authorization error:**
1. Hosted env? Verify AD/OKTA group membership first (SF 25-01020548). If groups OK → Cloud team relicense.
2. On-prem: recipe A relicense. If error returns: uninstall the app, delete `C:\ProgramData\Quorum Software`, `C:\ProgramData\Flow-Cal, Inc`, `%LocalAppData%\Flow-Cal, Inc`/`Flowcal` folders, reinstall, relicense (SF 25-01058218 verbatim sequence).

**Fix recipe D — policy file out of sync (TESTit/PROVEit, confirmed verbatim SF 26-01107496):**
1. Open TESTit → **Switch Users**.
2. Log in as **FCADMIN**.
3. **File > Security > Security Options** → prompt "synchronize the security policy?" → **Yes**.
4. Close and reopen TESTit.
5. KB article exists: `support.quorumsoftware.com/s/article/Date-in-policy-file-is-out-of-sync-with-database` (SF 25-00999098).
6. Afterwards verify admin/security roles survived the sync (SF 26-01107982 regression).

### 3.4 Site key issuance & license transfer (the volume driver)

**Signature.** "Need a site key for <env/machine>", "License transfer from <old> to <new> laptop", "New Non Prod Server Site Key", "De-authorization code provided". Highest-volume symptom family across all three products (Licensing category: FLOWCAL 1,934 + TESTit 3,227 + PROVEit 1,176 cases; CrypKey category adds 2,768). Root_Cause__c almost always `Licenses` → **G1/ops, not a defect**.

**Issuance recipe (new machine/env):**
1. Client runs `FCInit.exe` (FLOWCAL) or the product's licensing screen (TESTit/PROVEit) → Site Code.
2. Client sends Site Code; support generates Site Key against the entitled module set + seat count; one key per server/machine (SF 26-01111009 — two servers, two code/key pairs; SF 26-01124764, 26-01124438 typical requests).
3. Client enters key. Keys are also issued for tools: `FcDataBoss` (SF 26-01124163), CALCit plugin (SF 26-01121658).

**Transfer recipe (old machine → new machine, desktop TESTit/PROVEit):**
1. Preferred: client runs the license transfer/de-authorization on the OLD machine → **de-authorization code** proves the seat is freed (SF 26-01120651 — PROVEit key issued after de-auth code provided).
2. If old machine is dead/imaged: delete the CrypKey files on the old system to kill the license (SF 26-01117984 — "removed the license from Kade's system by deleting the required CrypKey files").
3. Issue new site key on the new machine (issuance recipe). TESTit desktop with SQL Server LocalDB quirk: SF 26-01117984 also required installing SQL Server 2022 Express and running the **Password Utility** to fix the post-transfer login failure — check DB login before blaming the license.
4. Process doc exists per SF 26-01065301 ("TESTit w/PROVEit Desktops - License Transfer Process").

### 3.5 CrypKey Bypass (non-persistent Citrix/VDI and problem sites)

**Signature.** Client on non-persistent Citrix/VDI where every image redeploy invalidates the CrypKey license; or chronic CrypKey breakage. Cases titled "Crypkey Bypass delivery" (SF 26-01112707, 26-01112926).

**What it is (all anchored):** an alternative licensing method that disables CrypKey. Originated from SF 24-00938200 (P66 non-persistent Citrix enhancement → ADO Feature 1816387; PI Objective ADO 1817621 "Deliver authtest bypass for P66 and Diversified"). Delivered per-release: ADO 1815135 [DEV], 1830247 [R1050 PORT], 1830253 [R1060 PORT], 1833873 [R1090 PORT] (Diversified on FLOWCAL 10.5, P66 on 10.6). FieldApps (TESTit/PROVEit) bypass: ADO Feature 1788639 "Add CrypKey Bypass for FieldApps", tag 1.19.1.0, Closed.

**Install recipe (verbatim from SF 26-01112707 resolution):**
1. Extract `authtest_bypass.exe` into the FLOWCAL installation directory (internal build share: `\\qddfcfs01\Data\InstallBuilds\InstallSets\AuthTest Bypass\10.5 - 10.6`). 7-zip needed to extract.
2. Replace the existing `AuthTest.dll` in the directory.
3. Run `powershell ./Set-AuthorizationBypass.ps1` from the install directory.
4. If PowerShell blocked: manually edit `FLOWCAL.exe.config` → add `<add key="licensing:Authorization.Bypass" value="Y"/>` to `<appSettings>` (also confirmed as the internal QA bypass method in ADO bugs 1836642/1802263/1836632 repro steps).
5. Launch FLOWCAL and log in normally.

**Gotchas (anchored):**
- The bypass build **expires** — expiry produced unclear messaging, fixed by ADO 1835448 / 1850610 (Instant User variant) / 1854028 [R1090 PORT]. If a bypassed site suddenly can't log in, suspect bypass expiry first; get the refreshed standalone build.
- Bypass standalone builds needed **signing certificate updates** — ADO 1837533 (Dev), 1837612 (R1050), 1837600 (R1060). An old build may fail SmartScreen/signing checks.
- Strategic direction: CrypKey replacement is under SPIKE for multitenant SaaS (ADO 1852877, state New as of 2026-08). Okta OIDC is the chosen auth direction for next-gen (ADO Requirement 1779180); CrypKey extraction refactor for FieldApps: ADO 1732355 (`Quorum.FieldApplications.Licensing.CrypKey` project, `ICrypKey`/`CCrypKey`, `CAuthorization`).

### 3.6 License modules & counts (what a site key actually encodes)

**Signature.** Feature grayed out or unexpectedly enabled after relicensing; read-only env behaving read-write; FLOWCAL-TESTit integration refusing to enable; count disputes.

**Facts (anchored):**
- The FLOWCAL **About file** dumps the full license: user, machine, "Licenses in Use: N of M", DB instance, "Type of License: Enterprise", and the module list — Gas Application, Liquid Application, Additional Data Validation, Audit Package, Data Archive, Exception Resolver Linkages, Gas Day Projection Volume Service, Liquid Inventory/Line Fill, Lists/Locations, Live Oil Management, Master Characteristics, Monthly Close Functions and Service, Online Transaction Processing, Scheduled Movement Reconciliation, Scheduled Reporting, Service to Auto Estimate Missing Data, Source Analysis, System Balance Functions, Validation Set Points, Read-Only, Multi-System Extension, Number of Systems, TESTit Integrated, plus Current License Users list (ADO 1867827 verbatim). **Always request the About file before relicensing** — it is the module-preservation checklist.
- Read-only installs: check the **"VIEW ONLY USER"** module when keying with CrypKey instead of relying on a separate RO installer (ADO 1133540).
- FLOWCAL↔TESTit integration requires the **"TESTit Integrated = Yes"** module — DSU UAT had to be relicensed with existing modules + TESTit Integrated to enable integration (ADO 1810419).
- Wrong module set = auth errors (PROVEit Security module case, SF 24-00969496 in §3.3).
- Count questions ("what is our active license count?") — read it off the About file / license screen; SF 26-01116344, 26-01119513, 26-01082545 are routine G1.

---

## 4. Known ADO items (licensing/CrypKey)

| ADO ID | Type | Title (verbatim) | Relevance |
|---|---|---|---|
| 1816387 | Feature | 24-00938200--Enhancement to FC 10 to disable Crypkey for use in a non-persistent citrix deployment model | Bypass origin (P66) |
| 1817621 | PI Objective | Deliver authtest bypass for P66 and Diversified | Bypass program |
| 1815135 / 1830247 / 1830253 / 1833873 | User Story | P66 and Diversified: Crypkey Bypass [DEV]/[R1050 PORT]/[R1060 PORT]/[R1090 PORT] | Bypass in 10.5/10.6/10.9 branches — fixed-in builds INFERRED from port tags |
| 1788639 | Feature | Add CrypKey Bypass for FieldApps | TESTit/PROVEit bypass, tag 1.19.1.0 (INFERRED build) |
| 1835448 / 1850610 / 1854028 | User Story | Add clearer messaging when CrypKey bypass expires (+ Instant User; + R1090 PORT) | Bypass expiry symptom |
| 1837533 / 1837612 / 1837600 | User Story | Update signing certificate for Crypkey bypass standalone build (Dev/R1050/R1060) | Stale bypass builds fail signing |
| 1852877 | User Story | SPIKE - Multitenant: CrypKey replacement | Future direction (New) |
| 1732355 | Requirement | Extract CrypKey functionality | FieldApps `Quorum.FieldApplications.Licensing.CrypKey`, `ICrypKey`/`CCrypKey` |
| 1658988 / 1655717 | Bug | [AHT] FCInit support email is wrong (DEV / R1060* PORT) | FCInit dialog text + flow |
| 1133540 | Bug | FLOWCAL Read only Tank Editor grayed out (DEV*) | VIEW ONLY USER module guidance |
| 1788761 | Problem (Cloud Ops) | 26-01087007 - CRI - PRD - All licenses in use error | FCInit relicense on QCloud |
| 1818569 / 1818946 | Incident/Problem (Cloud Ops) | 26-01105935 - Dominion WEXPRO - FC_DOWP - All License in use | QCloud relicense flow |
| 1705054 | Incident (Cloud) | 24-00994231 - GPL TESTit PRD and UAT - Crypkey Failure and Policy file out of sync with DB | ICA double-launch ↔ CrypKey interplay |
| 1779180 | Requirement | ADR-006: Authentication - OIDC | Next-gen: Okta OIDC replaces CrypKey-era auth |

## 5. Diagnostic SQL

None surfaced. CrypKey state lives in the file system (`C:\ProgramData\CrypKey`, `crp32002.ngn`, `fieldapplications.pf/.dat`, policy files) and in the site key itself — not in the FLOWCAL schema. Do not invent license tables. The policy-file error references DB sync, but every observed fix is the in-app FCADMIN sync (§3.3 recipe D), not SQL.

## 6. Expected-Behavior FAQ

- **"Shouldn't UAT have its own license count?"** Yes — every server/environment is licensed independently with its own site key and count; if UAT shows PRD's count it was keyed wrong, relicense it (SF 26-01097402).
- **"Can we get more seats temporarily?"** Seat count is encoded in the site key; changing it = relicensing with a new key against entitlement (contract question, not support). QCloud clients with unlimited entitlement can be relicensed to unlimited (ADO 1867827/1868617).
- **"Why does each server need its own key?"** CrypKey fingerprints the machine; keys are per-machine (SF 26-01111009 — two servers, two keys).
- **"We rebooted and lost licenses."** Known VM/RDS behavior with the non-VM NGN file — apply the VM-friendly `crp32002.ngn` and relicense; not a defect (SF 25-01005422, 26-01069308).
- **"Where do I send the site code?"** FLOWCAL.Support@QuorumSoftware.com (ADO 1658988; the old in-app email text was a doc bug).

## 7. Escalation guidance

- **QCloud-hosted env** → never remote in; open `myQuorum Cloud` Cloud Ops item referencing the SF case; they run FCInit/relicense (ADO 1788761 pattern). Provide the About file + exact server FQDN (`QCP*`/`QCU*.qcloud.com`).
- **Ckldrv.sys signing / CrypKey vendor faults** → Measurement engineering (area `Quorum\North America\Measurement`), it needs a vendor-signed driver drop (SF 25-01024840).
- **Bypass requests** → require product-team approval + the current signed standalone build for the client's release (10.5/10.6/10.9 ports exist; §3.5). Never hand out `licensing:Authorization.Bypass` casually — it disables licensing enforcement.
- **Repeated CrypKey corruption on one host** → collect AV/EDR product + exclusions, host type (physical/VM/RDS/Citrix), then §3.2 recipe B; escalate as Platform only with that evidence.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
