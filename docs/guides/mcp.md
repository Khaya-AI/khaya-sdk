# MCP Server

Khaya ships an [MCP](https://modelcontextprotocol.io) server, which puts
translation, speech recognition and text-to-speech inside AI clients such as
Claude Desktop, Claude Code and Cursor as callable tools.

You ask the assistant to translate something into Twi; it calls the Khaya API.
No code required.

## Install

```bash
pip install khaya[mcp]
```

The extra is separate because `mcp` pulls in a web stack the SDK itself does
not need. A plain `pip install khaya` stays lean.

## Configure your client

```json
{
  "mcpServers": {
    "khaya": {
      "command": "khaya-mcp",
      "env": { "KHAYA_API_KEY": "your_api_key_here" }
    }
  }
}
```

Same shape for Claude Desktop, Claude Code and Cursor — only the location of
the config file differs. Restart the client afterwards.

If `KHAYA_API_KEY` is missing the server exits immediately with a message,
rather than failing on the first tool call.

## Tools

| Tool | Purpose |
|------|---------|
| `translate` | Translate text between English and an African language |
| `transcribe` | Transcribe a `.wav` file, optionally with word or segment timings |
| `synthesize` | Generate speech and write it to a `.wav` file |
| `list_languages` | Look up the codes a service accepts |

`list_languages` exists so the assistant looks a code up instead of guessing
between `tw`, `twi` and `eng-twi`. It answers from the codes bundled with the
release; pass `refresh` to query the API's live catalogue.

`synthesize` takes an output path and returns it — audio is written to disk
rather than returned inline.

## Example prompts

> Translate "Good morning, how are you?" into Twi.

> Transcribe `recording.wav` — it's in Ewe — and give me word-level timings.

> Say "Akwaaba" in Twi with the female voice and save it to `welcome.wav`.

> Which languages can Khaya transcribe?

## Errors

Tool failures come back as errors carrying the SDK's message, so the assistant
can correct itself and retry:

```
Error executing tool synthesize: Unknown speaker 'robot'.
Supported speakers: female, male_high, male_low
```

## Running it directly

The server speaks stdio, so it is not useful to run by hand — it waits for a
client on stdin. To check it starts:

```bash
KHAYA_API_KEY=... khaya-mcp
```

Silence means it is running and waiting. `Ctrl-C` to stop.
