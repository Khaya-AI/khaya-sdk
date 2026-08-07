"""Tests for the MCP server.

The tool schemas are the contract a calling model sees, so a signature change
that silently alters them is a breaking change to every client. These pin it.
"""

import json

import httpx
import pytest

pytest.importorskip("mcp", reason="requires the [mcp] extra")

from khaya import KhayaClient  # noqa: E402
from khaya.config import Settings  # noqa: E402
from khaya.mcp.server import MissingAPIKeyError, build_server  # noqa: E402

BASE_URL = "https://translation-api.ghananlp.org"
TRANSLATE_URL = f"{BASE_URL}/v1/translate"
ASR_URL = f"{BASE_URL}/asr/v3/transcribe"
TTS_URL = f"{BASE_URL}/tts/v1/tts"
WAV_BYTES = b"RIFF$\x00\x00\x00WAVEfmt " + b"\x00" * 24
AUDIO_HEADERS = {"content-type": "audio/wav"}


@pytest.fixture
def server():
    config = Settings(api_key="test-api-key", retry_attempts=1)
    return build_server(KhayaClient(api_key="test-api-key", config=config))


# ---------------------------------------------------------------------------
# Tool contract
# ---------------------------------------------------------------------------


async def test_expected_tools_are_registered(server):
    names = {t.name for t in await server.list_tools()}
    assert names == {"translate", "transcribe", "synthesize", "list_languages"}


async def test_every_tool_has_a_description(server):
    """The description is the only documentation the model gets."""
    for tool in await server.list_tools():
        assert tool.description and len(tool.description) > 40, tool.name


@pytest.mark.parametrize(
    ("tool_name", "required"),
    [
        ("translate", ["text"]),
        ("transcribe", ["audio_path"]),
        ("synthesize", ["text", "output_path"]),
        ("list_languages", ["service"]),
    ],
)
async def test_required_arguments(server, tool_name, required):
    tool = next(t for t in await server.list_tools() if t.name == tool_name)
    assert tool.input_schema.get("required", []) == required


async def test_enum_arguments_are_constrained(server):
    """A model should not be able to invent a granularity or a service."""
    tools = {t.name: t for t in await server.list_tools()}

    timestamps = tools["transcribe"].input_schema["properties"]["timestamps"]
    assert {"word", "segment"} == set(timestamps["anyOf"][0]["enum"])

    service = tools["list_languages"].input_schema["properties"]["service"]
    assert set(service["enum"]) == {"translation", "asr", "tts"}


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------


async def test_translate_returns_text(server, respx_mock):
    respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="Mema wo akwaaba"))
    result = await server.call_tool("translate", {"text": "Good morning"})
    assert result.structured_content["result"] == "Mema wo akwaaba"


async def test_translate_defaults_to_iso_codes(server, respx_mock):
    route = respx_mock.post(TRANSLATE_URL).mock(return_value=httpx.Response(200, json="x"))
    await server.call_tool("translate", {"text": "Good morning"})
    assert json.loads(route.calls.last.request.content)["lang"] == "eng-twi"


async def test_transcribe_surfaces_warnings_and_timings(server, respx_mock, tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(WAV_BYTES)
    respx_mock.post(ASR_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "text": "Me ho yɛ.",
                "warnings": ["'tw' is a legacy code."],
                "timings": {
                    "unit": "seconds",
                    "granularity": "word",
                    "segments": [],
                    "words": [{"word": "Me", "start": 0.0, "end": 0.12}],
                },
            },
        )
    )
    result = await server.call_tool(
        "transcribe", {"audio_path": str(audio), "language": "tw", "timestamps": "word"}
    )
    content = result.structured_content
    assert content["text"] == "Me ho yɛ."
    assert content["warnings"] == ["'tw' is a legacy code."]
    assert content["timings"]["words"][0]["word"] == "Me"


async def test_transcribe_omits_timings_when_not_requested(server, respx_mock, tmp_path):
    audio = tmp_path / "a.wav"
    audio.write_bytes(WAV_BYTES)
    respx_mock.post(ASR_URL).mock(return_value=httpx.Response(200, json={"text": "hi"}))
    result = await server.call_tool("transcribe", {"audio_path": str(audio)})
    assert result.structured_content["timings"] is None


async def test_synthesize_writes_a_file_and_returns_its_path(server, respx_mock, tmp_path):
    respx_mock.post(TTS_URL).mock(
        return_value=httpx.Response(200, content=WAV_BYTES, headers=AUDIO_HEADERS)
    )
    out = tmp_path / "out.wav"
    result = await server.call_tool(
        "synthesize", {"text": "Me ho yɛ", "output_path": str(out), "language": "twi"}
    )
    assert result.structured_content["result"] == str(out)
    assert out.read_bytes() == WAV_BYTES


async def test_list_languages_uses_bundled_constants_without_network(server):
    from khaya.constants import SUPPORTED_TTS_LANGUAGES

    result = await server.call_tool("list_languages", {"service": "tts"})
    assert set(result.structured_content["codes"]) == set(SUPPORTED_TTS_LANGUAGES)


async def test_list_languages_refresh_reads_the_live_catalogue(server, respx_mock):
    respx_mock.get(f"{BASE_URL}/asr/v3/languages").mock(
        return_value=httpx.Response(200, json={"languages": [{"code": "twi", "name": "Twi"}]})
    )
    result = await server.call_tool("list_languages", {"service": "asr", "refresh": True})
    assert result.structured_content["codes"] == ["twi"]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


async def test_sdk_errors_reach_the_model_as_actionable_text(server, tmp_path):
    """MCP converts a raised exception into is_error plus the message.

    The message must name the valid options so the model can retry correctly.
    """
    with pytest.raises(Exception, match="male_high"):
        await server.call_tool(
            "synthesize",
            {"text": "hi", "output_path": str(tmp_path / "x.wav"), "speaker": "robot"},
        )


def test_missing_api_key_fails_at_construction(monkeypatch):
    monkeypatch.delenv("KHAYA_API_KEY", raising=False)
    with pytest.raises(MissingAPIKeyError, match="KHAYA_API_KEY"):
        build_server()


def test_lazy_export_keeps_the_package_importable_without_mcp():
    """khaya.mcp must import even when the extra is absent.

    The console script goes through khaya.mcp.__main__, which triggers this
    package's __init__. An eager import of the server here would raise before
    main() could print the install hint.
    """
    import ast
    from pathlib import Path

    source = Path("src/khaya/mcp/__init__.py").read_text()
    tree = ast.parse(source)
    top_level_imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    imported = {
        alias.name
        for node in top_level_imports
        for alias in node.names
        if isinstance(node, ast.Import)
    } | {node.module for node in top_level_imports if isinstance(node, ast.ImportFrom)}
    assert not any(m and m.startswith(("mcp", "khaya.mcp.server")) for m in imported)


def test_build_server_is_still_reachable_from_the_package():
    from khaya.mcp import build_server as lazy

    assert lazy is build_server
