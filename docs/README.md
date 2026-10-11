# Documentation

## Use SkipHow

- [Owner guide](guide.md): installation, activation, updates, requests, optional workflows, and reports.
- [FAQ](faq.md): fit, limits, and common questions.
- [Evidence](evidence.md): supported claims, receipt requirements, dated observations, and unverified behavior.
- [Security and host support](../SECURITY.md): private reporting and the dated capability matrix.

## Understand or contribute

- [Owner-outcome contract](outcome-contract.md): the product responsibilities implementations must preserve.
- [Design](design.md): the current package, kernel, workflows, and host boundary.
- [Decisions](decisions.md): current rationale, premises, and conditions for reopening a choice.
- [Prior art](prior-art.md): adopted ideas and rejected alternatives.
- [Contributing](../.github/CONTRIBUTING.md) and [repository instructions](../AGENTS.md): development and delivery rules.
- [Evaluation corpus](../evals/README.md): discovery cases, behavioral scenarios, fixtures, and retained receipts.
- [Changelog](../CHANGELOG.md): changes in the current major series.

## Repository map

| Directory | Purpose |
| --- | --- |
| `plugins/skiphow/` | The installable package shared by Codex and Claude Code |
| `docs/` | Current user, product, design, and evidence documentation |
| `evals/` | Evaluation data, synthetic projects, and retained run evidence |
| `tests/` | Offline deterministic tests |
| `scripts/` | Contributor checks, capture, grading, and privacy tools |
| `site/` | The static website published by the release workflow |
| `.github/` | Contribution policies, issue templates, and CI workflows |

The root host catalogs and contributor settings stay at the paths their hosts read.
The dogfood skill is contributor tooling, outside the installable package.

## Historical material

The following material is preserved at pre-cleanup commit
`72aef4540d30d3639a2f63af6663971345c6dc5a`. It describes earlier packages or completed
launch work and is not current procedure.

- [Decision narratives and earlier archives](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/decisions.md).
- [Complete historical evidence ledger](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/evidence.md).
- [Changelog through 6.3.3](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/CHANGELOG.md).
- [Completed discoverability and launch plan](https://github.com/mzored/SkipHow/blob/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/discoverability.md).
- [Historical presentation and usage notes](https://github.com/mzored/SkipHow/tree/72aef4540d30d3639a2f63af6663971345c6dc5a/docs/presentation).

Retained receipt files remain in this checkout so offline integrity and claim checks
continue to work. An archived observation applies only to the package and conditions
it names; it does not establish behavior on a newer release.
