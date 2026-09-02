# Fix: QEMAIL stopped after an environment refresh - reset the email global config

## Steps
1. Open Configuration Setting (Global) for the environment and set the email keys for this env:
   - `EMAIL_USERNAME`
   - `EMAIL_PASSWORD`
   - `EMAIL_HOSTNAME`
2. Restart QPEC so the process picks up the new values (for an outgoing-address change, restart services likewise - 23-00916973).
3. SMTP settings reference: QuorumSoftware wiki "SMTP Configurations for sending emails" (23-00922562).
4. Related notification controls if the complaint is about email content/behavior rather than failure: events are configured on the Event Detector Setup screen (Maintenance > Notifications); `SEND_EMAIL_ON_CANCEL=0` stops cancel-notice emails; the `ATTSIZERR` event configures large-attachment notifications.

## Verification
QEMAIL runs without erroring on its next cycle and outbound TIPS emails (statement distribution, notices) are received.

## Workaround
None - outbound email is down until the EMAIL_* keys are corrected. Note QEMAIL runs on a ~5-minute cycle: statements/exports release on the next cycle after the event is logged (26-01084450), and submissions posted within one interval merge into one email (24-00993505).

## Source
SKILL_TIPS_System_Configuration.md §7; SF cases 24-00944285, 22-00693503, 23-00916973, 23-00922562; SKILL_TIPS_Reporting_Statements.md §5 (24-00993505, 26-01084450).
