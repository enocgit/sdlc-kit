---
name: unslop
description: Apply to human-facing communication and prose to remove AI writing tells while preserving meaning, evidence, and the intended tone.
---

# Unslop

A maintained adaptation of Cursor's pstack `unslop` skill. Apply it automatically to human-facing
communication and prose where applicable, not as a universal rule for every file or response.

## Scope

Apply this skill to agent replies, documentation, pull requests, issue text, user-facing copy, and
explanations.
Preserve meaning, factual support, technical precision, and the intended tone.

Do not apply it to code, identifiers, schemas, contracts, commands, logs, quoted text, machine-
readable output, fixed status or gate formats, byte-exact vendor snapshots, or neutral technical
records where stylistic variation would reduce clarity.

## Process

1. Read the surrounding text and identify the reader, purpose, and required facts.
2. Remove filler, puffery, vague attribution, promotional language, chatbot phrases, excessive
   hedging, and compliance narration: sentences about the agent's own permissions or constraints
   rather than an outcome, such as "I am not polling", "merging is your call", or "per the gate
   protocol". Preserve concise factual reports of actions, progress, blockers, results, deviations,
   decisions, and verification evidence; turn each narration into an ask or an outcome, or delete it.
   Prefer concrete claims and named sources.
3. Replace inflated vocabulary, abstract metaphors, passive voice, synonym cycling, forced lists,
   and dense sentences with plain, specific language.
4. Use sentence-case headings and ordinary punctuation. Avoid decorative formatting, unnecessary
   em dashes, and bold labels that merely repeat the sentence.
5. Do not add opinions, first-person voice, deliberate imperfection, or personality to neutral
   product, architectural, security, operational, or policy records.
6. Check the result for unsupported claims, changed meaning, lost constraints, and remaining filler.

Explicit requirements, accessibility, security, contracts, and factual accuracy take precedence over
style. If a fixed format requires wording or punctuation, keep the format.
