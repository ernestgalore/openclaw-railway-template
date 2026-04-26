# Yumyum Owner Access

This workspace is configured to operate the Yumyum tips backend
as the seeded owner account.

## CLI

The supported tool is `owner-cli`, installed system-wide from the
vendored `yumyum-owner-cli` wheel. State lives at
`~/.config/yumyum-owner-cli/state.json` and is seeded at boot from
the `YUMYUM_OWNER_STATE_JSON_B64` Railway env var (config + session +
restaurant context). Refresh tokens auto-rotate; no interactive login
is needed for normal use.

## Authoritative reference

Use the `yumyum-owner-operations` skill (auto-discovered by OpenClaw
under `/data/.openclaw/skills/`). It documents the canonical product
surfaces, supported commands, operating rules, and safety guardrails.

## Quick smoke checks

```
owner-cli version
owner-cli auth whoami
owner-cli restaurants current
owner-cli operations          # list dedicated action commands
```

## Generic API access

When no dedicated command exists, fall back to the authenticated
request helper:

```
owner-cli request GET  /api/v1/restaurants/{restaurant_id}/employees
owner-cli request POST /api/v1/restaurants/{restaurant_id}/inventory/suppliers \
  --data '{"name":"Example"}'
owner-cli request PUT  /api/v1/restaurants/{restaurant_id}/employees/<id> \
  --data '{"canSchedule":true}'
```

## Safety notes

- Auth is owner-scoped for the seeded restaurant. Treat writes as real
  production actions.
- Read state before mutating. Run `owner-cli restaurants current` and
  `owner-cli auth whoami` first when in doubt.
- If requests start failing with 401, the refresh token in the seeded
  state has expired and `YUMYUM_OWNER_STATE_JSON_B64` needs re-seeding.
