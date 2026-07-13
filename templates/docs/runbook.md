# Runbook

> How the system is operated: deploy, roll back, observe, and respond. Keep current as
> infrastructure changes.

## Environments

**GitHub Flow:** `main` is always deployable. Environments are *deploy targets*, not long-lived
branches — promote the same build artifact forward rather than merging between branches.

| Env | URL | Deployed from | When |
|-----|-----|---------------|------|
| Preview | per-PR URL | the PR branch | automatically on each PR |
| Staging | {url} | `main` | on every merge to `main` |
| Prod | {url} | `main` (tagged release) | on promotion / release |

## Deploy

<!-- Exact steps / command / pipeline. Who can deploy. -->

## Rollback

<!-- How to revert a bad release fast. The single most important section here. -->

## Observability

- **Logs:** {where, how to query}
- **Metrics/dashboards:** {links}
- **Alerts:** {what pages whom}
- **Health checks:** {endpoints}

## Common incidents

| Symptom | Likely cause | First response |
|---------|--------------|----------------|
| {symptom} | {cause} | {action} |

## Secrets & access

<!-- Where secrets live, how to rotate, who has access. Never commit secrets. -->
