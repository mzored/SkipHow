# Product spec

Use this when the owner asks to settle what they want before work starts. [Product decisions](product-decisions.md) owns the asking. This owns what the answers become. It runs on their request rather than on your judgment that a result was broadly stated. That case is already theirs to ask about and yours to record as the agreed outcome.

## What comes out

What comes out is a document the owner can read back, not a summary in the conversation. It belongs where this project keeps tracked work, as the parent of the units that carry it out, so that continuing does not depend on this conversation surviving.

## The vocabulary

Settle the vocabulary before the outcomes. List the things this product talks about, one entry each, in the owner's own term, with what it means here and what it is not. One term, one meaning. Where the same word covers two things, or two words cover one, the spec cannot be checked, and delegates carrying it out will each pick a reading and both write it.

Where the owner's word and the code's word differ, the record uses theirs and names the code's once beside it. This list is the part that survives longest, because it is what a session weeks later reads first.

## The outcome and the decisions

State the outcome as what a person using the product will be able to do, and the condition that would show it true, observable in the product rather than in the code. [Decomposition](decomposition.md) turns that into units. Do not do its work here, and do not prescribe files, structure, or steps.

Record each decision the owner made with what it settled, the option they turned down, and what reversing it would cost. An option they were never told about is one they cannot revisit. A decision written without its alternative reads later as a fact about the product rather than a choice somebody made. Record what stays open the same way, naming who has to settle it.

Say what is deliberately out of scope. The thing most likely to be built by mistake later is the thing nobody wrote down as absent on purpose.

## What does not belong

Keep engineering out of it. Settle libraries, schemas, interfaces, and branch and test strategy without asking. They do not belong in a document the owner is meant to check. Ask nothing here that reading the project, its records, or a current source would answer.

## When to stop

Stop when nothing material is open. This is not an interview that runs until a design tree is exhausted. The rounds end where [product decisions](product-decisions.md) ends them, and a spec still growing after the outcome is settled is spending the owner's attention for nothing.
