# Security

> STATUS: TEMPLATE — fill at Stage 0 and delete this marker.
> The current trust boundaries and how they are defended. Update it in the change that moves a
> boundary. Review records live in `docs/security/records/`.

## Trust boundaries

| Boundary | Who crosses it | Threat | Control | Verified by |
| --- | --- | --- | --- | --- |
| {e.g. public API → database} | {anonymous user} | {reads another user's data} | {row ownership check} | {test name or record} |

## Baseline controls

- Every entry point checks identity and permission.
- Input is validated at the boundary; output is encoded.
- Secrets come from the environment or a secret manager, never code or logs.
- Personal data is minimized and kept out of logs.
- Dependencies are scanned for known vulnerabilities in CI.

## Records

<!-- Newest first. One row per security-review record. -->

| Date | Change | Findings | Open | Record |
| --- | --- | --- | --- | --- |
| YYYY-MM-DD | {change or PR} | {count by severity, or none} | {count, or 0} | [`records/{file}.md`](./security/records/{file}.md) |
