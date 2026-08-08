from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yams.tools.pdf.tool import (
    _count_pages,
    _format_content,
    _resolve_path,
    _validate_pdf_file,
    create_read_pdf_tool,
)


class TestResolvePath:
    def test_absolute_path(self):
        path = _resolve_path("/home/user/document.pdf")
        assert path.name == "document.pdf"

    def test_file_url(self):
        path = _resolve_path("file:///home/user/document.pdf")
        assert path == Path("/home/user/document.pdf")

    def test_file_url_with_spaces(self):
        path = _resolve_path("file:///home/user/my%20document.pdf")
        assert path == Path("/home/user/my document.pdf")

    def test_relative_path(self):
        with patch("pathlib.Path.cwd") as mock_cwd:
            mock_cwd.return_value = Path("/home/user")
            path = _resolve_path("document.pdf")
            assert path.name == "document.pdf"


class TestValidatePdfFile:
    def test_valid_file(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf")
        _validate_pdf_file(pdf_file)

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="File not found"):
            _validate_pdf_file(Path("/nonexistent/file.pdf"))

    def test_not_a_file(self, tmp_path):
        with pytest.raises(ValueError, match="Not a file"):
            _validate_pdf_file(tmp_path)

    def test_not_pdf_extension(self, tmp_path):
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("hello")
        with pytest.raises(ValueError, match="Not a PDF file"):
            _validate_pdf_file(txt_file)

    def test_uppercase_pdf_extension(self, tmp_path):
        pdf_file = tmp_path / "test.PDF"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf")
        _validate_pdf_file(pdf_file)


class TestFormatContent:
    def test_markdown_format(self):
        content = "# Hello\n## World\n[link](http://example.com)\n**bold**"
        result = _format_content(content, "markdown")
        assert result == content

    def test_text_format(self):
        content = "# Hello\n## World\n[link](http://example.com)\n**bold**"
        result = _format_content(content, "text")
        assert "Hello" in result
        assert "#" not in result
        assert "**" not in result

    def test_html_format(self):
        content = "Hello World"
        result = _format_content(content, "html")
        assert result == "<pre>Hello World</pre>"


class TestCountPages:
    def test_pypdf_not_installed(self):
        pdf_bytes = b"%PDF-1.4 fake pdf"
        with patch.dict("sys.modules", {"pypdf": None}):
            count = _count_pages(pdf_bytes)
            assert count == -1


@pytest.mark.asyncio
class TestReadPdfTool:
    async def test_empty_path_raises(self):
        tool = create_read_pdf_tool()
        with pytest.raises(ValueError, match="File path must not be empty"):
            await tool("")

    async def test_whitespace_path_raises(self):
        tool = create_read_pdf_tool()
        with pytest.raises(ValueError, match="File path must not be empty"):
            await tool("   ")

    async def test_file_not_found(self):
        tool = create_read_pdf_tool()
        with pytest.raises(FileNotFoundError):
            await tool("/nonexistent/document.pdf")

    async def test_success(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        mock_result = MagicMock()
        mock_result.text_content = "# Test Document\n\nHello World"
        mock_result.source_url = None

        with patch("markitdown.MarkItDown") as mock_markitdown:
            mock_instance = MagicMock()
            mock_instance.convert_stream.return_value = mock_result
            mock_markitdown.return_value = mock_instance

            tool = create_read_pdf_tool()
            result = await tool(str(pdf_file))

        assert result["file_path"] == str(pdf_file)
        assert "Hello World" in result["content"]
        assert result["converted_at"] is not None

    async def test_file_url_success(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        mock_result = MagicMock()
        mock_result.text_content = "# Test Document\n\nHello World"
        mock_result.source_url = None

        with patch("markitdown.MarkItDown") as mock_markitdown:
            mock_instance = MagicMock()
            mock_instance.convert_stream.return_value = mock_result
            mock_markitdown.return_value = mock_instance

            tool = create_read_pdf_tool()
            file_url = f"file://{pdf_file}"
            result = await tool(file_url)

        assert "Hello World" in result["content"]

    async def test_text_format(self, tmp_path):
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        mock_result = MagicMock()
        mock_result.text_content = "# Test Document\n\n**Hello** World"
        mock_result.source_url = None

        with patch("markitdown.MarkItDown") as mock_markitdown:
            mock_instance = MagicMock()
            mock_instance.convert_stream.return_value = mock_result
            mock_markitdown.return_value = mock_instance

            tool = create_read_pdf_tool()
            result = await tool(str(pdf_file), format="text")

        assert "#" not in result["content"]
        assert "**" not in result["content"]
