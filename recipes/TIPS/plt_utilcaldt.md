# Fix: Schedule UTILCALDT so the Confirmation Response screen populates

## Steps
1. Confirm the diagnosis: noms exist but the Confirmation Response screen is empty because `QCTRL_CONF` is not being built.
```sql
SELECT COUNT(*) FROM QCTRL_CONF     /* company + gas-day filter */;  -- 0 rows => UTILCALDT likely not running
SELECT COUNT(*) FROM QTRAN_CAL_DATE /* same filter */;               -- staging present but QCTRL_CONF empty => run UTILCALDT
```
2. Schedule (and run) the `UTILCALDT` batch process - it populates `QCTRL_CONF` from the `QTRAN_CAL_DATE` staging table (verbatim pattern from 25-01001893).
3. Restart the services so the application picks up the rebuilt tables. Nomination changes then flow to the Confirmation Response screen.
4. Watch-out (25-01002219): nominations entered WHILE the sub-process was broken may still not appear after the fix - they need a separate data restore of the missing nom-to-conf records plus another service restart. Track that as its own item.

## Verification
New nomination submissions appear on the Confirmation Response screen; QCTRL_CONF row counts grow for current gas days after each UTILCALDT run.

## Workaround
None - nothing can be confirmed (auto or manual) while the Confirmation screen is empty.

## Source
SKILL_TIPS_Nominations_Scheduling.md §8 / §15-D; SF cases 25-01001893, 25-01002219.
