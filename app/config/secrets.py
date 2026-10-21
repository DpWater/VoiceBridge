from __future__ import annotations


class SecretStore:
    service_name = "VoiceBridge"

    def get_api_key(self, provider: str = "openai-compatible") -> str | None:
        try:
            import keyring
            return keyring.get_password(self.service_name, provider)
        except Exception:  # Keyring backend availability is platform-specific.
            return None

    def set_api_key(self, value: str, provider: str = "openai-compatible") -> None:
        if not value:
            raise ValueError("API key must not be empty")
        import keyring
        keyring.set_password(self.service_name, provider, value)
