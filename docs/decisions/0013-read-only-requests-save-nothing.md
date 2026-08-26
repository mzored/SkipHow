# ADR 0013: Read-only requests save nothing

## Status

Accepted in 1.6.1. Amends [ADR 0011](0011-findings-tag-codex-role-files-neutral-repo-instructions.md) (finding authority). [ADR 0004](0004-github-lifecycle-and-authority.md) stands and is the rule this restores.

## Date

2026-08-26

## Context

ADR 0004 grants one record per material finding with "fix" or "implement" and makes read-only requests inspection and reporting only. ADR 0011 added "saving a finding you met along the way is always within authority" to the root skill to stop findings from being dropped. The two sentences contradict each other on a read-only request, and the guide had a third reading ("while delivering"). In the [1.6 receipts](../research/2026-08-26/v1.6-receipts.md), two Codex runs given "without changing anything" wrote nothing and tagged the finding `PERSISTED`, a tag the skill does not define. The runs honored the owner's words; the contract gave them no disposition for doing so.

## Decision

- `DELIVER` and `RECORD` grant one deduplicated record per material finding. A read-only request (`RESPOND`) grants none.
- Under a read-only request a finding is reported with the tag `UNSAVED`, with the note that the owner can ask to save it. "Review this, but save any material findings" grants the record.
- The four tags are `TRACKED`, `SAVED`, `UNSAVED`, `DISMISSED`; "outside the request" remains no reason to dismiss.

## Consequences

"Do not change anything" means exactly that, including tracker and inbox writes. Findings from a review still reach the report. The README claim that findings were saved in every run is replaced by the observed count.

## Rejected alternatives

- Keeping "always within authority" and teaching the model to save under read-only requests: it makes the owner's words mean less than they say.
- Saving to the inbox but not to GitHub under read-only requests: still a change to the project.

## Revalidation triggers

Revisit when a receipt shows a read-only request writing a record, or a `DELIVER` run dropping a material finding without a tag.
