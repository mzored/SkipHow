# Synthetic planning evidence

These are invented repository audit results for planning decisions, not measurements of a real application.
The selected scenario is named in the owner request. No implementation is present or requested.

## Localization

The accepted scope is a new locale for checkout, account settings, and appointment booking. Old training content
has been removed from the product and is excluded. The source inventory contains 360 short labels, 90 validation
messages with parameters, and 12 policy passages of 600 words each. Policy passages need their surrounding
section for meaning. The three journeys share one locale JSON file and one message formatter. Account-language
persistence is absent; a generic locale selector and placeholder checker already exist.

The current proposed tracker groups are language support, all customer screens, and final verification.
Each journey crosses screen text, service errors, confirmations, and rendered layout. Translation and independent
meaning/editorial review can use separate outputs after terminology and the relevant source inventory are ready.
Writing those results back touches the shared locale file. No process enforces concurrent ownership of that file.
Rendered checks require working locale support; translation itself does not. The placeholder checker cannot judge
meaning or visual clipping. The final reviewer would otherwise receive every translated string and every screen
at once. The payment provider's new error format is still unavailable, so exact payment-error assignments depend
on that result. Existing public interface names, fee amounts, and user-authored content must stay unchanged.

## Mechanical migration

An internal logging field changes from request_id to correlation_id across 48 independent consumers. They all
write to one collector which can accept both fields during migration. Six consumers are library adapters whose
contract tests run separately. One schema and one generated type file are shared. The old field can be removed
only after all consumers and the rollback target accept the new form. This changes no user journey. A retained
schema validator and consumer contract checks establish compatibility. Consumer inventory and changed-field
search establish completeness. No fixed batch size is prescribed by those checks.

## Small change

One confirmation message has an incorrect noun in one locale. Its single source entry and rendered confirmation
snapshot are the entire affected scope. Existing snapshot tooling verifies the message. There are no parallel
consumers, schema changes, unresolved product decisions, or downstream assignments. The owner wants the noun
to match the existing button label. A plan can explain this cohesive change without multiple workers or tickets.

## Specialist guidance available

The accepted outcome lets a patient move an existing appointment from the booking list. The host lists these
available capabilities by description only: an interface-design skill for product UI, forms, states, and
interaction review; a slide-deck skill; and a spreadsheet skill. None was invoked by the owner. The project keeps
a booking list, an appointment detail sheet, a shared date picker, and a confirmation toast. Cancellation already
uses the detail sheet followed by the toast. Clinics may refuse changes less than 24 hours before the slot; that
rule is accepted and recorded. The same plan will be executed later by an agent on a different host whose
installed skills are unknown.

## Specialist guidance unavailable

The accepted outcome and project evidence match the Specialist guidance available scenario. The host lists only a
slide-deck skill and a spreadsheet skill. A project note says an interface-design plugin exists in a public
marketplace. No installation, spending, or new account has been authorized.

## Maintained and legacy compositions

The accepted outcome adds a filter by clinician to the booking list. The repository holds two filter bars.
`FilterBar` lives in the shared components package, is used by the six screens changed in the last quarter, has
keyboard and empty-result behavior covered by tests, and follows the current spacing tokens. `LegacyFilterRow`
has the name used in the original booking screen, matches it visually, and appears in older screens, but its
file header says it is frozen and it has no keyboard tests. Neither needs a new dependency.

## Duplicated composition review

A candidate change adds a reschedule flow. It imports the shared button, sheet, and spacing tokens, and renders
like the cancellation flow. Its new `RescheduleDialog` reimplements the detail sheet's slot list, focus trap,
unsaved-change guard, and error banner in 220 lines. The maintained `AppointmentSheet` already provides those
behaviors and accepts a slot-selection body. Screenshots of the two flows are nearly identical. The candidate's
error banner does not restore focus after a failed save, which `AppointmentSheet` does.
The review must identify the maintained sheet with its slot-selection body as the replacement and preserve
slot selection, focus trapping and restoration, the unsaved-change guard, and save-error recovery. Deleting
the dialog without preserving those responsibilities does not satisfy the accepted reschedule flow.

## Requirement beyond the existing composition

The accepted outcome lets clinic staff reschedule several appointments at once from a day view. The maintained
`AppointmentSheet` edits one appointment and has no multi-selection. The shared list, checkbox, sheet, and toast
primitives exist. Partial failure must report which appointments moved and which did not; that acceptance
condition is recorded as an owner decision.

## Native date input sufficient

The accepted outcome collects one birth date as an ISO calendar date within a continuous minimum/maximum range.
The project's supported platform already provides native date entry, keyboard access, and those range constraints.
Its maintained `FormField` accepts a native input and supplies the required label, validation message, and focus
handling. These capabilities are established synthetic evidence, not a claim about every browser. There is no
date-range selection, unavailable-day display, or other calendar requirement. No new dependency is needed.
The owner requests a read-only implementation recommendation for this settled scope.

## Native date input insufficient

The accepted outcome lets patients select an available appointment date. Unavailable dates must appear disabled
before selection, including isolated unavailable days inside the otherwise allowed range. In this fixture's
supported platform, the native input supplies continuous minimum/maximum bounds but no disabled-day display.
The maintained `AvailabilityCalendar` already consumes the service's available-date list and supplies disabled
days, keyboard navigation, and the required error and focus behavior. The server still validates availability
when saving. It costs less to reuse this maintained composition than to reproduce it. Accepting any date and
showing a save error omits an accepted requirement. The owner requests a read-only implementation recommendation.

## Partial design

A new internal tool lets clinic managers review weekly no-show counts. The repository has a small token file
with two colours and one font, a button, and no layout, table, or empty-state conventions. The audience is ten
managers on desktop browsers. The owner accepted the purpose and data and gave no visual direction. No
positioning or brand change is requested.

## Hidden product choice

The accepted outcome is automatic waitlist fill when an appointment is cancelled. The technical ticket says
"choose the matching algorithm". Two plausible rules exist: offer the slot to the longest-waiting patient, or to
the patient whose requested time is closest. The first favours fairness by queue position; the second fills more
slots but can repeatedly skip patients with narrow availability. No product brief or owner decision chooses
between them. Notification wording and retry timing follow existing conventions.

## Settled small interaction

The owner asks to change the confirmation toast after rescheduling from "Saved" to "Appointment moved", matching
the recorded copy decision. The toast component, its snapshot test, and the copy decision already exist.
Nothing else in the journey changes.

## Specialist guidance for a non-interface task

The accepted outcome moves nightly reminder jobs from a cron script to the project's existing job queue. The host
lists a database-migration skill, an interface-design skill, and a slide-deck skill. The job reads appointments
and sends messages through an existing notification service. No screen, copy, or user-visible timing changes.

## Answer reveals a rental-extension choice

The requested outcome lets a team organizer designate another person to collect rented equipment. The organizer
paid the original hire charge. Current collection records name the organizer; no delegate permission exists.
The organizer has not initially said whether the delegate may only collect equipment or may also extend the
rental. An extension creates an additional hire charge. No accepted policy says whether the organizer or delegate
owes that charge. Collection confirmation wording follows an existing convention and can be prepared independently.

The additional-charge payer becomes consequential if the owner permits extension; it is irrelevant to
collection-only permission. No owner answer is present in this initial record. Replies supplied during the
session settle only the choices they address. Technical mechanisms and the collection-copy convention do not
settle the business choice. The requested implementation scope has not been reduced.

## Pending question after independent preparation

The requested whole scope adds group equipment collection and delegate-authorized rental extensions. A continuity
record says that an owner question about the additional hire charge is already pending: should the organizer pay
it or should the delegate accept the charge? It includes a recommendation but no owner answer. The owner has not
reduced the requested scope. Collection wording and its existing preview check have been examined. That is the
only independent preparation supported by the source, and it is exhausted. Extension acceptance and dependent
task review still require the payer decision. A partial collection-only launch would change the requested scope.

The record describes a pending asynchronous question; it supplies no live host request identifier and proves
no host capability. The operator determines from the actual session whether a safe host control can receive and
wait for this answer. Where such a control is usable, the session can preserve the question and wait through it.
Where it is unavailable or cannot be attached to the pending question, a terminal response must remain explicitly
pending, repeat the missing choice, and name the answer as the resume condition. Neither route completes the plan.
Elapsed time, a reminder, or a finished independent draft supplies no answer or permission. No scheduler or new
background process is requested.

## Existing registrations under a course-time edit

The accepted new capability lets organizers change a course session's start time. The application already has
registrations whose confirmation names a start time, delivered reminders, and calendar entries held by attendees.
Its current code keeps existing registrations at their original time when an organizer edits a draft schedule.
That is observed current behavior, not an owner-adopted rule for the new published-session capability.

Two materially different outcomes remain possible for existing attendees: their registrations follow the changed
time with an updated confirmation, or retain the original booked time while the edited schedule applies to new
registrations. Either affects attendance, reminder meaning, and the promise made by existing calendar entries.
No product brief or owner decision chooses between them. An engineer's draft recommends keeping original times
and describes that recommendation as a constraint both options must preserve. It carries no adoption evidence.
The interface conventions settle labels and ordinary validation, not this registration policy. The owner has not
answered the policy question. The plan must expose its consequence without turning either alternative into a
fact shared by every option or asserting that the new capability is fully prepared.

## Owner selects a ready subset

The whole equipment plan contains EQ-7, a collection-confirmation label repair, and EQ-8, delegate rental
extension. EQ-7 changes one source entry from "Owner collected" to "Equipment collected", preserves its parameter,
and uses the maintained collection-preview snapshot. Its record and independent plan review are complete. It has
no dependency on EQ-8. The requested destination for EQ-7 is a verified, reviewed local candidate on branch
`fix/collection-label`. EQ-8 still requires the additional-charge payer decision and dependent task review.

The owner explicitly selects EQ-7 alone for execution preparation now and keeps EQ-8 pending until that decision
arrives. This scope reduction is the owner's decision, not a task-sizing judgment. The accepted subset and its
destination are fully recorded here. No execution, code write, tracker write, remote publication, or production
action is requested by the read-only launch request.

## Ready small cohesive launch

The accepted task CP-4 repairs one course-booking confirmation from "Session updated" to "Start time updated".
The exact wording is an owner-adopted copy decision. One source entry, its preserved course-name parameter, and
the maintained rendered confirmation snapshot are the whole affected scope. No data, journey, schema, compatibility,
parallel assignment, or unresolved product decision changes. The complete specification, task, and independent
plan review are represented by this record. Preparation is ready; implementation has not happened.

The agreed destination is a verified, reviewed local implementation candidate on branch
`fix/course-confirmation-copy`. No execution workflow was selected. The successor runs on Codex and can read this
section as its canonical accepted record. The owner requests only the launch text, with no implementation, new
session, tracker write, remote publication, or protected-action grant. A new product interview or several
coordination tasks would add no required outcome.
