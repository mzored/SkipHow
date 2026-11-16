# Accepted margin report plan

This synthetic plan is the canonical accepted source for the margin report rebuild. All known product
decisions are settled, and the owner's interview answers are recorded here. Its task records have been
written, sized for one agent each, and independently reviewed against the accepted source evidence.

The accepted scope rebuilds the monthly margin report in repository `margin-report`. The agreed destination is
a verified, reviewed implementation candidate on local branch `feature/margin-report`, published into the
owner's shared report spreadsheet. The owner granted writing that one spreadsheet and local commits; the grant
excludes the source ledgers, other spreadsheets, and remote Git.

Task MR-1 corrects how deferred costs move between months and verifies the result against the accepted
worked examples. Task MR-2 rebuilds the report layout from MR-1's results and checks it against the accepted
sample. Task MR-3 writes the checked report into the shared spreadsheet and confirms what reached it while
keeping the owner's manual edits there. MR-2 consumes MR-1's result; MR-3 consumes MR-2's.

The spreadsheet connection this session used for research has expired. MR-3 needs the owner to reconnect it
before it can write. MR-1 and MR-2 do not use the spreadsheet. No other preparation prerequisite remains.
