# Fix: External gas/settlement statement 'Not Enough Memory' / won't render in browser

## Steps
1. In Crystal, on the gas-statement report (GAS_STMT_WEB / RPT_GSTMT-QTIP / RPTGASSTWB-QTIP), turn OFF "Retain Original Image Color Depth" on the logo / reduce the logo's image color depth. Verbatim from 23-00886361: "This cut the file size in half and allowed the report to be generated and accessible almost immediately."
2. Raise the web file-streaming size limit for downloads. In 22-00875574 the cap was raised from 100 MB to 350 MB.
3. Apply both together: smaller rendered file + larger cap = the statement renders in the browser for external users.

## Verification
The external/producer user re-runs the gas or settlement statement from myQuorum and it renders in the browser (no "Not Enough Memory", no "Exception retrieving report files ... deserialize" error).

## Workaround
Until fixed, the statement can be generated to a network drive instead of streamed to the browser (the report itself completes; only web delivery fails).

## Source
SKILL_TIPS_CAW.md §5; SF cases 22-00875574, 23-00886361, 23-00883409.
