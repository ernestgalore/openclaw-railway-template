# UI And API Debugging Map

Use this reference when the task is an owner/admin or worker issue and you need to decide whether the problem is CLI usage, frontend wiring, or backend behavior.

## Triage Order

1. Reproduce with the owner CLI if the workflow is owner/admin-facing.
2. If the CLI works, inspect the frontend API client and the route/component.
3. If the CLI and UI fail the same way, inspect the backend route, dependency layer, and service.

## Frontend Context Files

- Auth destination resolver: `frontend/lib/utils/routing.ts`
- Post-auth restaurant hydration: `frontend/lib/hooks/usePostAuthRedirect.ts`
- App restaurant storage: `frontend/lib/hooks/useRestaurant.ts`
- Page guard: `frontend/lib/hooks/usePageGuard.ts`
- API client: `frontend/lib/api/client.ts`

## Main Owner/Admin Screens

- Admin home: `frontend/app/[locale]/admin/page.tsx`
- Daily operations: `frontend/app/[locale]/admin/daily/page.tsx`
- Worker directory: `frontend/app/[locale]/admin/workers/page.tsx`
- Wages: `frontend/app/[locale]/admin/wages/page.tsx`
- Settings: `frontend/app/[locale]/admin/settings/page.tsx`
- Scheduling: `frontend/app/[locale]/admin/schedules/page.tsx`
- Restaurant selector: `frontend/app/[locale]/select-restaurant/page.tsx`
- Login: `frontend/app/[locale]/auth/login/page.tsx`

## Main Worker Screens

- Worker home: `frontend/app/[locale]/worker/page.tsx`
- Worker clock: `frontend/app/[locale]/worker/clock/page.tsx`
- Worker tips: `frontend/app/[locale]/worker/tips/page.tsx`
- Worker history: `frontend/app/[locale]/worker/history/page.tsx`

## Backend Entry Points

- CLI implementation: `backend/app/tools/owner_cli.py`
- Auth and role dependencies: `backend/app/api/dependencies.py`
- Employees: `backend/app/api/v1/employees.py`
- Invitations: `backend/app/api/v1/invitations.py`
- Tips: `backend/app/api/v1/tips.py`
- Reports: `backend/app/api/v1/reports.py`
- Wage routes: `backend/app/api/v1/wages`

## Common Failure Patterns

- CLI succeeds, UI fails:
  frontend wiring bug, stale client state, or wrong restaurant context in browser storage.
- CLI and UI both fail:
  backend permission, validation, route, or service bug.
- CLI and UI show different restaurant data:
  verify `owner-cli restaurants current` and the app's `restaurant-storage` state before going deeper.
