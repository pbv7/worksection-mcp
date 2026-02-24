"""Tests for file-related MCP tool behavior."""

from __future__ import annotations

import base64
import types
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock

import pytest

from tests.helpers import FakeMCP
from worksection_mcp.tools.files import register_file_tools


def _make_file_client(task_payload: Any = None, comments_payload: Any = None) -> Any:
    return SimpleNamespace(
        download_file=AsyncMock(return_value=b""),
        get_task=AsyncMock(return_value=task_payload or {"status": "ok", "data": {"files": []}}),
        get_comments=AsyncMock(return_value=comments_payload or {"status": "ok", "data": []}),
    )


def _get_closure_var(func, name: str):
    """Get a named free variable from a closure."""
    assert func.__closure__ is not None
    assert func.__code__.co_freevars
    mapping = dict(zip(func.__code__.co_freevars, func.__closure__, strict=False))
    return mapping[name].cell_contents


@pytest.mark.asyncio
async def test_download_and_attachment_tools(tmp_path):
    """File tools should surface metadata and aggregate task/comment attachments."""
    client = _make_file_client(
        task_payload={
            "status": "ok",
            "data": {"files": [{"id": "f1", "name": "spec.pdf"}, {"id": "f2", "name": "shot.png"}]},
        },
        comments_payload={
            "status": "ok",
            "data": [
                {
                    "id": "c1",
                    "text": "See image",
                    "user_from": {"name": "Ana"},
                    "files": [{"id": "f3", "name": "note.jpg"}],
                }
            ],
        },
    )
    client.download_file = AsyncMock(return_value=b"content")

    cache_path = tmp_path / "download.bin"
    cache_path.write_bytes(b"content")
    file_cache: Any = SimpleNamespace(save=AsyncMock(return_value=cache_path))

    mcp = FakeMCP()
    register_file_tools(mcp, client, file_cache)

    task_files = await mcp.tools["get_task_files"]("t1")
    assert task_files["status"] == "ok"

    downloaded = await mcp.tools["download_file"]("f2")
    assert downloaded["cached"] is True
    assert downloaded["size_bytes"] == 7
    assert downloaded["resource_uri"] == "worksection://file/f2"

    attachments = await mcp.tools["get_all_task_attachments"]("t1")
    assert attachments["total_files"] == 3

    images = await mcp.tools["list_image_attachments"](task_id="t1")
    assert images["image_count"] == 2
    assert {image["source"] for image in images["images"]} == {"task", "comment"}


@pytest.mark.asyncio
async def test_get_file_as_base64_builds_data_url_for_images():
    """Image content should be detected and returned with display-ready data URL."""
    png_bytes = b"\x89PNG\r\n\x1a\nimagedata"
    client = _make_file_client()
    client.download_file = AsyncMock(return_value=png_bytes)

    mcp = FakeMCP()
    register_file_tools(mcp, client, file_cache=None)

    result = await mcp.tools["get_file_as_base64"]("img-1")
    assert result["is_image"] is True
    assert result["mime_type"] == "image/png"
    assert result["base64_content"] == base64.b64encode(png_bytes).decode("utf-8")
    assert result["data_url"].startswith("data:image/png;base64,")


@pytest.mark.asyncio
async def test_get_file_content_text_and_binary_paths():
    """Text and image/binary content should map to correct content categories."""
    client = _make_file_client()
    mcp = FakeMCP()
    register_file_tools(mcp, client, file_cache=None)

    client.download_file = AsyncMock(return_value=b"hello world")
    text_result = await mcp.tools["get_file_content"]("txt-1")
    assert text_result["content_type"] == "text"
    assert text_result["is_readable"] is True
    assert "hello world" in text_result["text_content"]

    client.download_file = AsyncMock(return_value=b"\x89PNG\r\n\x1a\nraw")
    image_result = await mcp.tools["get_file_content"]("img-1")
    assert image_result["content_type"] == "image"
    assert image_result["is_readable"] is False

    client.download_file = AsyncMock(return_value=b"\x00\x01\x02")
    binary_result = await mcp.tools["get_file_content"]("bin-1")
    assert binary_result["content_type"] == "binary"
    assert binary_result["is_readable"] is False


@pytest.mark.asyncio
async def test_detect_mime_type_webp_openxml_and_riff_fallback():
    """MIME detection should handle WebP, generic OpenXML, and RIFF non-WebP data."""
    client = _make_file_client()
    mcp = FakeMCP()
    register_file_tools(mcp, client, file_cache=None)

    client.download_file = AsyncMock(return_value=b"RIFFxxxxWEBPzzzz")
    webp = await mcp.tools["get_file_as_base64"]("webp")
    assert webp["mime_type"] == "image/webp"
    assert webp["is_image"] is True

    client.download_file = AsyncMock(return_value=b"PK\x03\x04generic-office-zip")
    generic_openxml = await mcp.tools["get_file_as_base64"]("office")
    assert generic_openxml["mime_type"] == "application/vnd.openxmlformats-officedocument"
    assert generic_openxml["is_image"] is False

    client.download_file = AsyncMock(return_value=b"RIFF\x00\x01\x02\x03")
    riff_non_webp = await mcp.tools["get_file_as_base64"]("riff")
    assert riff_non_webp["mime_type"] == "application/octet-stream"
    assert riff_non_webp["is_image"] is False

    client.download_file = AsyncMock(return_value=b"\xff\xfe\xfd")
    undecodable = await mcp.tools["get_file_as_base64"]("invalid-utf8")
    assert undecodable["mime_type"] == "application/octet-stream"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("payload", "expected_type"),
    [
        (b"PK\x03\x04word/document.xml", "document"),
        (b"PK\x03\x04xl/workbook.xml", "spreadsheet"),
        (b"PK\x03\x04ppt/slides/slide1.xml", "presentation"),
        (b"%PDF-1.7\n", "document"),
    ],
)
async def test_get_file_content_office_and_pdf_detection(payload, expected_type):
    """Office/PDF signatures should be detected and routed to extraction paths."""
    client = _make_file_client()
    client.download_file = AsyncMock(return_value=payload)
    mcp = FakeMCP()
    register_file_tools(mcp, client, file_cache=None)

    result = await mcp.tools["get_file_content"]("doc-1")
    assert result["content_type"] == expected_type
    assert result["is_readable"] is True


@pytest.mark.asyncio
async def test_download_file_without_cache_uses_default_mime():
    """download_file should still work when cache layer is not configured."""
    client = _make_file_client()
    client.download_file = AsyncMock(return_value=b"abc")

    mcp = FakeMCP()
    register_file_tools(mcp, client, file_cache=None)

    result = await mcp.tools["download_file"]("f9")
    assert result["cached"] is False
    assert result["mime_type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_get_file_content_extractor_success_paths(monkeypatch):
    """DOCX/XLSX/PPTX/PDF extractors should return readable content when libs succeed."""
    fake_docx = types.SimpleNamespace(
        Document=lambda _bio: types.SimpleNamespace(
            paragraphs=[types.SimpleNamespace(text="Doc text"), types.SimpleNamespace(text="")]
        )
    )

    class _Sheet:
        def iter_rows(self, values_only=True):
            _ = values_only
            return [("A1", "B1"), ("", None)]

    class _Workbook:
        def __init__(self):
            self.sheetnames = ["Main"]

        def __getitem__(self, _name):
            return _Sheet()

        def close(self):
            return None

    fake_openpyxl = types.SimpleNamespace(load_workbook=lambda *_args, **_kwargs: _Workbook())

    fake_pptx = types.SimpleNamespace(
        Presentation=lambda _bio: types.SimpleNamespace(
            slides=[
                types.SimpleNamespace(
                    shapes=[types.SimpleNamespace(text="Slide one"), types.SimpleNamespace(text="")]
                )
            ]
        )
    )

    fake_pypdf = types.SimpleNamespace(
        PdfReader=lambda _bio: types.SimpleNamespace(
            pages=[
                types.SimpleNamespace(extract_text=lambda: "Page one"),
                types.SimpleNamespace(extract_text=lambda: ""),
            ]
        )
    )

    monkeypatch.setitem(__import__("sys").modules, "docx", fake_docx)
    monkeypatch.setitem(__import__("sys").modules, "openpyxl", fake_openpyxl)
    monkeypatch.setitem(__import__("sys").modules, "pptx", fake_pptx)
    monkeypatch.setitem(__import__("sys").modules, "pypdf", fake_pypdf)

    client = _make_file_client()
    mcp = FakeMCP()
    register_file_tools(mcp, client, file_cache=None)

    for payload in (
        b"PK\x03\x04word/document.xml",
        b"PK\x03\x04xl/workbook.xml",
        b"PK\x03\x04ppt/slides/slide1.xml",
        b"%PDF-1.7\n",
    ):
        client.download_file = AsyncMock(return_value=payload)
        result = await mcp.tools["get_file_content"]("doc")
        assert result["is_readable"] is True
        assert result["content_type"] in {"document", "spreadsheet", "presentation"}


def test_extract_text_content_latin1_and_double_decode_failure():
    """Text extraction helper should fall back to latin1 and then to binary on repeated failure."""
    client = _make_file_client()
    mcp = FakeMCP()
    register_file_tools(mcp, client, file_cache=None)

    get_file_content = mcp.tools["get_file_content"]
    extract_text_content = _get_closure_var(get_file_content, "_extract_text_content")

    latin1_text, latin1_type = extract_text_content(b"\xff", "text/plain")
    assert latin1_type == "text"
    assert latin1_text

    class BadDecodable:
        def decode(self, encoding):
            if encoding == "utf-8":
                raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")
            raise RuntimeError("decode failed")

    fallback_text, fallback_type = extract_text_content(BadDecodable(), "text/plain")
    assert fallback_type == "binary"
    assert fallback_text == "[Unable to decode text content]"
