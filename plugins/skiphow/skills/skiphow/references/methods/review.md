# Technical review

Use independent review when requested, required by repository policy, or justified by security, public contracts, large integration changes, weak evidence, or repeated failure. Delegate it to the `reviewer` role when the host supports it; a fresh reviewer helps but does not replace tests.

## Review the exact candidate

Name the repository, the base commit, the candidate head or tree, and the checks the verdict relies on. For a pull request, record its exact head. Dirty files, a new head, changed submodules, or untracked executable inputs invalidate the affected evidence; review the delivered state and its effective diff, never a stale snapshot or a delegate's receipt.

## Two axes

The spec axis checks missing, partial, incorrect, and unrequested behavior against the owner request and accepted decisions. The standards axis checks repository instructions, security boundaries, compatibility, failure paths, maintainability, and relevant design defects; add a specialist lens only when the changed area needs it.

Every material finding names its evidence, affected behavior, impact, and one disposition: `RESOLVED` (fixed in scope), `PERSISTED` (saved once as a separate finding), `DUPLICATE` (existing record), or `DISMISSED` (evidence rejects it). Separate confirmed defects from risks and suggestions; severity follows impact, not style.

After a fix, re-review the finding, its diff, and plausible regressions. Repeat the full review only when the fix changed architecture, product behavior, a protected area, or enough of the candidate to void the earlier verdict.
