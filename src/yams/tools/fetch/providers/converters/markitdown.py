from __future__ import annotations

from io import BytesIO

from markitdown import MarkItDown

from yams.tools.fetch.providers.converters.base import ContentConverter


class MarkItDownConverter(ContentConverter):
    def convert(self, content: bytes | str, content_type: str) -> str:
        if isinstance(content, str):
            content = content.encode("utf-8")
        md = MarkItDown()
        result = md.convert_stream(BytesIO(content))
        return result.text_content if result else ""
