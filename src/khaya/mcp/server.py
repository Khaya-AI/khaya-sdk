"""Tool definitions for the Khaya MCP server.

Tool docstrings are the only documentation the calling model sees, so they
carry the guidance a human would get from the docs — especially which language
codes are valid, since guessing between ``tw``, ``twi`` and ``eng-twi`` is the
most likely way a model gets this wrong.
"""

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Any, Literal

from mcp.server import MCPServer

from khaya import KhayaClient, __version__
from khaya.constants import (
    SUPPORTED_ASR_LANGUAGES,
    SUPPORTED_LANGUAGE_PAIRS,
    SUPPORTED_TTS_LANGUAGES,
)
from khaya.exceptions import APIError, AuthenticationError

Service = Literal["translation", "asr", "tts"]
Granularity = Literal["word", "segment"]

INSTRUCTIONS = """Translation, speech recognition and text-to-speech for 30+ African
languages via the Khaya API.

Language codes are ISO 639-3 (three letters): twi, ewe, gaa, yor, hau, swa.
Older two-letter codes (tw, ee, yo) still work but are deprecated. Call
list_languages when unsure — do not guess."""

_CATALOGUES: dict[str, frozenset[str]] = {
    "translation": SUPPORTED_LANGUAGE_PAIRS,
    "asr": SUPPORTED_ASR_LANGUAGES,
    "tts": SUPPORTED_TTS_LANGUAGES,
}


class MissingAPIKeyError(RuntimeError):
    """Raised at startup rather than on the first tool call."""


def _client() -> KhayaClient:
    api_key = os.environ.get("KHAYA_API_KEY")
    if not api_key:
        raise MissingAPIKeyError(
            "KHAYA_API_KEY is not set. Add it to the env block of your MCP "
            "client configuration for this server."
        )
    return KhayaClient(api_key)


def build_server(client: KhayaClient | None = None) -> MCPServer:
    """Construct the server with its tools registered.

    Args:
        client: Injected for tests. Built from ``KHAYA_API_KEY`` otherwise.
    """
    khaya = client if client is not None else _client()

    @asynccontextmanager
    async def lifespan(_: MCPServer) -> AsyncIterator[KhayaClient]:
        try:
            yield khaya
        finally:
            await khaya.http_client.aclose()

    mcp: MCPServer = MCPServer(
        name="khaya",
        version=__version__,
        instructions=INSTRUCTIONS,
        lifespan=lifespan,
    )

    @mcp.tool()
    async def translate(text: str, language_pair: str = "eng-twi") -> str:
        """Translate text between English and an African language.

        language_pair is "<source>-<target>" using ISO 639-3 codes, e.g.
        "eng-twi" (English to Twi) or "twi-eng". Every pair goes through
        English. Call list_languages("translation") for the full set.
        """
        result = await khaya.atranslate(text, language_pair)
        return result.text

    @mcp.tool()
    async def transcribe(
        audio_path: str,
        language: str = "twi",
        timestamps: Granularity | None = None,
    ) -> dict[str, Any]:
        """Transcribe a .wav audio file to text.

        audio_path is a path on this machine. language is the spoken language,
        ISO 639-3, e.g. "twi". Set timestamps to "word" or "segment" to also
        get start/end offsets in seconds.

        Returns the transcript, any advisories from the API, and timings when
        requested.
        """
        result = await khaya.atranscribe(audio_path, language, timestamps)
        return {
            "text": result.text,
            "warnings": result.warnings,
            "timings": asdict(result.timings) if result.timings else None,
        }

    @mcp.tool()
    async def synthesize(
        text: str,
        output_path: str,
        language: str = "twi",
        speaker: str | None = None,
    ) -> str:
        """Generate speech from text and write it to a .wav file.

        language is ISO 639-3, e.g. "twi". speaker is one of "male_low",
        "male_high" or "female"; omit it for the default voice. Returns the
        path written — the audio is not returned inline.
        """
        result = await khaya.asynthesize(text, language, speaker)
        result.save(output_path)
        return output_path

    @mcp.tool()
    async def list_languages(service: Service, refresh: bool = False) -> dict[str, Any]:
        """List the language codes a service accepts.

        Use this instead of guessing a code. service is "translation" (returns
        source-target pairs), "asr", or "tts". Set refresh to fetch the live
        catalogue from the API rather than the codes bundled with this
        release.
        """
        if refresh:
            return {"service": service, "codes": sorted(await _live_catalogue(khaya, service))}
        return {"service": service, "codes": sorted(_CATALOGUES[service])}

    return mcp


async def _live_catalogue(client: KhayaClient, service: Service) -> set[str]:
    """Fetch a catalogue from the API. Only ASR and TTS publish one."""
    base = client.config.base_url
    if service == "asr":
        response = await client.http_client.arequest("GET", f"{base}/asr/v3/languages")
        return {entry["code"] for entry in response.json()["languages"]}
    if service == "tts":
        response = await client.http_client.arequest("GET", f"{base}/tts/v2/languages")
        return set(response.json()["languages"].values())
    # Translation publishes single codes, not the pairs the API actually takes.
    return set(_CATALOGUES["translation"])


__all__ = ["APIError", "AuthenticationError", "MissingAPIKeyError", "build_server"]
