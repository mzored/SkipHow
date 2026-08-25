# Technical review

Use independent review when requested, required by repository policy, or justified by security, public contracts, large integration changes, weak evidence, or repeated failure.

## Bind review to the candidate

Identify the repository, base tree or commit, committed candidate tree or head commit, clean-state proof, effective diff hash, submodule identities when present, and the evidence configuration used for the verdict. For a pull request, record its exact head.

Dirty files, submodule changes, a new head, untracked executable inputs, or any relevant byte change invalidate the affected review evidence. A diff hash supplements the candidate identity. It does not replace it.

## Review on two axes

The Spec axis checks missing, partial, incorrect, and unrequested behavior against the owner request and accepted product decisions.

The Standards axis checks repository instructions, security boundaries, compatibility, failure paths, maintainability, and relevant design defects. Add a specialist lens only when the changed area needs it.

Inspect the delivered state and effective diff. Do not review an obsolete snapshot or trust a worker receipt as proof. A fresh reviewer is useful when the host supports one, but it does not replace tests.

Every material finding names evidence, affected behavior, impact, and one disposition:

- `RESOLVED` for a fixed in-scope defect;
- `PERSISTED` for a separate actionable finding saved once;
- `DUPLICATE` for an existing equivalent record;
- `DISMISSED` when evidence rejects or supersedes the claim.

Separate confirmed defects from risks, investigations, and suggestions. Severity follows impact, not style preference.

After a fix, re-review the finding, its fix diff, and plausible regressions. Repeat the full review only when the fix changed architecture, product behavior, a protected area, or enough of the candidate to invalidate the earlier verdict.
