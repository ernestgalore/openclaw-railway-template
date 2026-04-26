# Dama Owner Access

This workspace includes a scoped helper CLI for the Dama restaurant owner context.

Use `yumyum-owner` for authenticated Yumyum actions. It reads the seeded owner
state from `~/.config/yumyum-owner-cli/state.json` and defaults to the restaurant
stored there.

Read-first commands:

- `yumyum-owner whoami`
- `yumyum-owner restaurant`
- `yumyum-owner employees`
- `yumyum-owner schedules`
- `yumyum-owner policies`
- `yumyum-owner inventory categories`
- `yumyum-owner inventory items`
- `yumyum-owner inventory suppliers`

Generic API access:

- `yumyum-owner get '/api/v1/restaurants/{restaurant_id}/employees'`
- `yumyum-owner post '/api/v1/restaurants/{restaurant_id}/inventory/suppliers' --data '{"name":"Example"}'`
- `yumyum-owner put '/api/v1/restaurants/{restaurant_id}/employees/<employee_id>' --data '{"canSchedule":true}'`

Safety notes:

- This auth is owner-scoped for Dama. Treat writes as real production actions.
- Prefer reading current state before mutating data.
- The seeded state currently has no refresh token. If requests start failing with
  `401`, the owner state needs to be reseeded.
