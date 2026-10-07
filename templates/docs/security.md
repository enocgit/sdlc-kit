# Security

> STATUS: TEMPLATE — fill at Stage 0 and delete this marker.
> The current trust boundaries and how they are defended. Update it in the change that moves a
> boundary. Review records live in `docs/security/records/`.

## Trust boundaries

| Boundary | Who crosses it | Threat | Control | Verified by |
| --- | --- | --- | --- | --- |
| {e.g. public API → database} | {anonymous user} | {reads another user's data} | {row ownership check} | {test name or record} |

## Baseline controls

<!-- Only controls code or CI enforces today. Candidates: every entry point checks identity and
     permission; input is validated at the boundary and output encoded; secrets come from the
     environment, never code or logs; personal data stays out of logs; CI scans dependencies. -->

- {control enforced today, or "none yet"}

## Records

<!-- Newest first. One row per security-review record; empty until the first review runs.
     Row: | YYYY-MM-DD | change or PR | count by severity, or none | open count | [`records/file.md`](./security/records/file.md) | -->

| Date | Change | Findings | Open | Record |
| --- | --- | --- | --- | --- |
