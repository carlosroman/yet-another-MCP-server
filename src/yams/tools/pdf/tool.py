from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal
from urllib.parse import unquote, urlparse


def create_read_pdf_tool():
    async def read_pdf(
        file_path: str,
        format: Literal["markdown", "text", "html"] = "markdown",
    ) -> dict:
        if not file_path or not file_path.strip():
            raise ValueError("File path must not be empty")

        resolved_path = _resolve_path(file_path)
        _validate_pdf_file(resolved_path)

        pdf_bytes = resolved_path.read_bytes()

        title, content = _convert_pdf(pdf_bytes, resolved_path.name)

        return {
            "file_path": str(resolved_path),
            "content": _format_content(content, format),
            "page_count": _count_pages(pdf_bytes),
            "title": title,
            "converted_at": datetime.now(UTC).isoformat(),
        }

    return read_pdf


def _resolve_path(file_path: str) -> Path:
    parsed = urlparse(file_path)
    if parsed.scheme == "file":
        path_str = unquote(parsed.path)
        return Path(path_str)
    return Path(file_path).expanduser().resolve()


def _validate_pdf_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    if not path.is_file():
        raise ValueError(f"Not a file: {path}")
    if path.suffix.lower() != ".pdf":
        raise ValueError(f"Not a PDF file: {path}")


def _convert_pdf(pdf_bytes: bytes, filename: str) -> tuple[str | None, str]:
    import io

    from markitdown import MarkItDown

    md = MarkItDown()
    result = md.convert_stream(io.BytesIO(pdf_bytes), file_extension=".pdf")

    if not result:
        raise RuntimeError(f"Failed to convert PDF: {filename}")

    return result.title, result.text_content


def _count_pages(pdf_bytes: bytes) -> int:
    import io

    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        return len(reader.pages)
    except ImportError:
        return -1


def _format_content(content: str, fmt: str) -> str:
    import re

    if fmt == "text":
        text = re.sub(r"#+ ", "", content)
        text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
        text = re.sub(r"[*_~`]", "", text)
        text = re.sub(r"!\[([^\]]*)\]\([^\)]+\)", r"[IMAGE: \1]", text)
        return text.strip()
    elif fmt == "html":
        return f"<pre>{content}</pre>"
    return content
