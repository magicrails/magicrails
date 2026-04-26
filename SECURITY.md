# Security Policy

## Supported versions

| Version | Security fixes |
|---------|----------------|
| `0.1.x` | ✅ |
| `< 0.1` | ❌ |

While Magicrails is in `0.x`, only the latest minor version receives fixes.

## Reporting a vulnerability

**Please do not open a public GitHub issue for security reports.**

Email **masketir84000@gmail.com** with:

- A description of the issue.
- Steps to reproduce, or a minimal repro snippet.
- The Magicrails version and Python version you tested on.
- Any suggested fix or mitigation, if you have one.

Acknowledgement target: within 72 hours.
Fix target for high-severity issues: within 7 days, or a publicly tracked timeline if the fix is non-trivial.

## What is in scope

- Bypasses of the guard contract — for example, a way to make `BudgetCeiling` under-count a real bill, or a way to make `RepeatCallGuard` miss a same-args repeat.
- Adapter bugs that misreport token usage in a way that causes silent overspend.
- Webhook handler bugs that leak credentials, hostnames, or arbitrary memory into the outgoing JSON payload.
- Bugs in pricing-table loading that allow a crafted `models.json` to cause arbitrary code execution or a denial of service.

## What is out of scope

- False positives or false negatives in the detectors. Those are real bugs — please file them as regular issues.
- Stale prices in `models.json`. Please open a regular pricing-update PR.
- Vulnerabilities in third-party LLM SDKs (OpenAI, Anthropic, etc.). Report those upstream.
- Misuse of the on-trip `webhook` action by the user (e.g., posting to an attacker-controlled URL). Magicrails does what you tell it to with webhook URLs; check your config.
- Magicrails being used as a compliance or audit tool. It is not one. Use a purpose-built policy/audit layer for that.

## Coordinated disclosure

If you have an embargoed fix you would like to coordinate, mention "embargo" in the subject line of your email and we will agree on a timeline before any public commit, release, or advisory is published.

## Credit

If you would like public credit in the release notes for a reported issue, say so in your report. We will use the name and link you provide. If you prefer to remain anonymous, that is fine too.
