from __future__ import annotations

import json
from dataclasses import asdict, fields
from pathlib import Path

from app.models.contracts import AppSettings


class SettingsStore:
    """JSON settings deliberately exclude secrets, which belong in OS keychain."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".voicebridge" / "settings.json"

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Unable to read settings: {exc}") from exc
        accepted = {field.name for field in fields(AppSettings)}
        return AppSettings(**{key: value for key, value in payload.items() if key in accepted})

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(asdict(settings), ensure_ascii=False, indent=2), encoding="utf-8")
        temp_path.replace(self.path)
