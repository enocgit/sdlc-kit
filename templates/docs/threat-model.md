# Threat model

> STATUS: TEMPLATE — fill during bootstrap and delete this marker.
> The current trust boundaries and how they are defended. Update it in the change that moves a
> boundary. Review records live in `docs/security/records/`.

## Trust boundaries

| Boundary | Who crosses it | Threat | Control |
| --- | --- | --- | --- |
| {e.g. public API → database} | {anonymous user} | {reads another user's data} | {row ownership check} |

## Baseline controls

<!-- Only controls code or CI enforces today. Candidates: every entry point checks identity and
     permission; input is validated at the boundary and output encoded; secrets come from the
     environment, never code or logs; personal data stays out of logs; CI scans dependencies. -->

- {control enforced today, or "none yet"}
