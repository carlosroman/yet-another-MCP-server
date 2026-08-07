from __future__ import annotations

from abc import ABC, abstractmethod


class ContentConverter(ABC):
    @abstractmethod
    def convert(self, content: bytes | str, content_type: str) -> str: ...
