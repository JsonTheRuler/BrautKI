from __future__ import annotations

import argparse
import os
import sys


def get_missing(required: list[str]) -> list[str]:
    missing: list[str] = []
    for key in required:
        value = os.getenv(key, "").strip()
        if not value:
            missing.append(key)
    return missing


def check_gateway() -> int:
    secure_mode = os.getenv("SECURE_MODE", "false").lower() == "true"
    required = [
        "PORT",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "OPENROUTER_API_KEY",
        "AGENTS_BASE_URL",
        "COUNCIL_BASE_URL",
    ]
    if secure_mode:
        required.extend(["ADMIN_API_KEY", "GATEWAY_API_KEY", "SERVICE_SHARED_KEY"])
    missing = get_missing(required)
    if missing:
        print(f"[gateway] missing: {', '.join(missing)}")
        return 1
    print("[gateway] env preflight OK")
    return 0


def check_agents() -> int:
    secure_mode = os.getenv("SECURE_MODE", "false").lower() == "true"
    required = ["GATEWAY_URL", "DATABASE_URL", "REASONING_MODEL_ALIAS"]
    if secure_mode:
        required.append("SERVICE_SHARED_KEY")
    missing = get_missing(required)
    if missing:
        print(f"[agents] missing: {', '.join(missing)}")
        return 1
    print("[agents] env preflight OK")
    return 0


def check_data() -> int:
    required = ["DATABASE_URL", "GATEWAY_URL", "EMAIL_SOURCE"]
    missing = get_missing(required)
    if missing:
        print(f"[data] missing: {', '.join(missing)}")
        return 1

    source = os.getenv("EMAIL_SOURCE", "mock").strip().lower()
    if source == "imap":
        missing = get_missing(["IMAP_HOST", "IMAP_USERNAME", "IMAP_PASSWORD"])
        if missing:
            print(f"[data] EMAIL_SOURCE=imap missing: {', '.join(missing)}")
            return 1
    if source == "graph":
        missing = get_missing(["GRAPH_TENANT_ID", "GRAPH_CLIENT_ID", "GRAPH_CLIENT_SECRET", "GRAPH_MAILBOX_USER"])
        if missing:
            print(f"[data] EMAIL_SOURCE=graph missing: {', '.join(missing)}")
            return 1

    print("[data] env preflight OK")
    return 0


def check_council() -> int:
    secure_mode = os.getenv("SECURE_MODE", "false").lower() == "true"
    required = ["GATEWAY_URL", "COUNCIL_MEMBER_ALIASES", "COUNCIL_SYNTHESIS_ALIAS"]
    if secure_mode:
        required.append("SERVICE_SHARED_KEY")
    missing = get_missing(required)
    if missing:
        print(f"[llm-council] missing: {', '.join(missing)}")
        return 1
    print("[llm-council] env preflight OK")
    return 0


CHECKERS = {
    "gateway": check_gateway,
    "agents": check_agents,
    "data": check_data,
    "llm-council": check_council,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Environment preflight validation for AI Ready services.")
    parser.add_argument(
        "--service",
        choices=["all", "gateway", "agents", "data", "llm-council"],
        default="all",
        help="Service to validate.",
    )
    args = parser.parse_args()

    if args.service == "all":
        rc = 0
        for name in ("gateway", "agents", "data", "llm-council"):
            rc |= CHECKERS[name]()
        sys.exit(rc)

    sys.exit(CHECKERS[args.service]())


if __name__ == "__main__":
    main()
