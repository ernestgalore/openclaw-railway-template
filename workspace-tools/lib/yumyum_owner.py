#!/usr/bin/env python3
"""
Thin Yumyum owner helper CLI for OpenClaw workspaces.

The CLI reads a seeded owner state file and uses the saved bearer token plus the
default restaurant context from that state. It is intentionally small and uses
only the Python standard library so it can run inside the Railway image.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request


DEFAULT_STATE_CANDIDATES = [
    os.environ.get("YUMYUM_OWNER_STATE_PATH", "").strip(),
    os.path.expanduser("~/.config/yumyum-owner-cli/state.json"),
    "/data/.config/yumyum-owner-cli/state.json",
]


def iso_from_epoch(epoch_value: int | None) -> str | None:
    if not epoch_value:
        return None
    return dt.datetime.fromtimestamp(epoch_value, dt.timezone.utc).isoformat()


def resolve_state_path(explicit_path: str | None) -> pathlib.Path:
    candidates = []
    if explicit_path:
        candidates.append(explicit_path)
    candidates.extend(path for path in DEFAULT_STATE_CANDIDATES if path)

    for candidate in candidates:
        path = pathlib.Path(candidate).expanduser()
        if path.exists():
            return path

    joined = ", ".join(candidates)
    raise SystemExit(f"Could not find Yumyum owner state. Checked: {joined}")


def load_state(explicit_path: str | None) -> tuple[pathlib.Path, dict]:
    state_path = resolve_state_path(explicit_path)
    try:
        return state_path, json.loads(state_path.read_text())
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {state_path}: {exc}") from exc


def require_state_fields(state: dict) -> tuple[str, str, str]:
    api_url = (state.get("config", {}).get("api_url") or "").strip().rstrip("/")
    token = (state.get("session", {}).get("access_token") or "").strip()
    restaurant_id = (state.get("context", {}).get("restaurant_id") or "").strip()

    missing = []
    if not api_url:
        missing.append("config.api_url")
    if not token:
        missing.append("session.access_token")
    if not restaurant_id:
        missing.append("context.restaurant_id")
    if missing:
        raise SystemExit(f"State file is missing required fields: {', '.join(missing)}")

    return api_url, token, restaurant_id


def substitute_restaurant_id(path_value: str, restaurant_id: str) -> str:
    return path_value.replace("{restaurant_id}", restaurant_id)


def build_url(api_url: str, restaurant_id: str, path_value: str, query_pairs: list[tuple[str, str]] | None = None) -> str:
    normalized = substitute_restaurant_id(path_value, restaurant_id)
    if not normalized.startswith("/"):
        normalized = "/api/v1/" + normalized.lstrip("/")
    url = api_url + normalized
    if query_pairs:
        query_string = urllib.parse.urlencode(query_pairs)
        if query_string:
            separator = "&" if urllib.parse.urlparse(url).query else "?"
            url = f"{url}{separator}{query_string}"
    return url


def api_request(
    *,
    method: str,
    url: str,
    token: str,
    payload: dict | list | None,
) -> tuple[int, object]:
    data = None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method.upper())
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            payload = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            payload = {"detail": raw}
        return exc.code, payload
    except urllib.error.URLError as exc:
        raise SystemExit(f"Request failed: {exc}") from exc


def parse_json_payload(raw_payload: str | None, payload_file: str | None) -> dict | list | None:
    provided = [value for value in [raw_payload, payload_file] if value]
    if len(provided) > 1:
        raise SystemExit("Use either --data or --data-file, not both.")

    if raw_payload:
        try:
            return json.loads(raw_payload)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON for --data: {exc}") from exc

    if payload_file:
        path = pathlib.Path(payload_file).expanduser()
        try:
            return json.loads(path.read_text())
        except FileNotFoundError as exc:
            raise SystemExit(f"JSON file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc

    return None


def print_json(obj: object) -> None:
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def parse_common_args(argv: list[str]) -> tuple[argparse.Namespace, argparse.ArgumentParser]:
    parser = argparse.ArgumentParser(description="Scoped Yumyum owner helper")
    parser.add_argument("--state-path", help="Override the owner state JSON path")
    parser.add_argument(
        "--restaurant-id",
        help="Override the restaurant context from the state file",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("whoami", help="Show the current owner and restaurant context")
    subparsers.add_parser("restaurant", help="Get the current restaurant details")
    subparsers.add_parser("employees", help="List employees for the current restaurant")
    subparsers.add_parser("policies", help="Get policies for the current restaurant")
    subparsers.add_parser("schedules", help="List schedules for the current restaurant")

    inventory_parser = subparsers.add_parser("inventory", help="Inspect inventory resources")
    inventory_parser.add_argument(
        "resource",
        choices=["categories", "items", "suppliers", "restock-requests", "counts"],
    )

    for method in ["get", "post", "put", "patch", "delete"]:
        method_parser = subparsers.add_parser(method, help=f"{method.upper()} an API path")
        method_parser.add_argument("path", help="Path relative to the API root or a full /api/v1/... path")
        method_parser.add_argument("--data", help="Inline JSON request body")
        method_parser.add_argument("--data-file", help="Path to a JSON request body file")
        method_parser.add_argument(
            "--query",
            action="append",
            default=[],
            metavar="KEY=VALUE",
            help="Append a query parameter",
        )

    return parser.parse_args(argv), parser


def parse_query_pairs(raw_pairs: list[str]) -> list[tuple[str, str]]:
    query_pairs = []
    for raw_pair in raw_pairs:
        if "=" not in raw_pair:
            raise SystemExit(f"Invalid --query value: {raw_pair}. Expected KEY=VALUE.")
        key, value = raw_pair.split("=", 1)
        query_pairs.append((key, value))
    return query_pairs


def main(argv: list[str] | None = None) -> int:
    args, _parser = parse_common_args(argv or sys.argv[1:])
    state_path, state = load_state(args.state_path)
    api_url, token, default_restaurant_id = require_state_fields(state)
    restaurant_id = (args.restaurant_id or default_restaurant_id).strip()
    if not restaurant_id:
        raise SystemExit("No restaurant_id available.")

    if args.command == "whoami":
        user = state.get("session", {}).get("user", {})
        print_json(
            {
                "statePath": str(state_path),
                "apiUrl": api_url,
                "restaurantId": restaurant_id,
                "user": {
                    "id": user.get("id"),
                    "email": user.get("email"),
                    "phone": user.get("phone"),
                    "fullName": user.get("user_metadata", {}).get("full_name"),
                },
                "expiresAt": iso_from_epoch(state.get("session", {}).get("expires_at")),
                "hasRefreshToken": bool(state.get("session", {}).get("refresh_token")),
            }
        )
        return 0

    shortcut_paths = {
        "restaurant": f"/api/v1/restaurants/{restaurant_id}",
        "employees": f"/api/v1/restaurants/{restaurant_id}/employees",
        "policies": f"/api/v1/restaurants/{restaurant_id}/policies",
        "schedules": f"/api/v1/restaurants/{restaurant_id}/schedules",
    }

    if args.command == "inventory":
        url = build_url(
            api_url,
            restaurant_id,
            f"/api/v1/restaurants/{restaurant_id}/inventory/{args.resource}",
        )
        status_code, response = api_request(method="GET", url=url, token=token, payload=None)
        print_json(response)
        return 0 if status_code < 400 else 1

    if args.command in shortcut_paths:
        url = build_url(api_url, restaurant_id, shortcut_paths[args.command])
        status_code, response = api_request(method="GET", url=url, token=token, payload=None)
        print_json(response)
        return 0 if status_code < 400 else 1

    query_pairs = parse_query_pairs(getattr(args, "query", []))
    payload = parse_json_payload(getattr(args, "data", None), getattr(args, "data_file", None))
    url = build_url(api_url, restaurant_id, args.path, query_pairs)
    status_code, response = api_request(
        method=args.command.upper(),
        url=url,
        token=token,
        payload=payload,
    )
    print_json(response)
    return 0 if status_code < 400 else 1


if __name__ == "__main__":
    raise SystemExit(main())
