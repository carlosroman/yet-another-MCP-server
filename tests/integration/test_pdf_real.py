from __future__ import annotations

from pathlib import Path

import pytest

from yams.tools.pdf.tool import create_read_pdf_tool

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestReadPdfToolIntegration:
    @pytest.mark.asyncio
    async def test_read_local_pdf_file(self):
        pdf_path = FIXTURES / "test_document.pdf"
        tool = create_read_pdf_tool()
        result = await tool(str(pdf_path))

        assert result["file_path"] == str(pdf_path)
        assert result["content"] is not None
        assert result["converted_at"] is not None

    @pytest.mark.asyncio
    async def test_read_pdf_with_file_url(self):
        pdf_path = FIXTURES / "test_document.pdf"
        file_url = f"file://{pdf_path}"
        tool = create_read_pdf_tool()
        result = await tool(file_url)

        assert "Hello World" in result["content"] or result["content"]

    @pytest.mark.asyncio
    async def test_read_pdf_text_format(self):
        pdf_path = FIXTURES / "test_document.pdf"
        tool = create_read_pdf_tool()
        result = await tool(str(pdf_path), format="text")

        assert isinstance(result["content"], str)

    @pytest.mark.asyncio
    async def test_read_pdf_html_format(self):
        pdf_path = FIXTURES / "test_document.pdf"
        tool = create_read_pdf_tool()
        result = await tool(str(pdf_path), format="html")

        assert result["content"].startswith("<pre>")
        assert result["content"].endswith("</pre>")

    @pytest.mark.asyncio
    async def test_read_nonexistent_pdf_raises(self):
        tool = create_read_pdf_tool()
        with pytest.raises(FileNotFoundError):
            await tool("/nonexistent/file.pdf")

    @pytest.mark.asyncio
    async def test_read_non_pdf_file_raises(self):
        html_path = FIXTURES / "test_page.html"
        tool = create_read_pdf_tool()
        with pytest.raises(ValueError, match="Not a PDF file"):
            await tool(str(html_path))
