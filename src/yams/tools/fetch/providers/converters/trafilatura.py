from __future__ import annotations

import json
import xml.dom.minidom

from yams.tools.fetch.providers.converters.base import ContentConverter


class TrafilaturaConverter(ContentConverter):
    def convert(self, content: bytes | str, content_type: str) -> str:
        if not content:
            return ""

        ct = content_type.lower()

        if "html" in ct or "xml" in ct:
            return _extract_html(content)
        elif "json" in ct:
            return _format_json(content)
        elif "xml" in ct:
            return _format_xml(content)

        return (
            _extract_html(content)
            if isinstance(content, str)
            else content.decode("utf-8", errors="replace")
        )


def _extract_html(content: bytes | str) -> str:
    import trafilatura

    text = trafilatura.extract(content, output_format="markdown")
    return text or ""


def _format_json(content: bytes | str) -> str:
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    try:
        parsed = json.loads(content)
        return "```json\n" + json.dumps(parsed, indent=2) + "\n```"
    except json.JSONDecodeError:
        return content


def _format_xml(content: bytes | str) -> str:
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    try:
        dom = xml.dom.minidom.parseString(content)
        pretty = dom.toprettyxml(indent="  ")
        lines = [line for line in pretty.splitlines() if line.strip()]
        return "```xml\n" + "\n".join(lines) + "\n```"
    except xml.parsers.expat.ExpatError:
        return content
