---
name: improve-codebase-architecture
description: Scan a codebase for deepening opportunities, present ranked candidates, then grill through whichever one you pick.
disable-model-invocation: true
---

# Improve Codebase Architecture

A maintained adaptation of Matt Pocock's `improve-codebase-architecture` skill
([mattpocock/skills](https://github.com/mattpocock/skills), MIT — see `LICENSE` in this
directory). Re-scoped for this kit: `CONTEXT.md` means `docs/context.md`; the unavailable
`codebase-design` / `domain-modeling` skills are replaced by the vocabulary defined inline below;
the CDN-backed HTML report is replaced by a chat presentation. Runtime-specific files from the
upstream snapshot (`agents/openai.yaml`) are not carried.

Surface architectural friction and propose **deepening opportunities**: refactors that turn
shallow modules into deep ones. The aim is testability and AI-navigability.

Use this shared design vocabulary: **module**, **interface**, **depth**, **seam**, **adapter**,
**leverage**, **locality** — and the principles of the deletion test, "the interface is the test
surface", and "one adapter = hypothetical seam, two = real". Use these terms exactly in every
suggestion, and don't drift into "component," "service," "API," or "boundary." The domain
language in `docs/context.md` gives names to good seams; ADRs in `docs/adr/` record decisions
this command should not re-litigate.

## Process

### 1. Explore

**Scope before you scan: YAGNI.** Deepening a module pays off by making future changes to it
easier, so put extra weight on the parts of the codebase that have recently changed. Decide
*where* to look before you look:

- If the user named a direction (a module, a subsystem, a pain point), take it, and skip the
  inference below.
- Otherwise, walk back a good stretch of the commit history (`git log --oneline`) to find the
  codebase's hot spots, the files and areas that keep coming up, and let those paths pull your
  attention first. If the changes are scattered with no clear hot spot, widen the net.

Read the project's glossary in `docs/context.md` and any ADRs in the area you're touching first.

Then spawn a sub-agent to walk the codebase. Don't follow rigid heuristics; explore organically
and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow**, with an interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in how
  they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate
complexity, or just move it? A "yes, concentrates" is the signal you want.

### 2. Present ranked candidates

Present the candidates as a ranked list in chat. For each candidate:

- **Files**: which files/modules are involved
- **Problem**: why the current architecture is causing friction
- **Solution**: plain English description of what would change
- **Benefits**: explained in terms of locality and leverage, and how tests would improve
- **Recommendation strength**: one of `Strong`, `Worth exploring`, `Speculative`

End with a **Top recommendation**: which candidate you'd tackle first and why.

**Use the project's domain vocabulary from `docs/context.md`.** If `docs/context.md` defines
"Order," talk about "the Order intake module," not "the FooBarHandler," and not "the Order
service."

**ADR conflicts**: if a candidate contradicts an existing ADR, only surface it when the friction
is real enough to warrant revisiting the ADR. Mark it clearly (e.g. _"contradicts ADR-0007, but
worth reopening because…"_). Don't list every theoretical refactor an ADR forbids.

Do NOT propose interfaces yet. After presenting, ask the user: "Which of these would you like to
explore?"

### 3. Grilling loop

Once the user picks a candidate, use the `grilling` skill to walk the decision tree with them:
constraints, dependencies, the shape of the deepened module, what sits behind the seam, what
tests survive.

Side effects happen inline as decisions crystallize:

- **Naming a deepened module after a concept not in `docs/context.md`?** Add the term to the
  context document's terms section, creating it if needed.
- **Sharpening a fuzzy term during the conversation?** Update `docs/context.md` right there.
- **User rejects the candidate with a load-bearing reason?** Offer an ADR, framed as: _"Want me
  to record this as an ADR so future architecture reviews don't re-suggest it?"_ Only offer when
  the reason would actually be needed by a future explorer to avoid re-suggesting the same
  thing; skip ephemeral reasons ("not worth it right now") and self-evident ones.
- **Writing changes down:** record structure risks and the chosen smallest useful improvement in
  the chat summary; durable decisions become ADRs by the normal process.
