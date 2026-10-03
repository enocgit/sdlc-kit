---
name: webapp-testing
description: Toolkit for interacting with and testing local web applications using Playwright. Supports verifying frontend functionality, debugging UI behavior, capturing browser screenshots, and viewing browser logs.
license: Complete terms in LICENSE.txt
---

# Web Application Testing

A maintained adaptation of Anthropic's `webapp-testing` skill
([anthropics/skills](https://github.com/anthropics/skills), Apache-2.0 — see `LICENSE.txt` in
this directory). Re-scoped for this kit: the bundled server-lifecycle script and its examples
are not carried, and readiness waits are app-specific. To test local web applications, write
native Python Playwright scripts.

**Server lifecycle is the project's own.** Start the app with the project's lifecycle runner or
attach to an already-running server, so output is drained and the process tree stays owned by
the project's tooling — this skill does not bundle a server manager. Wait for an app-specific
readiness signal (a locator appearing, a URL change, or a health check); never rely on a
mandatory global network-idle wait.

**Scope:** UI/browser checks only — skip for backend-only changes. For mobile apps, use a
platform runner such as Maestro or Detox instead.

## Decision Tree: Choosing Your Approach

```text
User task → Is it static HTML?
    ├─ Yes → Read HTML file directly to identify selectors
    │         ├─ Success → Write Playwright script using selectors
    │         └─ Fails/Incomplete → Treat as dynamic (below)
    │
    └─ No (dynamic webapp) → Is the server already running?
        ├─ No → Start it with the project's lifecycle runner, then use the
        │        reconnaissance-then-action pattern below
        │
        └─ Yes → Reconnaissance-then-action:
            1. Navigate and wait for an app-specific readiness signal
            2. Take screenshot or inspect DOM
            3. Identify selectors from rendered state
            4. Execute actions with discovered selectors
```

## Example: Minimal dynamic-app check

Start the server the way the project starts it (dev server, compose service, platform runner),
then drive the app:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:3000/login")
    page.get_by_label("Email").fill("user@example.com")   # readiness: the locator appears
    page.get_by_label("Password").fill("correct-horse")
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("**/dashboard")
    page.screenshot(path="/tmp/after-login.png", full_page=True)
    browser.close()
```

## Reconnaissance-Then-Action Pattern

1. **Inspect rendered DOM** (after the readiness signal):
   ```python
   page.screenshot(path='/tmp/inspect.png', full_page=True)
   content = page.content()
   page.locator('button').all()
   ```

2. **Identify selectors** from inspection results

3. **Execute actions** using discovered selectors

## Best Practices

- Use `sync_playwright()` for synchronous scripts
- Always close the browser when done
- Use descriptive selectors: `text=`, `role=`, CSS selectors, or IDs
- Add appropriate waits: `page.wait_for_selector()` for a specific element, or an explicit
  health check for the app under test
