"""Version-aware registries for independently shipped Trident extensions."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Generic, TypeVar

from src.core.contracts import ExtensionDescriptor


class ExtensionRegistrationError(ValueError):
    pass


T = TypeVar("T")


class ExtensionRegistry(Generic[T]):
    def __init__(self, extensions: Iterable[T] = ()) -> None:
        self._items: dict[tuple[str, str], T] = {}
        for extension in extensions:
            self.register(extension)

    @staticmethod
    def _descriptor(extension: T) -> ExtensionDescriptor:
        descriptor = getattr(extension, "descriptor", None)
        if not isinstance(descriptor, ExtensionDescriptor):
            raise ExtensionRegistrationError(
                "extension must expose an ExtensionDescriptor named descriptor"
            )
        if not descriptor.extension_id.strip() or not descriptor.version.strip():
            raise ExtensionRegistrationError("extension id and version are required")
        return descriptor

    def register(self, extension: T, *, replace: bool = False) -> None:
        descriptor = self._descriptor(extension)
        key = (descriptor.extension_id, descriptor.version)
        if key in self._items and not replace:
            raise ExtensionRegistrationError(
                f"extension already registered: {descriptor.extension_id}@{descriptor.version}"
            )
        self._items[key] = extension

    def get(self, extension_id: str, version: str) -> T:
        try:
            return self._items[(extension_id, version)]
        except KeyError as exc:
            raise KeyError(f"unknown extension: {extension_id}@{version}") from exc

    def versions(self, extension_id: str) -> tuple[str, ...]:
        return tuple(
            sorted(version for item_id, version in self._items if item_id == extension_id)
        )

    def descriptors(self) -> tuple[ExtensionDescriptor, ...]:
        return tuple(
            self._descriptor(item)
            for _, item in sorted(self._items.items(), key=lambda pair: pair[0])
        )
