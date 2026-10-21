from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class ProviderRegistry(Generic[T]):
    """A small registry keeps UI labels independent from provider implementations."""

    def __init__(self) -> None:
        self._providers: dict[str, T] = {}

    def register(self, provider_id: str, provider: T) -> None:
        if provider_id in self._providers:
            raise ValueError(f"Provider already registered: {provider_id}")
        self._providers[provider_id] = provider

    def get(self, provider_id: str) -> T:
        try:
            return self._providers[provider_id]
        except KeyError as exc:
            raise KeyError(f"Unknown provider: {provider_id}") from exc

    def ids(self) -> tuple[str, ...]:
        return tuple(self._providers)
