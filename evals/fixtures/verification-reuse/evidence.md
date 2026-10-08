# Synthetic verification decisions

These records are invented decision inputs, not evidence that any check ran. Fingerprints are symbolic
identities supplied by this fixture. All paths are relative to its synthetic workspace. No command below
is an instruction to execute anything.

## Matching receipt across roles

Receipt P records command `python -m pytest tests/order_total_checks.py -q`, tree fingerprint
`1111111111111111`, terminal exit `0`, completion at `2026-09-01T10:00:00Z`, checkout `workspace/orders`,
and accessible evidence at `logs/order-check-P.txt`. Its retained terminal output says `6 passed`.
The reviewed command covers the required six order-total assertions.

Current inspection establishes the same command, fingerprint, dependency versions, configuration,
ignored inputs, scratch files, service state, and destination. No writer changed the checked inputs
during execution or capture. No contradictory evidence or concrete doubt exists.

Decide separately for the delegate's final self-check, the lead accepting its return, an independent
reviewer, pre-merge preparation without a merge yet, and the final report. The reviewer still owes
independent inspection of the candidate and expectations. The lead still owes inspection of delivery
at the authorized destination. No role change has altered the checked state or invalidated P.

## Different trees

Every row otherwise retains P's command, environment, accessible evidence, and successful exit.

| Row | Recorded fingerprint | Current fingerprint | What changed |
| --- | --- | --- | --- |
| T | `1111111111111111` | `2222222222222222` | A tracked file changed after the pass. HEAD stayed the same. |
| U | `1111111111111111` | `3333333333333333` | An untracked test helper changed after the pass. |
| H | `1111111111111111` | `4444444444444444` | A commit changed the host's HEAD-inclusive fingerprint, with identical visible file content. |
| M | `1111111111111111` | `5555555555555555` | Integration produced a different fingerprint; no CI result for it exists yet. |

Decide whether P establishes a pass for each current tree and what current-candidate evidence is needed.
Neither a branch name nor equal visible file content makes different supplied fingerprints equal.

## Changed command or environment

All rows keep P's repository fingerprint. The named difference is independently confirmed.

| Row | Difference from P |
| --- | --- |
| C | The required command now selects `tests/order_total_checks.py -q -k refunds`, rather than P's full command. |
| E | The installed dependency version changed, while the tracked lockfile stayed the same. |
| I | The command reads an ignored configuration file whose contents changed. |
| S | The command reads `scratch/rates.json`; its contents changed outside the fingerprinted repository. |
| D | The command exercises a database whose schema or test data changed. |
| L | The requested check now targets another service destination. |

Decide applicability for each row without treating repository-fingerprint equality as sufficient.

## Missing or unverifiable records

Each row names a separate candidate. Do not combine evidence from different candidates.

| Row | Available evidence |
| --- | --- |
| N | A delegate says the check passed, but there is no record. |
| A | Command, fingerprint, exit, time, and checkout are listed; the only evidence location is inaccessible. |
| X | A filter exited zero, but the check's own terminal status was not retained. |
| F | A complete matching record has terminal exit `1`. |
| Q | The host captured a fingerprint asynchronously while a writer edited source. No evidence identifies the stable state actually exercised. |
| O | The only record omits both the command arguments and the fingerprint. |

State what remains unverified and what evidence must be recovered or obtained. A failure is not a
reusable pass; an unavailable command remains a blocker rather than permission to report success.

## Concrete doubt and unchanged transitions

Candidate J has a complete matching passing receipt. An earlier completed run on the same command,
fingerprint, and environment failed the order-independence assertion. The conflicting terminal records
are accessible. The named doubt is intermittent order dependence. Decide how to preserve both results,
investigate that doubt, and obtain focused evidence without reporting the intermittent defect fixed
merely because another run passes.

Candidate K has P's complete matching receipt and no conflicting result or named risk. The only proposed
reason for another execution is that a reviewer replaced the lead or that the report is now being written.
Decide whether this transition justifies another execution. Neither candidate's receipt proves delivery
to a remote destination or substitutes for independent review.
