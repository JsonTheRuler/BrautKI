from __future__ import annotations

import os
from dataclasses import dataclass


def _member_aliases() -> list[str]:
    raw = os.getenv("COUNCIL_MEMBER_ALIASES", "reasoning-primary,fast-cheap,internal-secure")
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    gateway_url: str = os.getenv("GATEWAY_URL", "http://localhost:4000")
    synthesis_alias: str = os.getenv("COUNCIL_SYNTHESIS_ALIAS", "reasoning-primary")
    member_aliases: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "member_aliases", _member_aliases())


settings = Settings()
