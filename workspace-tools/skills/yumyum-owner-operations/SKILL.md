---
name: yumyum-owner-operations
description: Use when working on YumYum owner or admin operations, especially when you need to operate the system through the supported owner CLI, validate behavior against the admin or worker app, or reproduce operator workflows without editing the database directly.
metadata:
  author: yumyum
  version: "1.0.0"
---

# Yumyum Owner Operations

Use this skill for owner and admin workflows in this repo.

Typical triggers:
- create or update workers, positions, invitations, tips, holidays, payroll, reports, schedules, or inventory through supported product surfaces
- reproduce an owner/admin bug with the real CLI or compare CLI behavior with the app
- verify restaurant-scoped permissions or current owner workflows

## Canonical Product Surfaces

- Owner and admin UI: `/[locale]/admin`
- Daily operations UI: `/[locale]/admin/daily`
- Worker UI: `/[locale]/worker`
- Worker history: `/[locale]/worker/history`
- Worker clock: `/[locale]/worker/clock`
- Worker tips: `/[locale]/worker/tips`
- Supported operator CLI: `scripts/owner-cli` in-repo, or installed `owner-cli`
- Owner/admin files: `frontend/app/[locale]/admin/page.tsx`, `frontend/app/[locale]/admin/daily/page.tsx`, `frontend/app/[locale]/admin/wages/page.tsx`
- Auth and restaurant files: `frontend/app/[locale]/auth/login/page.tsx`, `frontend/app/[locale]/select-restaurant/page.tsx`, `frontend/lib/hooks/usePageGuard.ts`, `frontend/lib/utils/routing.ts`

Do not use retired routes like `/owner`, `/worker/monthly-report`, or `/admin/attendance`.

## Operating Rules

- Prefer the owner CLI for real owner and admin operations and smoke tests.
- Prefer the app UI when the task is specifically about UX, wording, layout, or button wiring.
- When debugging, check the CLI first, then `frontend/lib/api/client.ts`, then the route/component, then the backend endpoint/service.
- Do not bypass the product with direct database edits when a supported CLI or API path exists.
- For normal owner use, use `auth login`.
- Use `auth assume` only when the user explicitly wants trusted internal operator access from an environment that already has Railway and Supabase secrets.
- Confirm the current restaurant before mutating data. If needed, run `restaurants current`, `restaurants list`, and `restaurants select`.
- The CLI restaurant selection and the app restaurant selection are different persisted contexts. Cross-check both before assuming a backend mismatch.
- Treat report downloads and binary outputs as files. Use `--output PATH` directly on the wrapped command (for example `reports monthly --output ./reports/april.xlsx`). `request ... --output` still works but is no longer the preferred form.
- Structured command results are JSON by default.
- Be careful with destructive worker actions, invitation cancellation, payroll finalization, and cache clearing. Confirm intent if the consequence is not easily reversible.

## First Checks

Read [docs/OWNER_CLI.md](docs/OWNER_CLI.md) for command coverage and examples.
See [references/owner-cli-flows.md](references/owner-cli-flows.md) for the quickest supported command bundles.
See [references/ui-api-debugging.md](references/ui-api-debugging.md) for route and API file maps.

Start with:

```bash
scripts/owner-cli config show
scripts/owner-cli auth whoami
scripts/owner-cli restaurants current
scripts/owner-cli operations
```

If using the installed standalone command, replace `scripts/owner-cli` with `owner-cli`.

## Authentication And Context

Preferred normal flow:

```bash
scripts/owner-cli auth login --env-file /tmp/yumyum-frontend.env --email owner@example.com
```

Standalone install flow:

```bash
owner-cli config set \
  --api-url https://tips-api-production.up.railway.app \
  --supabase-url https://YOUR_PROJECT.supabase.co \
  --supabase-anon-key YOUR_PUBLIC_SUPABASE_ANON_KEY
owner-cli auth login --email owner@example.com
```

Restaurant selection:

```bash
scripts/owner-cli restaurants list
scripts/owner-cli restaurants select RESTAURANT_ID
scripts/owner-cli restaurants current
```

If the account has exactly one restaurant, the CLI may already auto-select it after login.
`auth refresh` will not work for assumed sessions because they do not store a refresh token. Re-run `auth assume` instead.

## High-Value Commands

Profile and roles:

```bash
scripts/owner-cli profile get
scripts/owner-cli profile update --field preferredLocale=he
scripts/owner-cli profile roles
```

Workers — prefer name-based commands over raw UUIDs. `--employee` and `--invitation` resolve locally against the workers/invitations list (exact → case-insensitive → substring; 0 or ambiguous matches error with a candidate list):

```bash
scripts/owner-cli workers list --query status_filter=active
scripts/owner-cli workers list-invites
scripts/owner-cli workers find \"<full or partial name>\"
scripts/owner-cli workers find-invite \"<name or email>\"
scripts/owner-cli workers invite --field fullName=\"Test Worker\" --field email=\"worker@example.com\"
scripts/owner-cli workers update --employee \"<name>\" --field fullName=\"Updated Worker\"
scripts/owner-cli workers add-position --employee \"<name>\" --field jobTypeId=JOB_TYPE_ID --field wageRate=38
scripts/owner-cli workers delete --employee \"<name>\" --dry-run
```

Tips and attendance:

```bash
scripts/owner-cli tips sessions --query session_date=2026-04-21
scripts/owner-cli tips session-by-date --date 2026-04-21 --session-name morning
scripts/owner-cli tips session-entries SESSION_ID --field 'cash={\"amount\":1200}' --field 'credit={\"amount\":2500}'
scripts/owner-cli attendance auto-clockout --query hours=12
scripts/owner-cli daily summary --date 2026-04-21
```

Payroll — always run `wages finalize-preview` before `wages finalize`:

```bash
scripts/owner-cli wages calculate --field period_start=2026-04-01 --field period_end=2026-04-30
scripts/owner-cli wages payroll-overview --query period_start=2026-04-01 --query period_end=2026-04-30
scripts/owner-cli wages finalize-preview --period-start 2026-04-01 --period-end 2026-04-30
scripts/owner-cli wages finalize --field period_start=2026-04-01 --field period_end=2026-04-30 --field expected_run_id=DRAFT_RUN_ID --field expected_inputs_hash=DRAFT_INPUTS_HASH
scripts/owner-cli wages reopen --field period_start=2026-04-01 --field period_end=2026-04-30
scripts/owner-cli wages runs --query period_start=2026-04-01 --query period_end=2026-04-30
```

`finalize-preview` returns `ready_to_finalize` plus the exact `wages finalize` command. Never call `wages finalize` unless `ready_to_finalize` is true.

Reports:

```bash
scripts/owner-cli reports monthly \
  --query period_start=2026-04-01 \
  --query period_end=2026-04-30 \
  --query format=xlsx \
  --query calculation_run_id=FINALIZED_RUN_ID \
  --output ./reports/april.xlsx
```

`--output PATH` is available on every wrapped command. Use it for binary formats (xlsx, csv) and to archive JSON snapshots like `wages payroll-overview --output ./snapshots/payroll-april.json`.

## Debugging Guidance

When CLI and app disagree:

1. Check the CLI result first to learn whether the backend data and permissions are correct.
2. Check the matching frontend API client in [frontend/lib/api/client.ts](frontend/lib/api/client.ts).
3. Check the active admin or worker route under [frontend/app/[locale]/admin](frontend/app/[locale]/admin) or [frontend/app/[locale]/worker](frontend/app/[locale]/worker).
4. Cross-check both restaurant contexts: CLI selected restaurant and app `restaurant-storage`.
5. If the CLI works and the UI does not, treat it as a frontend wiring or state bug.
6. If both fail the same way, inspect the backend route and service.

Good backend entrypoints to inspect:
- [backend/app/tools/owner_cli.py](backend/app/tools/owner_cli.py)
- [backend/app/api/dependencies.py](backend/app/api/dependencies.py)
- [backend/app/api/v1/employees.py](backend/app/api/v1/employees.py)
- [backend/app/api/v1/invitations.py](backend/app/api/v1/invitations.py)
- [backend/app/api/v1/tips.py](backend/app/api/v1/tips.py)
- [backend/app/api/v1/reports.py](backend/app/api/v1/reports.py)
- [backend/app/api/v1/wages](backend/app/api/v1/wages)

## Safety Notes

- Never put `auth assume` in a normal owner workflow.
- Never use service-role credentials or the Supabase JWT secret outside trusted internal operator environments.
- Do not finalize payroll casually. Always check blockers first.
- When clearing data or deleting workers, call out permanence clearly.
