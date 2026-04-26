# Owner CLI Flows

Use this reference when you already know the task belongs in the YumYum owner/admin skill and you need the fastest supported CLI path.

## First Checks

```bash
scripts/owner-cli config show
scripts/owner-cli auth whoami
scripts/owner-cli restaurants current
scripts/owner-cli operations
```

If you installed the standalone tool, replace `scripts/owner-cli` with `owner-cli`.

## Auth And Bootstrap

Normal owner flow:

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

Internal-only assumed session:

```bash
railway run --service tips-api --environment production -- \
  scripts/owner-cli auth assume --email owner@example.com
```

Notes:
- Prefer `auth login` for normal use.
- `auth assume` is only for trusted internal environments that already have Railway and Supabase secrets.
- `auth refresh` will not work for assumed sessions because they do not have refresh tokens.

## Restaurant Context

Check and set the CLI restaurant context:

```bash
scripts/owner-cli restaurants list
scripts/owner-cli restaurants select RESTAURANT_ID
scripts/owner-cli restaurants current
```

Important:
- The CLI restaurant selection is stored in local CLI state.
- The web app stores `currentRestaurant` separately in browser storage.
- When the CLI and app disagree, verify both contexts before assuming a backend bug.

## Common Operations

Profile and roles:

```bash
scripts/owner-cli profile get
scripts/owner-cli profile update --field preferredLocale=he
scripts/owner-cli profile roles
```

Workers — prefer name-based commands; the CLI resolves `--employee` and `--invitation` locally (exact → case-insensitive → substring; errors on 0 or ambiguous matches with a candidate list):

```bash
scripts/owner-cli workers list --query status_filter=active
scripts/owner-cli workers list-invites
scripts/owner-cli workers find "<full or partial name>"
scripts/owner-cli workers find-invite "<name or email>"
scripts/owner-cli workers invite --field fullName="Test Worker" --field email="worker@example.com"
scripts/owner-cli workers update --employee "<name>" --field fullName="Updated Worker"
scripts/owner-cli workers add-position --employee "<name>" --field jobTypeId=JOB_TYPE_ID --field wageRate=38
scripts/owner-cli workers delete --employee "<name>" --dry-run
```

Tips and attendance:

```bash
scripts/owner-cli tips sessions --query session_date=2026-04-21
scripts/owner-cli tips session-by-date --date 2026-04-21 --session-name morning
scripts/owner-cli tips session-entries SESSION_ID --field 'cash={"amount":1200}' --field 'credit={"amount":2500}'
scripts/owner-cli attendance auto-clockout --query hours=12
scripts/owner-cli daily summary --date 2026-04-21
```

Payroll — always call `wages finalize-preview` before `wages finalize`:

```bash
scripts/owner-cli wages calculate --field period_start=2026-04-01 --field period_end=2026-04-30
scripts/owner-cli wages payroll-overview --query period_start=2026-04-01 --query period_end=2026-04-30
scripts/owner-cli wages finalize-preview --period-start 2026-04-01 --period-end 2026-04-30
scripts/owner-cli wages finalize --field period_start=2026-04-01 --field period_end=2026-04-30 --field expected_run_id=DRAFT_RUN_ID --field expected_inputs_hash=DRAFT_INPUTS_HASH
scripts/owner-cli wages reopen --field period_start=2026-04-01 --field period_end=2026-04-30
scripts/owner-cli wages runs --query period_start=2026-04-01 --query period_end=2026-04-30
```

`finalize-preview` returns a `ready_to_finalize` flag and, when true, the exact `wages finalize` command to run. Never call `wages finalize` unless `ready_to_finalize` is true.

Reports:

```bash
scripts/owner-cli reports monthly \
  --query period_start=2026-04-01 \
  --query period_end=2026-04-30 \
  --query format=xlsx \
  --query calculation_run_id=FINALIZED_RUN_ID \
  --output ./reports/april.xlsx
```

`--output PATH` is available on every wrapped command. Use it for binary formats (xlsx, csv) and to archive JSON snapshots (for example `wages payroll-overview --output ./snapshots/payroll-april.json`). The legacy `request ... --output` still works but is no longer the preferred form.
