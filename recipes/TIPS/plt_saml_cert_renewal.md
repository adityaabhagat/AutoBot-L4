# Fix: Renew the expiring Entra ID SAML signing certificate for 'Okta - Quorum Software' SSO

## Steps
1. In the client's Azure portal, open the Single sign-on page for the "Okta - Quorum Software" enterprise app; under SAML Signing Certificate choose Create new certificate (duration up to 3 years).
2. Make the new certificate active and Save (rolls over the existing cert).
3. Download the new certificate and upload it to the Okta - Quorum Software app (the Quorum/Cloud Ops side adds the new SSO authentication).
4. Confirm the customer can log in before closing - there may be brief SSO downtime during the roll, so schedule it. Both sides (client Entra AND Quorum Okta) must hold the new cert; per 25-01034697: "Added the new SSO authentication on the customer's side and ours and confirmed the customer could login."

## Verification
A client user completes an SSO login through Okta after the roll; no further "certificate is going to expire" notices for this app.

## Workaround
None - if the certificate expires before the roll, SSO breaks for every user at that client until the new cert is in place on both sides.

## Source
SKILL_TIPS_Security_UserAdmin.md §8; SF case 25-01034697 (Merit Energy).
