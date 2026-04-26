#!/bin/bash
set -e

seed_file_from_b64() {
  local env_name="$1"
  local target_path="$2"
  local value="${!env_name:-}"

  if [ -z "$value" ]; then
    return 0
  fi

  umask 077
  mkdir -p "$(dirname "$target_path")"
  printf '%s' "$value" | base64 -d > "$target_path"
}

install_workspace_file() {
  local source_path="$1"
  local target_path="$2"
  local mode="$3"

  if [ ! -f "$source_path" ]; then
    return 0
  fi

  mkdir -p "$(dirname "$target_path")"
  install -m "$mode" "$source_path" "$target_path"
}

append_workspace_hint() {
  local target_path="$1"
  local marker="$2"
  local content="$3"

  if [ ! -f "$target_path" ]; then
    return 0
  fi

  if grep -Fq "$marker" "$target_path"; then
    return 0
  fi

  printf '\n\n%s\n' "$content" >> "$target_path"
}

mkdir -p /data/.codex
mkdir -p /data/.config/yumyum-owner-cli
chmod 700 /data/.codex
seed_file_from_b64 CODEX_AUTH_JSON_B64 /data/.codex/auth.json
seed_file_from_b64 CODEX_CONFIG_TOML_B64 /data/.codex/config.toml
seed_file_from_b64 YUMYUM_OWNER_STATE_JSON_B64 /data/.config/yumyum-owner-cli/state.json

mkdir -p /data/workspace
install_workspace_file /app/workspace-tools/YUMYUM_OWNER.md /data/workspace/YUMYUM_OWNER.md 0644
append_workspace_hint \
  /data/workspace/TOOLS.md \
  'owner-cli auth whoami' \
  'Yumyum owner CLI: use `owner-cli auth whoami`, `owner-cli restaurants current`, `owner-cli operations` to discover commands, or inspect `YUMYUM_OWNER.md` and the `yumyum-owner-operations` skill.'

# Install / refresh the yumyum-owner-operations skill.
# The OpenClaw runtime auto-discovers skills under /data/.openclaw/skills.
mkdir -p /data/.openclaw/skills
rm -rf /data/.openclaw/skills/yumyum-owner-operations
cp -a /app/workspace-tools/skills/yumyum-owner-operations /data/.openclaw/skills/yumyum-owner-operations

# Sweep legacy yumyum-owner helper artifacts left on the volume by
# pre-owner-cli deploys. Safe no-ops if already absent.
rm -f /data/workspace/bin/owner-cli
rm -f /data/workspace/bin/yumyum-owner
rm -f /data/workspace/lib/owner_cli.py
rm -f /data/workspace/lib/yumyum_owner.py
rmdir /data/workspace/bin /data/workspace/lib 2>/dev/null || true
rm -f /home/linuxbrew/.linuxbrew/bin/owner-cli
rm -f /home/linuxbrew/.linuxbrew/bin/yumyum-owner

chown -R openclaw:openclaw /data
chmod 700 /data

if [ ! -d /data/.linuxbrew ]; then
  cp -a /home/linuxbrew/.linuxbrew /data/.linuxbrew
fi

rm -rf /home/linuxbrew/.linuxbrew
ln -sfn /data/.linuxbrew /home/linuxbrew/.linuxbrew

rm -rf /home/openclaw/.codex
ln -sfn /data/.codex /home/openclaw/.codex
chown -h openclaw:openclaw /home/openclaw/.codex

mkdir -p /home/openclaw/.config
rm -rf /home/openclaw/.config/yumyum-owner-cli
ln -sfn /data/.config/yumyum-owner-cli /home/openclaw/.config/yumyum-owner-cli
chown -R openclaw:openclaw /home/openclaw/.config
chown -h openclaw:openclaw /home/openclaw/.config/yumyum-owner-cli

export YUMYUM_OWNER_STATE_PATH=/home/openclaw/.config/yumyum-owner-cli/state.json

# Mint a fresh owner session on every boot via `owner-cli auth assume`.
# Requires SUPABASE_JWT_SECRET (project JWT signing secret) and the
# YUMYUM_OWNER_USER_ID (Supabase auth user UUID) Railway env vars.
# The seeded YUMYUM_OWNER_STATE_JSON_B64 still provides config + restaurant
# context; this command overlays a non-expired session into the same state
# file so authed CLI calls work without operator intervention.
if [ -n "${SUPABASE_JWT_SECRET:-}" ] && [ -n "${YUMYUM_OWNER_USER_ID:-}" ]; then
  if ! gosu openclaw \
       env SUPABASE_JWT_SECRET="$SUPABASE_JWT_SECRET" \
           YUMYUM_OWNER_STATE_FILE="$YUMYUM_OWNER_STATE_PATH" \
       owner-cli auth assume \
         --user-id "$YUMYUM_OWNER_USER_ID" \
         --expires-in 86400 \
         >/dev/null 2>&1; then
    echo "[entrypoint] warning: owner-cli auth assume failed; CLI calls may need manual login" >&2
  fi
fi

exec gosu openclaw node src/server.js
