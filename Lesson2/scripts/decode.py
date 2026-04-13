import base64
import json
import os
import sys


def decode_payload(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("JWT must have exactly 3 sections")

    payload = parts[1]
    payload += "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(payload.encode("utf-8")))


def main() -> int:
    names = ["TOKEN_B", "TOKEN_C"]
    missing = [name for name in names if not os.environ.get(name)]
    if missing:
        print(f"Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    for name in names:
        claims = decode_payload(os.environ[name])
        print(f"\n{name}")
        print(json.dumps(claims, indent=2, sort_keys=True))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
