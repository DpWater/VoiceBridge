import pytest

from app.providers.registry import ProviderRegistry


def test_provider_registry_rejects_duplicates_and_unknown_ids() -> None:
    registry = ProviderRegistry[str]()
    registry.register("local", "provider")
    assert registry.get("local") == "provider"
    with pytest.raises(ValueError):
        registry.register("local", "other")
    with pytest.raises(KeyError):
        registry.get("missing")
