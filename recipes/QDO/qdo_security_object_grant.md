# Fix: "Not authorized to access security object" / Save greyed out — grant the security object

## Steps
1. Identify the **security object name** from the error or the affected screen (examples seen: `QFRMDIVISIONORDERHEADERQUERY`, `QVpDashboardQDO`, `QRAWidgetAccess`, `QUCDashboardEditor`).
2. Identify the affected user's **security group** number (example from the field: group **48100** for BA/DOI header bulk-edit users). When fixing UAT, mirror PRD's group setup.
3. **Add the security object to the security group** via the standard grant script into the client metadata (`ESUITE_QFC` on this product). Field-proven example: *add `QFRMDIVISIONORDERHEADERQUERY` to security group 48100* (24-00966898).
4. Have the user re-login (or refresh cache) and retest the screen/Save button.

## Verification
- The user can open the screen without the "Not Authorized to access security object" error and the Save button is enabled.
- The group/object xref query shows the object present for the group.

## Workaround
A user in a security group that already carries the object can perform the action on the affected record until the grant is applied.

## Source
SKILL_QDO_Division_Orders.md §11. Cases: 24-00966898 (QFRMDIVISIONORDERHEADERQUERY → 48100), 23-00933550 / 23-00909049 (dashboard objects), 25-01034810 (DO007 empty for new user).
