# SKILL — FLOWCAL Family: FLOWCloud & Hosted Operations (QCloud)

> **Auto-Bot skill — built by Aditya Bhagat.**
> Sources: Salesforce all-history mining (Product_list__c IN 'FLOWCAL','TESTit','PROVEit'; Case_Category__c 'FLOWCloud' 972 cases + FTP/QCloud/portal keyword clusters; 15 resolved cases detail-sampled 2026-09-02) + ADO org `QuorumSoftware`, primarily project `myQuorum Cloud` (Incident/Problem/Request "Global Cloud Ops" types).
> Scope: QCloud-hosted FLOWCAL/TESTit environments — env down, Citrix published apps, OKTA/SAML federation sign-in, hosted SFTP/FTP file transfer, hosted DB access policy, portal access. PII redacted; client codes retained.
> Golden join key: Cloud Ops work items are usually titled with the SF case number (`26-01105935 - Dominion WEXPRO - ...`) or `[<CODE>] [<CLIENT>] [<ENV>] [<symptom>]`.

---

## 1. Quick Triage

| Symptom | Likely cause | § |
|---|---|---|
| "PRD is down for all users" / FLOWCAL won't come up (hosted) | QCloud-side outage or stale license on the Citrix app server | §3.1 |
| App "stopped working" during launch from QCloud service | QCloud outage — Cloud incident ticket | §3.1 |
| Hosted FLOWCAL/TESTit "not accessible" before an upgrade window | App needs relicensing on the QCloud Citrix server | §3.1 |
| Users can't sign in via OKTA / login.myquorumcloud.com | OKTA account state or federation cert — check which | §3.2 |
| ALL users locked out at once | Expired customer SAML/Azure federation certificate | §3.2 |
| "SAML certificate expiring on <date>" | Planned cert renewal — coordinate upload with Cloud team | §3.2 |
| One user can't log in to any myQ portal app | Individual OKTA account issue → reprovision access | §3.2 |
| SFTP down after QCloud maintenance window | Patching broke FTP servers / Bitvise service | §3.3 |
| "Error reading SSH protocol banner ... Connection reset by peer" | Bitvise SSH server hung — restart it | §3.3 |
| Bitvise license-expiry popup on SFTP box | Bitvise server license lapsed on that VM | §3.3 |
| Can't connect to newly provisioned SFTP / new on-prem SFTP | Firewall whitelist missing (usually client side) | §3.3 |
| SFTP password rejected / can't change password | Reset by Cloud team per client password policy | §3.3 |
| Import files missing from FTP folder / files disappearing | FTProot pathing/permissions or retention — Cloud team | §3.3 |
| App opens TWICE per click on the .ICA file | Citrix published-app misconfig — burns 2 licenses per user | §3.4 |
| Citrix published app missing for some users | App not published to the user's group / OKTA group gap | §3.4 |
| Client wants direct DB access, FCOWNER rejected | FCOWNER is prohibited — issue a read-only DB user | §3.5 |
| Imports stopped + meters locked + "abnormal program termination" | App/DB-tier fault on hosted env — Software Defect path | §3.6 |
| Imports "Out of Memory" on hosted env | Server resources/defect — check host sizing (8 GB is below spec) | §3.6 |

---

## 2. Decision Tree

```
Hosted (QCloud) FLOWCAL/TESTit issue?
├─ Whole env down / won't launch
│   ├─ Multiple apps + portal also down → QCloud outage → Cloud incident (§3.1)
│   ├─ Only FLOWCAL/TESTit launch fails, portal OK → suspect license state on the
│   │   Citrix app server → Cloud team relicenses (see Licensing skill §3.1) (§3.1)
│   └─ Wrong server targeted after re-provision? → verify FQDN in Env Delivery Report (§3.1)
├─ Sign-in problem
│   ├─ Everyone at that client, simultaneously → federation/SAML cert expired → client uploads
│   │   new Azure cert, Cloud applies (§3.2)
│   ├─ One user → OKTA account state → reprovision/unlock (§3.2)
│   └─ New-user setup / external user → OKTA group + Citrix access request, routine ops (§3.2)
├─ File transfer (SFTP/FTP)
│   ├─ Broke right after maintenance → restore FTP servers + update/restart Bitvise (§3.3)
│   ├─ SSH banner / connection reset → restart Bitvise on the SFTP VM (§3.3)
│   ├─ New endpoint unreachable → firewall whitelist BOTH directions; verify from outside
│   │   Quorum network before blaming client (§3.3)
│   └─ Credentials → reset per client password policy (§3.3)
├─ Citrix behavior (double-launch, missing icons, renames) → Cloud/Citrix team (§3.4)
├─ DB access request → read-only user, never FCOWNER (§3.5)
└─ App-functional failure that happens to be hosted (imports OOM, locked meters)
    → treat as normal product investigation (imports/services skills), hosted only changes
      WHO executes the fix (§3.6)
```

Gate mapping: §3.1-§3.5 are almost all **G2 Config** (env/infra config) or **Platform/ops** (not a product defect — classify as Config with Cloud-executed fix, or Expected Behavior for access requests). §3.6 routes to the normal G4/G5 paths of other skills.

---

## 3. Symptom clusters

### 3.1 Environment down / app won't launch (hosted)

**Signature.** "Our prod FLOWCAL does not come up. It is down for all users" during close (SF 26-01088091); "Application 'stopped working' during initiation from the QCloud service" (SF 26-01084055); "FLOWCAL and TESTit applications are currently not accessible" pre-upgrade (ADO 1816405, MOM UAT); generic "Connection Lost"/"FLOWCAL Outage" (SF 26-01067536, 26-01067559 — both Root_Cause = Cloud Outage).

**Root causes (anchored):**
1. **QCloud infrastructure outage** — resolved by Cloud with an incident ticket; support's job is coordination + confirmation (SF 26-01084055 "This was an outage on the QCLOUD side... resolved it with an incident ticket"; SF 26-01088091 confirmed relaunch).
2. **Stale CrypKey license on the hosted Citrix app server** — Cloud team relicenses FLOWCAL and/or TESTit and the env comes back (ADO 1816405 — both apps relicensed on `QCUMOMFCTX501`; ADO 1818569 — FC DOW PRD relicensed from `QCPDOWFCTXZA01.qcloud.com`; ADO 1846739 — SCG UAT relicensed on `QCUSCGFCTX501.qcloud.com`). Full recipes in SKILL_FLOWCAL_Licensing_CrypKey §3.1.
3. **Wrong/decommissioned server in play after re-provisioning** — SCR PRD: correct server was `QCPSCRFCTXZA02.QCLOUD.COM`, the ZA01 box was shut down and pending deletion; always confirm the FQDN from the **Env Delivery Report** in the provisioning work item (ADO 1868581, referencing provisioning WI 1835463).
4. **Undersized host** — SCG UAT performance/launch complaints; Cloud noted "8 GB is not enough for FLOWCAL to run smoothly and it is in our system requirements" (ADO 1846739).

**Fix recipe:**
1. Confirm scope (one user vs all; one app vs portal-wide). Portal-wide → §3.2 cert check first.
2. Open/locate the Cloud Ops work item in project `myQuorum Cloud` titled with the SF case number; tag `Cloud Resolution`.
3. Ask Cloud to check the app server (CPU/mem graphs are standard attachments — ADO 1846739) and relicense if launch errors are license-flavored.
4. Verify server FQDN against the Env Delivery Report before any action (ADO 1868581).
5. Get user confirmation, capture the Cloud incident/WI ID in the SF case.

**Env vocabulary (CONFIRMED):** hosts `QCP<CLIENT>FCTX*` (PRD) / `QCU<CLIENT>FCTX*` (UAT) on domain `.qcloud.com`; DB hosts like `QCPFLDSQLZA09.QCLOUD.com\<INSTANCE>`; env names `<CLIENT>_PRD319FLD_TESTIT`; gMSA service accounts `svc<CLIENT>Meas<ENV>` (e.g. `svcDSUMeasPRD`); SFTP accounts `ftp-<CLIENT>-<ENV>-TESTit` (ADO 1810419 — DSU PRD delivery details).

### 3.2 OKTA / SAML federation sign-in

**Signature.** "FC: Okta Login issue" / "Error signing in" bursts (SF 26-01086687, 26-01086681, 26-01086702, 26-01086694 — a 4-case cluster in one week, all Root_Cause = Platform); "FLOWCAL - All users locked out" (SF 26-01082481); "Quorum Cloud SAML Certificate Expiration" (SF 26-01079264); "QCloud Federation - Kinder Morgan Azure Certificate Renewal URGENT" (SF 26-01113331); single user can't reach any myQ portal app (SF 26-01114388, 26-01102731).

**Root causes (anchored):**
- **Expired customer-side federation certificate** — client's Azure/SAML signing cert lapses → every federated user locked out. Fix: client uploads/provides the new cert, Quorum applies it. SF 26-01082481: "They uploaded a new Azure cert, and the users were able to login." SF 26-01113331 resolved live on a call. SF 26-01079264 is the proactive-renewal variant (client asked whether Base64 or Federated XML format is needed — Cloud team answers per IdP). ADO 1804648 = SF 26-01097791 (APL): SSO SAML cert renewal for `login.myquorumcloud.com`, impact listed as "access to Quorum portal, which contains Commpass and Flowcal, myQuorum web apps".
- **Individual OKTA account state** — QCloud reprovisioned the user's access (SF 26-01102731); one-user-locked-out ≠ cert issue.
- **Federation onboarding/misconfig** — users missing the "Profile sourced by SAML 2.0 idP" tag in OKTA aren't federated; new email domains must be added to the federation (ADO 1832643, Devon/Coterra). Federation setup flow: client IdP provides 2 URLs + signing certificate → Quorum builds the SAML IdP app in OKTA (ADO 1610260 KMI; 1549489 Maverick — note: disabling a user in client Azure does NOT auto-disable the OKTA QCloud account; 1675827 — the federation guide is written for Azure AD, other IdPs like Cisco DUO are best-effort).
- **OKTA group gaps** — access to the Citrix-published app is via OKTA groups (`<Client>-<Product>-RW/RO-<ENV>` style; e.g. "Delta States Utilities TESTit RW PRD", external-vendor variants — ADO 1810419). Missing group = missing app or "can't access" (SF 26-01064310 pattern, §3.4).

**Fix recipe:**
1. Scope test: all users at the client → cert; one user → account; new users only → group/federation membership.
2. Cert path: get the new cert from client IdP admin (Azure: Base64 cert from the enterprise app), Cloud Ops applies; verify with a live login.
3. Track renewals proactively — cert-expiry cases recur annually per client (SF 26-01079264 filed ~2 weeks pre-expiry; treat as high priority, deadline-driven).
4. Single user: Cloud reprovisions OKTA access (SF 26-01102731); check "Profile sourced by SAML 2.0 idP" tag when the client is federated (ADO 1832643).

### 3.3 Hosted SFTP / FTP file transfer

**Signature.** SCADA/CFX/GQ import files flow through per-client SFTP; failures block imports. Cases: "UAT SFTP Down After QCLOUD Maintenance" (SF 26-01101235); "Not able to connect to FLOWCAL SFTP" with "SSHException: Error reading SSH protocol banner [Errno 104] Connection reset by peer" (ADO 1673058 = SF 24-00966494, TC Pipeline); "Bitvise license expiry notification pops up" on the SoCalGas UAT SFTP box (SF 26-01107627); "Cannot change password on SFTP site housftp02.qbsol.net" (SF 26-01104615, EQT); "FTP Server Connection issue with the newly provisioned FTP" (SF 26-01103221); "Unable to connect to new on prem SFTP" (SF 26-01116491); "CFM SFTP shared files site has lost files" (SF 25-01062236); AutoSol→UAT SFTP errors (SF 26-01107500).

**Root causes (anchored):**
- **Patching/maintenance broke the FTP tier** — "a patching activity affected the FTP UAT servers, so we restored the FTP UAT servers and then we had to update the Bitvise SSH server" (SF 26-01101235). After every QCloud maintenance window, SFTP is a known casualty.
- **Bitvise SSH server hung/stopped** — restart Bitvise on the SFTP VM (`QCPFCFSZA01` in ADO 1673058); control panel shows zero client connections when hung.
- **Bitvise license expiry on the VM** — license-expiry popup at connect (SF 26-01107627); Cloud renews the Bitvise license.
- **Firewall/whitelist gaps for new endpoints** — for a client-hosted (on-prem) SFTP, QCloud verified nothing was blocked on the Quorum side and could connect from OUTSIDE the Quorum network → the client's network team had to whitelist Quorum's host (SF 26-01116491). Same class for newly provisioned Quorum-side FTP (SF 26-01103221).
- **Credential/policy issues** — password resets done by Cloud per the client's password requirements (SF 26-01104615); shared-file "lost files" was a permissions issue fixed by Cloud (SF 25-01062236).

**Fix recipe:**
1. Did a maintenance window just occur? → Cloud restores FTP servers + updates/restarts **Bitvise SSH Server** (SF 26-01101235, ADO 1673058).
2. Connection-reset/banner errors → restart Bitvise; check Bitvise Server Control Panel for active connections (ADO 1673058).
3. New endpoint unreachable → bidirectional connectivity test; from outside Quorum network if client-hosted (SF 26-01116491); collect exact client source IPs for whitelist.
4. Credentials → Cloud resets per client policy, shares securely (SF 26-01104615).
5. Missing/lost files → permissions audit by Cloud (SF 25-01062236); for import-file cleanup requests (`FTProot` folders per DB, e.g. "FTProot for import in FLOWCAL RW PROD-FC_CFLP2 Database", SF 26-01117213) route to Cloud ops as routine.
6. Vocabulary: Quorum-side SFTP hosts observed: `housftp02.qbsol.net` (support/exchange SFTP), `QCPFCFSZA01` (FLOWCAL customer SFTP VM), per-client accounts `ftp-<CLIENT>-<ENV>-TESTit` (ADO 1810419). The FcDataBoss VM has its own SFTP credentials (SF 25-01006379).

### 3.4 Citrix published-app behavior

**Signature.** "Applications in the UAT environment open twice when clicking on an ICA file" — every launch consumed two licenses, users had to close the extra instance (SF 25-01057567 description verbatim; ADO 1770875 titles it "Applications launch twice, issue when the license count exceeds the limit"). Older twin: GPL TESTit — double-launch of the executable on the server produced CrypKey failure + "policy file out of sync" (ADO 1705054 = SF 24-00994231; Citrix team fixed the double launch, apps relicensed after). Also: published app missing for a user/group ("Flowcal - Citrix portal - SEM_P2_Export App missing", SF 26-01064440; "New users missing Citrix apps" pattern), icon/naming changes ("QCLOUD: Change name on the FC/TI icon", SF 26-01085510).

**Root cause + fix (anchored):** the double-launch is a Citrix Cloud publishing config fault, not a product bug — "Our cloud team was working on this case, and they have fixed the issue" (SF 25-01057567); the executable was being invoked twice on the server (ADO 1705054 investigation). Downstream symptoms it causes: license exhaustion (§Licensing skill 3.1) and CrypKey/policy errors (§Licensing skill 3.3). Missing apps = publish-to-group / OKTA group membership fix (SF 26-01064440, App Config).

**Investigation note:** when a hosted client reports "all licenses in use" chronically, ask whether apps open twice per click BEFORE relicensing — the double-launch is upstream (SF 25-01057567 + 24-00994231 both prove the chain).

### 3.5 Hosted database access & standing ops requests

**Signature + policy (anchored):**
- **FCOWNER is off-limits to customers.** When TEG's linked-server credentials for the QCloud PRD DB started being rejected, the fix was NOT to hand over FCOWNER: "Since we do not permit customers to use FCOWNER, we created an Oracle read-only user for them. The new user account is TEG_READONLY" (SF 26-01069035). Recipe: create `<CLIENT>_READONLY` Oracle/SQL user for client BI/linked-server needs.
- Routine hosted ops handled via Cloud Ops items: add custom report to PRD (SF 26-01088864), update report logo (SF 26-01094494), Meter Rollup service queue cleanup (SF 26-01094275), restart TESTit integration services (SF 26-01096384), admin access grants (SF 26-01096392 — add new admin; SF 26-01072517), external user access (SF 26-01093032, 26-01082380). All are G2/ops — no defect investigation needed, just correct routing + evidence of completion.
- MS Fabric / replication asks from hosted DBs are pre-sales/architecture, not support (SF 26-01066880, closed No Action Taken).

### 3.6 Hosted-but-functional failures (route onward)

Hosted environment ≠ hosting root cause. Anchored examples that surfaced in the FLOWCloud clusters but belong to other skills:
- "QCloud [FC_VITP] - CRITICAL - Imports getting 'Out of Memory'" — Software Defect (SF 26-01101302) → Imports skill; check host sizing too (ADO 1846739's 8 GB note).
- "QCloud [AEO][PRD] - Imports have stopped and Users are unable to edit meters" — Software Defect (SF 26-01101011) → Imports/Services skill.
- "(QCloud) (PRD) 8 Locked Meters - Can't import CFX files - 'abnormal program termination'" — Software Defect (SF 25-01016994) → Imports skill.
- "(QCloud) (DOW) Report Service - Schedule Reports failing to send emails" — App Config (SF 26-01088879) → Reports skill.
- CALCit not working in PRD (Pembina FC_SEMP) — Cloud incident ADO 1853832 = SF 26-01117994.
Classify by the functional failure; the QCloud tag only decides WHO executes (Cloud Ops runs server-side steps).

---

## 4. Known ADO items (FLOWCloud/hosting)

| ADO ID | Type (project `myQuorum Cloud` unless noted) | Title (verbatim) | Relevance |
|---|---|---|---|
| 1770875 | Incident Global Cloud Ops | 25-01057567 - FLOWCAL & TESTit HVM UAT - Applications launch twice, issue when the license count exceeds the limit | ICA double-launch |
| 1705054 | Incident | 24-00994231 - GPL TESTit PRD and UAT - Crypkey Failure and Policy file out of sync with DB | double-launch → CrypKey chain |
| 1816405 | Incident Global Cloud Ops | [MOM] [Momentum Midstream] [UAT] FLOWCAL and TESTit applications are currently not accessible... | env down → relicense |
| 1818569 / 1818946 | Incident/Problem Global Cloud Ops | 26-01105935 - Dominion WEXPRO - FC_DOWP - All License in use | hosted relicense |
| 1788761 | Problem Global Cloud Ops | 26-01087007 - CRI - PRD - All licenses in use error | FCInit relicense request |
| 1867827 / 1868617 | Incident Global Cloud Ops | [SCR] [SILVER CREEK MIDSTREAM] [UAT & PRD] [FLOWCAL LICENSE SHOULD HAVE UNLIMITED LICENSES] (+PRD relicense) | About-file module list, QCP*/QCU* hosts |
| 1868581 | Incident Global Cloud Ops | [SCR] [...] [service import not working in RO and RW apps] | wrong server after re-provision; Env Delivery Report |
| 1846739 | Incident Global Cloud Ops | 26-01114936 - UAT - SCG - Performance issues | relicense + 8 GB below spec |
| 1810419 | Internal Activity | DSU PRD FLOWCAL to TESTit Integration Configuration | env naming, gMSA, SFTP account, OKTA groups, TESTit Integrated module |
| 1673058 | Incident | 24-00966494 TCP SFTP - Not able to connect to FLOWCAL SFTP | Bitvise restart, SSH banner error, QCPFCFSZA01 |
| 1804648 | Request Global Cloud Ops | APL - 26-01097791 - SSO SAML certificate expiring and requires update - 5/1/2026 | portal-wide cert renewal |
| 1832643 | Request Global Cloud Ops | [OKTA] [Devon Energy Corporation] [ODW] [Is Devon Federated?] | "Profile sourced by SAML 2.0 idP" diagnostics |
| 1610260 | Request | KMI - Federation with Qcloud system | federation setup flow (2 URLs + cert) |
| 1549489 | Change | Maverick Natural Resources, LLC - Integrate Azure with OKTA to Enable SSO | federation flows; disable-user caveat |
| 1675827 | Request | CUC - Chesapeake setup federated access | Azure-only federation guide caveat |
| 1853832 | Incident Global Cloud Ops | 26-01117994 - Pembina Pipeline Corporation - FC_SEMP - FLOWCAL- CALCit not working | hosted CALCit incident |

Fixed-in builds are not applicable to this skill's clusters (infra fixes, not product releases); any build references above are INFERRED context only.

## 5. Diagnostic SQL

None surfaced — every cluster here resolves through infrastructure actions (relicense, Bitvise restart, cert upload, OKTA/AD changes), not FLOWCAL schema queries. For the DB-access cluster (§3.5) the deliverable is a **read-only DB account** (`<CLIENT>_READONLY` pattern, SF 26-01069035), created by Cloud DBAs, not by support SQL.

## 6. Expected-Behavior FAQ

- **"Can we have FCOWNER credentials?"** No — policy: customers never get FCOWNER; a client-named read-only account is provided instead (SF 26-01069035).
- **"Whose job is the SAML cert renewal?"** The client's IdP admin generates/uploads the new cert; Quorum Cloud applies it. Renewals recur — calendar them (SF 26-01079264, ADO 1804648).
- **"Why can't support just fix our hosted server?"** Hosted servers are Cloud-Ops-controlled; support routes via `myQuorum Cloud` work items and the Cloud Resolution team executes (pattern across ADO 1788761, 1816405, 1846739).
- **"Disabled the user in our Azure AD — why can they still log in?"** Azure disable events do not propagate to the OKTA QCloud account automatically; request explicit deactivation (ADO 1549489).
- **"Support portal / customer portal access requests"** (add users, see cases) — routine User Administration, not investigation: route per SF 26-01123069 / 26-01070728 pattern.
- **"We use Ping/DUO, not Azure — can we federate?"** Yes if SAML-capable, but the guide is Azure-based; client IdP admin must locate their own URIs/signing cert (ADO 1675827, 1832643 — Ping IdP works).

## 7. Escalation guidance

- **Env down (PRD, during close)** → Sev-critical Cloud Ops incident in `myQuorum Cloud`, title `<SFcase> - <CLIENT> - <DB> - <symptom>`, cc Cloud Resolution; demand the incident/WI ID back into the SF case (SF 26-01084055 pattern).
- **Anything requiring hands on `*.qcloud.com` hosts** → Cloud Ops only. Always pass: client code, env (PRD/UAT), exact host FQDN from the Env Delivery Report (ADO 1868581), and the SF case number.
- **Federation/OKTA engineering** → Cloud identity team via Request Global Cloud Ops; provide IdP type, cert format, affected email domains (ADO 1832643, 1610260).
- **Repeated post-maintenance SFTP breakage** → cite SF 26-01101235 + ADO 1673058 and ask Cloud for a post-patch Bitvise health check as a standing step; this is a recurring failure mode.
- **Functional failures on hosted envs** (imports, reports, meters) → classify under the owning functional skill; hosted status only changes executor (§3.6).

---
*Investigated by Auto-Bot — the L4 issue solver built by Aditya Bhagat. Line numbers verified against live source; re-baseline against the client's build branch before coding.*
