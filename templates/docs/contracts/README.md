# Contracts

> STATUS: TEMPLATE — list the real contract artifacts at Stage 0 and delete this marker.

Contracts are artifacts in the codebase (OpenAPI files, schemas, typed routers, event schemas), not
prose. Both sides generate or share types from them; neither side hand-copies them.

Freeze a contract only when a consumer outside this repo, listed in `docs/context.md`, cannot change
in the same PR. Changing a frozen contract needs human approval and a re-freeze; one with a deployed
consumer also needs a versioning ADR.

| Contract | Artifact | Consumers | Frozen |
| --- | --- | --- | --- |
| {name} | `{path that exists in this repo}` | {who} | {yes, by change NNNN / no} |
