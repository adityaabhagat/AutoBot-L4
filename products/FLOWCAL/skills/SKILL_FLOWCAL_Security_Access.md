# SKILL: FLOWCAL Family — Security, Authentication & Access Troubleshooting Guide

**Version:** 1.0 | **Created:** 2026-09-02 | **Products:** `FLOWCAL`, `TESTit`, `PROVEit` (Product_list__c literals)
**Scope:** Everything between "user double-clicks the icon" and "app opens with the right permissions": **OKTA** (QCloud identity, admin groups, group sync), **Citrix / StoreFront / FAS** (published-app launch, tiles, outages, profile resets), **FLOWCAL Instant Login & the credential Vault** (setup, post-refresh breakage, splash-screen hangs, VaultApi), **in-app security** (Security > Groups, access lists, role/permission bleed), **desktop login failures** (TESTit/PROVEit local SQL Server + Password Utility), **license lockouts that masquerade as access issues** (CrypKey, Policy Date File, Casper), and **Secure Gateway / network access** (DB whitelisting, SFTP, blocked IPs).
**Use when:** case mentions `OKTA`, `Citrix`, "Login Failed", "unable to log in", "locked out", `Instant Login`, `vault`, "access list", `Secure Gateway`, "StoreFront", "Cannot complete your request", "All licenses in use", "Policy Date File", "password reset", "RO/RW PRD icon", or a named user losing access.
**Companion skills:** Licensing/site-key issuance mechanics → SKILL_FLOWCAL_Licensing_CrypKey (group #5). QCloud environment outages/FTP → FLOWCloud skill (group #10). Windows-services problems → Services skill (group #3).

> **Evidence base (mined 2026-09-02):** ~150 closed family cases sampled across 6 SOQL clusters (OKTA subject hits, Citrix subject hits, Access-List category, login-failure subjects filtered to Software Defect/Application Configuration, Security/Application Security/Systems-Users-Groups categories, Instant Login/vault/Secure Gateway subjects) + 12 ADO work items verified live (`Quorum`, `QuorumSoftware`, `myQuorum Cloud` projects). Coverage plan sizes this group at ~1,620 family cases, ~170 actionable. Every root-cause claim cites an SF case number and/or ADO id. Fixed-in versions are **INFERRED** from SF resolution text unless marked release-notes-confirmed.
>
> **Data-quality caveat:** like every security category, the bulk of volume is routine user-admin fulfillment (add/reset/unlock). The defect signal concentrates in Instant Login (real product bugs, some still open) and QCloud provisioning sync ("Login Failed" recurrences). Treat §4-§5 as runbook routing, §7 as genuine RCA territory.

---

## 1. Quick Triage Table

| Symptom | Likely cause | § | First action |
|---|---|---|---|
| Citrix published TESTit/FLOWCAL app shows **"Login Failed"** for ONE user (invalid username/password) | QCloud user provisioning broken / OKTA↔app-DB sync miss | §4 | QCloud **reprovision / refresh membership** for the user (26-01123583, 26-01120638, 25-01047561) |
| Same "Login Failed" **recurring across users over months** | Known OKTA↔database sync defect ("vault not syncing with AD") | §4 | Escalate to Cloud with RCA request; cite ADO 1758285, cases 25-01046564, 25-01029238 |
| **All users** locked out of FLOWCAL/TESTit RO/RW at once | Citrix outage — expired/stale **Citrix FAS user certificates** or app publish broken | §5 | Cloud incident; cite ADO 1840366 (26-01114400, 26-01114527) |
| StoreFront tile **"Cannot complete your request"**, Okta tile visible | Stale **Okta storefront membership** for that account | §5 | QCloud refreshes Okta storefront membership; user clears browser cache (26-01108524) |
| **"Instant login failed"** on Citrix icon, splash screen hangs | Instant Login product bug (random) or Vault/env config | §7 | Check log for `InstantLoginSignOnAsync` → `UnknownLegacyError`; ADO 1845898/1854045 |
| Instant Login broken **right after a DB refresh** (RMAN from PRD) | Oracle passwords in UAT no longer match Vault | §7 | `ALTER USER ... IDENTIFIED BY ... ACCOUNT UNLOCK` for `FCSRV`, `svcfcinstant`, `fcowner` (26-01081662) |
| TESTit icon inside FLOWCAL: **"Vault service is not found or is currently unavailable"** | `Quorum.Platform.SecretManagement.VaultApi` not configured on FLOWCAL server | §7 | QCloud configures VaultApi; then clear bad MSMQ data if TI sync broke (26-01098171) |
| After **10.9.0.0** upgrade, Standard-type users can't use instant login | Regression in login_type check (`CSecurityUser.cpp:697`) | §7 | Fixed in 10.9.0.0.1 (INFERRED — ADO 1834035 tag); or convert users to Instant type |
| Users in OKTA group but **not appearing in group / in FLOWCAL User Security** | OKTA third-party sync bug, or user added to group before profile finished creating | §6 | QCloud resets/repairs the user profile (26-01091655, 26-01092668, 26-01121397) |
| OKTA: "**An object with this field already exists**" creating a user | Deactivated account with same email hidden from default People view | §6 | Search *Everyone*/deactivated views; delete old account or reactivate (26-01099589) |
| OKTA admin **can't see certain groups/users** other admins see | Admin-group membership / group-visibility config | §6 | Compare the two admins' OKTA permissions; ADO 1854930 (26-01119149) |
| "**All licenses in use**" but nobody is on | Stuck CrypKey process/files, not real seat exhaustion | §8 | Kill `crp32002.ngn`, delete crypkey files, relicense (26-01109161, 25-01037058) |
| TESTit "**Policy Date File out of sync**" at login from some servers | Broken CrypKey **MK links** on one or more Citrix servers | §8 | Fix MK links on ALL Citrix servers (26-01088929) |
| TESTit/PROVEit **desktop** login failed (standalone laptop) | Local SQL Server / Password Utility problem, not identity | §9 | `sql_output.log`; Password Utility recipe (26-01087584, 25-01047256) |
| TESTit login blocked: "Exception Error occurred in **CExportUtils**: There is not enough space on the disk" | Disk full on the client machine | §9 | Free disk (advise ≥50 GB free) (25-01034176) |
| New FLOWCAL login needed / user can't see meters or lists | In-app security group membership | §10 | Security > Groups: move user Available→Selected (26-01117001); list access via List Editor Group and User Access tab |
| Can't reach client SFTP / connections blocked | Firewall/whitelist or wrong hostname-credential pairing, or client IP flagged malicious | §11 | Verify hostname↔credential pairs (26-01112648); Brightcloud check (25-01035175) |

---

## 2. How FLOWCAL-Family Access Works (QCloud-hosted, the dominant deployment)

A login failure can break at any of FOUR layers. The #1 triage mistake is resetting an OKTA password when the break is at layer 3 or 4.

```
[ L1 — Identity: OKTA (login.myquorumcloud.com) ]
   • Per-client groups, naming like  <Client>-FLOWCAL-RW-PRD,
     "<Client> External FLOWCAL RO Users PRD", Foundation-Energy-Management-LLC-FLOWCAL-RW-PRD.
   • OKTA Verify MFA. Client OKTA Admins manage their own users; Quorum Cloud Ops
     manages admin-group membership and profile repairs.
   • Some clients federate via their own SAML 2.0 IdP — Quorum CANNOT reset those
     passwords (26-01090067).
        ▼
[ L2 — Delivery: Citrix DaaS / StoreFront / FAS ]
   • Published apps: "FLOWCAL RW PRD", "FLOWCAL RO PRD", TESTit/PROVEit icons.
   • Okta storefront membership controls which tiles a user sees/launches.
   • Citrix FAS issues user certificates — stale/expired FAS certs = mass lockout
     (ADO 1840366). Citrix user profiles hold app settings (Exception Resolver
     layouts etc.) — corrupt profile = settings resets, app crashes.
        ▼
[ L3 — App authentication: FLOWCAL login ]
   • Three login types in fc_security_user: Standard (password), I = Instant Login
     (Windows/AD via Vault proxy), A = API (ADO 1834035/1834322).
   • Instant Login: flowcal.exe /instant <DBNAME>; credentials come from an
     encrypted .fcvault file managed by FLOWCAL.Vault.Configuration.exe.
   • CrypKey license check happens here too — a license failure presents as
     "can't log in" (§8).
        ▼
[ L4 — App authorization: FLOWCAL/TESTit security groups ]
   • Security > Groups (users), access lists (meters/locations scoped to lists),
     List Editor > "Group and User Access" tab, TESTit roles.
   • fc_security_user + fc_security_* tables (26-01068100).
```

Desktop/laptop TESTit & PROVEit (field techs) replace L1-L2 with a **local SQL Server** database — their "Login Failed" is nearly always the local DB or Password Utility (§9).

---

## 3. Decision Tree

```
"User cannot access FLOWCAL/TESTit/PROVEit"
│
├─ How many users?
│   ├─ ALL users, one environment → L2/L3 outage:
│   │     Citrix FAS certs (ADO 1840366) / app publish broken (26-01100706)
│   │     / license expiry-lockout (25-01042694, §8) → Cloud incident
│   └─ ONE user → continue
│
├─ Where does it fail?
│   ├─ Can't even reach OKTA / password or MFA problem
│   │     → L1: reset password + clear MFA (26-01103282); IF client is
│   │       SAML-federated, their own IT must reset (26-01090067);
│   │       duplicate-object on create → §6 (26-01099589)
│   ├─ OKTA fine, tile missing or "Cannot complete your request"
│   │     → L2: refresh Okta storefront membership + browser cache (26-01108524)
│   ├─ App launches, shows "Login Failed"/"invalid username or password"
│   │     → L3 provisioning: QCloud reprovision user (§4).
│   │       Recurring across users? demand RCA — known sync defect (§4)
│   ├─ "Instant login failed" / splash hang / Vault error → §7
│   ├─ License message ("All licenses in use", "Policy Date File", site key)
│   │     → §8
│   └─ Logs in but can't see lists/meters/screens or has TOO MANY rights
│         → L4: §10
│
└─ Desktop (no Citrix)? → §9 (local SQL Server / Password Utility / disk)
```

---

## 4. QCloud "Login Failed" — published-app user provisioning (HIGH-FREQUENCY)

**Signature:** Citrix-published TESTit or FLOWCAL app opens its own login and rejects the user — "Login Failed" or "invalid username or password". OKTA login itself worked. One user affected; others fine.

**Root cause (CONFIRMED pattern):** the QCloud provisioning that mirrors the OKTA identity into the application's user store didn't complete or went stale — WWM (whose cases recur) describe it as *"the vault not syncing with AD again"* (25-01029238) and *"a sync issue with OKTA and the database"* (25-01046564).

**Fix recipe (what Cloud actually does, verbatim from resolutions):**
1. **Reprovision the user** — remove from the app and re-add (26-01091463: "reprovisioned the user from the application & re add it again"; 25-01024919: "something did not go correctly during provisioning").
2. Or **refresh the user's membership** (26-01123583, 25-01047561 — "cloud team refreshed the membership for the user").
3. Or re-add to the correct app group (26-01120638: "readded to Whitewater Midstream TESTit RO PRD").
4. L4 support action: open a `myQuorum Cloud` Request/Incident; for repeat offenders request RCA (ADO 1758285 was WWM's incident — user was recreated, RCA requested).

**Recurrence watch:** WWM had at least three rounds (25-01029238 classified Software Defect, 25-01046564 → ADO 1758285, 26-01091463). If a client logs a third "Login Failed", classify **Software Defect (provisioning sync)**, not user error.

Related single-case variants: user reconfigured (26-01115169), remove+re-add (26-01099884), "password never expires" flag was false on an app account and Cloud set it true (26-01106962 — check this when a login breaks on a schedule), FC user not auto-generated in QCloud (25-01052542), whole-DB login failure fixed by re-licensing (25-01042694 — see §8).

---

## 5. Citrix / StoreFront / FAS layer

**Mass outage — stale/expired Citrix FAS user certificates.** July 2026 P1: users locked out of FLOWCAL RO and every myQ portal; parent incident **ADO 1840366** ("EQC - 26-01114383 - QPTM PRD Down for multiple users" — multi-product QCloud Citrix outage). Case trail: 26-01114400 ("expired or stale Citrix FAS user certificates"), 26-01114388 (Dee Prague, all myQ portals), 26-01114527 (resolved after Citrix uninstall/reinstall on the affected server), 26-01114390 (TESTit "Citrix Gateway Won't allow log-in", same parent). **Anchor:** ADO 1840366 (myQuorum Cloud, Incident, verified closed). Triage cue: multiple unrelated users + multiple products at once = FAS/Citrix, stop resetting individual passwords.

**Single-user tile failure.** "Cannot complete your request" on the PRD FLOWCAL StoreFront tile while the Okta tile shows: multiple stale OKTA accounts existed; the fix was to confirm the one active account, **refresh its Okta storefront membership**, and clear browser cache (26-01108524 — full 5-step resolution in case; parent WI 1822810 INFERRED from case text).

**App publish broken for everyone:** Cloud reinstalled the FLOWCAL RO published application (26-01100706). **Citrix Cloud lockout/password:** account reactivated, password reset, MFA cleared (26-01113295 → myQuorum Cloud WI 1839253 INFERRED; 26-01103282 → WI 1811881 INFERRED). **Password reset for SAML-federated clients is NOT ours to do** (26-01090067). **Citrix profile corruption** shows up as daily settings resets / crashing apps — profile reset fixes it (26-01098171 second issue; see also Exceptions skill §5 for ER settings resets).

**Crystal Reports in Citrix** needs read/write/modify on the app folder + Crystal runtime installed (26-01100869) — permission-shaped, not identity-shaped.

---

## 6. OKTA administration & group-sync anomalies

Routine fulfillment (route to Cloud, no investigation): add/replace OKTA admins (26-01105483, 26-01105699, 26-01097354 PROVEit, 26-01095387, 26-01068087), external-user adds (26-01093646, 26-01066627), deactivations (26-01090979), MFA device moves — the OKTA Verify "Add account to another device" QR flow is quoted in full in 26-01107029 (→ myQuorum Cloud WI 1831891 INFERRED), SOX screenshot/audit requests (26-01111102, 26-01091813, 26-01108785 → WI 1837323 INFERRED).

**Actionable anomalies:**

| Signature | Root cause | Fix | Anchors |
|---|---|---|---|
| User provisioned but not showing in OKTA group (`SCG_Victor_Lazar`, `SCG_Irene_Fuhrmann2` pattern) | **Third-party OKTA bug** — "sporadically, some users do not get properly set"; classified Software Defect | Cloud resets the profile per occurrence until OKTA fixes upstream | 26-01091655, 26-01092668 |
| New user added to groups but apps don't appear on dashboard | User was added to a group **before the user profile finished creating** | Repair profile; SOP: wait until user appears in User List before adding to groups | 26-01121397 |
| "An object with this field already exists in the current organization" on user create | Hidden **deactivated** account with same username/email | Look in Everyone/deactivated views; delete old account then recreate (confirmed) or reactivate | 26-01099589 |
| OKTA admin can't see groups/users a peer admin sees | Admin permission/visibility config mismatch | Compare the two admins' OKTA permissions; Cloud corrects membership | 26-01119149 → ADO 1854930 (verified: "[SEM] [Pembina] [PRD] [OKTA Admin not seeing all users]") |
| User "not in OKTA directory" though they exist | Two accounts w/ different emails; admin can only see one | Delete/deactivate stray account, recreate the right one, re-add to client Users group | 26-01103428 |
| User in OKTA but not in FLOWCAL User Security | Sync lag/profile issue — verify before escalating; SCG case turned out fine | Confirm in Security screen first | 26-01068046 |

Federated SSO (client's IdP → OKTA) setup guidance was delivered in 25-01048703; FLOWCAL does NOT do its own SSO handshake — see §7 note on PingFederate (26-01113463).

---

## 7. Instant Login & the Vault (FLOWCAL's SSO) — richest defect cluster

### 7.1 How it works (setup recipe, verbatim-condensed from 26-01107110 / 26-01089280 — keep for config cases)

1. SSO still needs a real DB user/pwd/db — hidden from the user. Create a proxy FLOWCAL user (e.g. `FC_SSO` / `FC_INSTANT_LOGIN`).
2. Run **`FLOWCAL.Vault.Configuration.exe`** (install dir) to store user/pwd/db in an encrypted **vault file** (`.fcvault` — ADO 1861910). Runner's Windows user must be in AD group **`FLOWCAL-VAULT-USER`**.
3. Point FLOWCAL at the vault: Settings Manager → **Instant Login Vault**; saved as an encrypted `.json` in the install folder (copyable to other installs/servers).
4. Launch shortcut: `c:\fcapps\flowcal\flowcal.exe /instant <DBNAME>`.
5. Create FLOWCAL security groups (ro-user, rw-user, ...) + matching AD groups; associate them.
6. First `/instant` login auto-creates a matching security user and assigns groups from the user's AD memberships. Removal from an AD group removes the security group at next login.

DB-side the proxy chain uses Oracle accounts **`FCSRV`**, **`svcfcinstant`**, **`fcowner`** (26-01081662). Architecture spike ADO 1861910 confirms `FlowCal.VaultConfiguration` manages "which Oracle database accounts to use as proxies for instant login users" and floats Entra ID replacement (future).

### 7.2 Failure modes

| Signature | Root cause | Fix | Anchors |
|---|---|---|---|
| Random users: "Instant Login Failed", splash screen hangs until force-closed | **Product bug**, root cause not published; log shows `LegacyLoginProxy.InstantLoginSignOnAsync()` completing then `InstantLoginPipelineSegment.ShowErrorAndClose` with `arg.Result=UnknownLegacyError` | Dev fix ported: ADO **1845898** (DEV, Closed) + **1854045** (R1090 PORT, Closed) → in 10.9 line (INFERRED). Cloud-side triage per incidents: ADO 1807973 (EIG), 1860388 (FEM, FC_FEMP, server QCPFEMFCTXZA01), 1862452 (WMN UAT) | 26-01120477 (in 1860388 title) |
| Instant Login dead in UAT **after RMAN clone from PRD** | UAT Oracle passwords replaced by PRD's; Vault now wrong | `alter user FCSRV identified by <pw> account unlock;` same for `svcfcinstant`, `fcowner` (passwords from Keeper for that env) | 26-01081662 |
| FLOWCAL→TESTit integration icon: "Vault connection error: Vault service is not found or is currently unavailable" | **`Quorum.Platform.SecretManagement.VaultApi`** not configured on the FLOWCAL server | Cloud configures VaultApi; then clean bad MSMQ data + purge audit/error queues if TI sync backed up | 26-01098171 |
| 10.9.0.0: Standard-login users blocked from `/instant` ("only instant login users can use instant login") | Regression — `dlls\cbuilderguis\CSecurityUser.cpp:697` checks `login_type != USER_TYPE_INSTANT`; login types: Standard, `I`=Instant, `A`=API | ADO **1834035** Closed, tag 10.9.0.0.1 (fixed-in INFERRED). Follow-on: API users get no proper error → ADO **1834322** (New) | case owner Johann Calvete per ADO |
| Instant Login user can't view/save Balance Explorer **custom templates** (10.5.0.13) | Open defect, under investigation since 2025 | No fix yet — workaround: use a password (Standard) account for template authoring | 25-00999986, 25-01004951 → ADO **1711912** (New/Investigation) |
| Instant Login fails only under **Azure RemoteApp / Nerdio** | **Product limitation** — Instant Login needs traditional Windows AD auth; can't read the vault under token-based auth models. Works in local/Citrix/RDP | Expected Behavior + enhancement request | 26-01090565 |
| Plains QCloud instant-login failure (long-running) | env-specific, ADO trail | ADO 1627717 (New) | 23-00878092 (config assistance; vault access) |
| Client asks "does FLOWCAL integrate with PingFederate?" | Authentication is done at the **Citrix layer** (PingFederate OIDC/RADIUS+MFA); FLOWCAL Instant Login just recognizes the authenticated Windows session — no secondary challenge | Expected Behavior — architecture is supported as-is | 26-01113463 |
| TESTit shows a **secondary login screen** for some PROD users | Users mis-set for instant/auto login | Reconfigure the users | 26-01096923 |

---

## 8. License lockouts masquerading as access issues

These arrive as "locked out"/"can't log in" but are CrypKey/licensing. Full site-key mechanics live in the Licensing skill; keep these signatures here because they mimic auth failures:

| Signature | Fix | Anchors |
|---|---|---|
| "All licenses in use" (false) on a Citrix server | End **`crp32002.ngn`** in Task Manager, delete the CrypKey files (7 of them per 26-01109161), relicense the app | 26-01109161 |
| "Locked out of FLOWCAL RO" | Remove all CrypKey files + generate a new key for the RO env | 25-01037058, 25-01026558 |
| ALL users can't log in to one FLOWCAL DB (FC_DOWP) | Re-license FLOWCAL | 25-01042694 |
| TESTit "**Policy Date File out of sync**" at login, varies by server | CrypKey **MK links** broken — fix MK links on ALL Citrix servers | 26-01088929 |
| "bad site key validation error" after a Windows software update | CrypKey **service not running** — restart it | 22-00531931 |
| TESTit serial numbers exhausted | Extend license count in **Casper** (Quorum's license/serial server; also validates PROVEit serials — outage case 23-00930662) | 26-01121753 |
| PROVEit/TESTit won't start on new Citrix env, "license issue?" | Citrix folder permissions missing, not licensing | 25-01088812 (26-01088812) |

---

## 9. TESTit / PROVEit desktop (standalone) login failures

Field-tech laptops: local SQL Server Express + app DB created by the **Password Utility**. "Login Failed" here is a DB problem.

**PROVEit/TESTit DB create fails — `Sqlcmd: Error: Microsoft ODBC Driver 17 for SQL Server: Login failed for user 'SA'`** (26-01087584, PROVEit 9.8.2 on Win11, SQL 2019/2022). Confirmed multi-step recipe (full text in case resolution — it is the canonical runbook):
1. Copy all `PasswordUtilityUI` files (`fccel.dll`, `PasswordUtility.exe(.config)`, `PasswordUtilityUI.exe(.config)`) into the field app's `bin` folder; run `PasswordUtilityUI`.
2. On failure check `<install>\Resources\Database\sql_output.log` for the SA error.
3. Apply **KB 000004569**.
4. Still failing → run `<install>\Resources\Database\__createMSDb.sql` in SSMS (update passwords in the script first if an old version — complexity requirements).
5. Re-run PasswordUtilityUI to sync app passwords; launch app.
Context: SQL 2014 engine can't install on Win11 (PowerShell V2 removed end-2025) — this recipe is the only confirmed path.

**TESTit after Windows 11 upgrade — login fails** (25-01047256): reimage + SQL Server 2022 + new registry key **`ForcedPhysicalSectorSizeInBytes`** (KB article referenced in case) + new DB via TESTit Password Utility + restore data by importing a **TIDX** from the server + recreate Task Scheduler import/export jobs + re-enter service credentials and Import File Path.

**Other desktop signatures:** login failed → full TESTit+SQL uninstall/reinstall (26-01095531); PROVEit login failure → run **Password Utility 1.4** (25-00998833); TESTit login blocked by "Exception Error occurred in CExportUtils: There is not enough space on the disk" → free disk, advise ≥50 GB (25-01034176); TESTit logs "unable to login as FCADMIN" during import processing — resolved itself after config (26-01110539, weak signal).

---

## 10. In-app security: groups, access lists, roles

**FLOWCAL security groups:** to grant a login/screen rights, Security > Groups → open group → move user **Available Users → Selected Users** (26-01117001). On-prem AD-integrated sites: user must ALSO be in the right AD group (26-01115618 — Keyera login worked only after AD group add). PPA approval rights: Settings Manager → Group permissions + System Configurations → Approval (auto-approvals) (25-01059859). User roles/privileges report → query `fc_security_user` and related security tables (26-01068100, 26-01098639).

**Access lists (FLOWCAL "lists" scoping meters/reports):**
- User can't see a list (e.g. in Exception Resolver dropdown): List Editor → select list → **"Group and User Access" tab** → add the user's security group (25-01048705).
- "CANNOT ACCESS LIST EXT2_ALL ... NOT ROLLING UP" — was actually **bad data**: invalid values written to Volume Editor user-defined fields by a prior import; NULL them, requeue Postponed records (26-01113739). Don't assume security when a list misbehaves.
- Access Lists screen sorting broken in 10.5.0.17 — Software Defect, scheduled for **10.9** (INFERRED) (25-01010699).

**TESTit roles — permission bleed (KEY expected-behavior trap):** if a user is in **two roles, permissions bleed over** — removing Create/Edit/Delete from one group does nothing while the user retains another role granting them (26-01108901, TESTit 3.18: "If you're in two different roles, the permissions will bleed over"). Check ALL role memberships before calling it a defect.

**CALC Meter security bug** — security not enforced on calc meters; resolved FC **10.3.0.23** (INFERRED) (24-00994488).

**User admin misc:** new-user template cases (26-01109953 — group names verbatim: "Third Coast Midstream External Users", "Third Coast Midstream External FLOWCAL RO Users PRD"), remove users from client groups (26-01115869), OKTA group add for support staff access to client TESTit (26-01104363).

---

## 11. Secure Gateway & network access

Secure Gateway = QCloud's brokered DB access path for client tools (SQL clients, Crystal, integrations).

- Setup/credential issuance: Cloud opens WIs per env (26-01064422 → myQuorum Cloud WIs 1775198 PRD / 1775199 UAT INFERRED; 25-01026554 Flywheel; 26-01091170 MACH; creds sent encrypted 26-01093634; UAT DB creds 26-01088988).
- **Whitelist**: client/integration IPs must be added (26-01114506); current whitelist obtainable from Cloud Secure Gateway team (26-01090432).
- Connection failures: wrong **hostname↔credential pairing** — each hostname has its own user/pwd (26-01112648); VPN resets fixed a dead connection (25-01053042 → WI 1764943 INFERRED); performance issues on exports through the gateway (26-01122450 → WI 1863942 INFERRED).
- Client's **public IP flagged malicious** in Brightcloud → Quorum blocks it; client IT must remediate their IP reputation (25-01035175).
- On-prem SFTP unreachable from QCloud: confirmed nothing blocked Quorum-side + outbound works; client network team must whitelist Quorum host (26-01116491).
- UAT launch failure needing a **certificate** delivered (25-01040726 — cert-shaped launch failures exist outside FAS too).

---

## 12. Known ADO items (verified live 2026-09-02 unless noted INFERRED)

| ADO | Project / Area | Type / State | Title (verbatim) | Relevance |
|---|---|---|---|---|
| 1845898 | Quorum | Bug / Closed | Failure to log in using Instant Login [DEV*] | Random instant-login splash hang (§7.2) |
| 1854045 | Quorum | Bug / Closed | Failure to log in using Instant Login [R1090 PORT] | 10.9 port of 1845898 — note R#### PORT convention |
| 1834035 | Quorum | Bug / Closed (tag 10.9.0.0.1) | FLOWCAL 10.9.0.0 Instant Logon issue (R109001) | Standard users blocked from instant login; `CSecurityUser.cpp:697` |
| 1834322 | Quorum | Bug / New | FLOWCAL 10.9.0.0 API login user should receive a valid error message upon login failure for instant login | API login_type 'A' UX gap |
| 1711912 | Quorum | Bug / New (Investigation) | 25-00999986--FC 10.5.0.13 - Cannot save custom templates logged in via Instant Login | Balance Explorer templates under instant login — STILL OPEN |
| 1627717 | Quorum | Bug / New | Unable to log in using instant login | Plains QCloud |
| 1861910 | Quorum | User Story / New | SPIKE - FLOWCAL SaaS Authentication | `.fcvault` / FlowCal.VaultConfiguration / Entra ID future |
| 1840366 | myQuorum Cloud | Incident / Closed | EQC - 26-01114383 - QPTM PRD Down for multiple users | July-2026 Citrix FAS cert mass lockout (multi-product) |
| 1758285 | myQuorum Cloud | Incident / Closed | 25-01046564 - WWM - TESTit PRD - Login Failed | OKTA↔DB provisioning sync defect trail |
| 1854930 | myQuorum Cloud | Request / Closed | [SEM] [Pembina] [PRD] [OKTA Admin not seeing all users] | OKTA admin visibility |
| 1807973 | myQuorum Cloud | Incident / Closed | EIG EIGER FLOWCAL - Instant Login Failed | Cloud troubleshooting doc referenced: "Flowcal: Instant Login Setup Instructions - Troubleshooting" |
| 1860388 | myQuorum Cloud | Incident / Closed | Case#26-01120477: [FEM][PRD][Foundation Energy] Instant Login Failed for Multiple Users | Contains the canonical log signature (`UnknownLegacyError`) |
| 1862452 | myQuorum Cloud | Incident / Closed | [WMN][Western Midstream Partners] Instant login failed error in FC UAT App icon | Access-request-shaped instant login failure |
| INFERRED (from SF resolution text only): 1822810, 1839253, 1811881, 1831891, 1837323, 1809689, 1827027, 1805195, 1726122, 1863942, 1775198, 1775199, 1764943 | myQuorum Cloud | — | — | Cited in case resolutions; not individually fetched |

---

## 13. Diagnostic SQL (FLOWCAL Oracle DB; run as fcowner-privileged account; env assumption: client DB, not DEV)

```sql
-- Does the user exist in FLOWCAL security, and what login type? (I=Instant, A=API, else Standard)
SELECT user_name, login_type FROM fc_security_user WHERE UPPER(user_name) = UPPER('&USERNAME');
-- (fc_security_user confirmed as the security table in 26-01068100; login_type values from ADO 1834035)

-- Instant-login proxy accounts healthy after a refresh? (26-01081662)
SELECT username, account_status, lock_date FROM dba_users
 WHERE username IN ('FCSRV','SVCFCINSTANT','FCOWNER');
-- Locked/expired after an RMAN clone → alter user ... identified by ... account unlock;
```
Verification SQL for group membership/roles beyond `fc_security_user` is **NOT YET RUN** against a live schema — table-analyst should enumerate `fc_security_%` tables on first connected case.

---

## 14. Expected-Behavior FAQ

- **"Does FLOWCAL do its own SSO / integrate with PingFederate/Okta directly?"** No. Authentication happens at the Citrix/IdP layer; FLOWCAL Instant Login just trusts the authenticated Windows session. No secondary challenge is issued — supported design (26-01113463).
- **"Instant Login doesn't work in Azure RemoteApp/Nerdio."** Product limitation, not misconfiguration — Instant Login requires traditional AD auth and cannot read the vault under token-based models. Enhancement request territory (26-01090565).
- **"Removed a permission from the group but the user still has it" (TESTit).** Users in multiple roles get the union — permissions bleed over (26-01108901).
- **"Can Quorum reset our OKTA/Citrix password?"** Only if Quorum sources the identity. SAML-federated clients own their accounts (26-01090067).
- **"Can our team force-log-off FLOWCAL users?"** In QCloud, no — Quorum can on request (26-01083842).
- **"User removed from AD group still got in via instant login."** Removal takes effect at the NEXT login — the login itself resyncs groups (26-01107110 note).
- **New-user SOP (QCloud):** create the user, WAIT until they appear in the User List, then add to groups — adding to groups first corrupts the profile (26-01121397).

---

## 15. Escalation guidance

- **Cloud Ops / myQuorum Cloud board** owns: OKTA profile repairs & admin groups, storefront membership, Citrix publish/FAS/profiles, provisioning reprovision, Secure Gateway, VaultApi config. Open an Incident (outage) or Request (fulfillment); reference the client tag pattern `[XXX][Client][ENV]`.
- **Measurement engineering (`Quorum\North America\Measurement`)** owns Instant Login product bugs (splash hang, login_type regressions, template save). Cite 1845898/1854045/1834035 lineage when filing; port bugs use the `(DEV)` / `(R#### PORT)` title convention.
- **Recurring "Login Failed" at one client** → do not close as user error; link prior cases + ADO 1758285 and demand RCA.
- **Anything mass-outage** → check for an existing 1840366-style parent incident before filing new.
- License lockouts: L4 can resolve directly with the §8 recipes (kill crp32002.ngn / MK links / relicense); site-key issuance goes to the licensing desk.

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
