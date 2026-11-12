"""Read deployment settings; do not log secrets."""

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database: Path
    model: str
    api_key: str | None

    @classmethod
    def from_env(cls):
        return cls(
            Path(os.getenv("COPILOT_DB", "data/energy.db")),
            os.getenv("OPENAI_MODEL", "gpt-4.1-mini-2025-04-14"),
            os.getenv("OPENAI_API_KEY") or None,
        )
