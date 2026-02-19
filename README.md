# Nougat-MCP

[![PyPI version](https://img.shields.io/pypi/v/nougat_mcp.svg)](https://pypi.org/project/nougat-mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/nougat_mcp.svg)](https://pypi.org/project/nougat-mcp/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![MCP Protocol](https://img.shields.io/badge/MCP-Standard-blue.svg)](https://modelcontextprotocol.io)

`nougat-mcp` is a Model Context Protocol (MCP) server for high-fidelity OCR of scientific PDFs using Meta's Nougat.

It is designed for agent workflows where you need equations, tables, and structure preserved better than traditional OCR.

## Why This Server

- Scientific OCR quality tailored for papers, formulas, and dense layouts.
- MCP-native interface for Codex, Claude, Cursor, Antigravity, and other clients.
- Output-format control:
  - `mmd`: raw Nougat/Mathpix-style output.
  - `md`: renderer-friendly conversion (math delimiter and KaTeX compatibility fixes).
- Settings file support so agents can read a shared default format policy.

## Installation

Install from PyPI:

```bash
uv pip install nougat-mcp
```

This package installs `nougat-ocr` and pins known-sensitive dependencies for stability.

## Tools

### `parse_research_paper`

Arguments:

- `file_path` (string): Absolute path to a local PDF.
- `output_format` (string, optional):
  - `default` (default): uses server settings.
  - `mmd`: raw Nougat output.
  - `md`: converted markdown-friendly output.

Returns:

- OCR result as a single text string in the requested format.

### `get_output_settings`

Returns resolved server output settings, including where settings were loaded from.

## Output Conversion (`mmd` -> `md`)

When `output_format="md"`, the server applies compatibility conversions:

- `\[ ... \]` -> `$$ ... $$`
- `\( ... \)` -> `$ ... $`
- `\tag{...}` -> visible equation label `\qquad\text{(...)}`
- KaTeX delimiter normalization, for example:
  - `\bigl{\|} ... \bigr{\|}` -> `\bigl\| ... \bigr\|`

This avoids common renderer parse errors in markdown environments that are not fully MathJax-compatible.

## Server Settings

Settings are read in this order:

1. `NOUGAT_MCP_SETTINGS` (if set)
2. `./settings.json` (current working directory)

Example `settings.json`:

```json
{
  "nougat_mcp": {
    "default_output_format": "md",
    "md_rewrite_tags": true,
    "md_fix_sized_delimiters": true
  }
}
```

## Agent Configuration

### Codex CLI

Add to `~/.codex/config.toml`:

```toml
[mcp_servers.nougat]
command = "uvx"
args = ["nougat-mcp"]
enabled = true

[mcp_servers.nougat.env]
NOUGAT_MCP_SETTINGS = "/absolute/path/to/settings.json"
```

### Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nougat": {
      "command": "uvx",
      "args": ["nougat-mcp"],
      "env": {
        "NOUGAT_MCP_SETTINGS": "/absolute/path/to/settings.json"
      }
    }
  }
}
```

### Antigravity / Gemini Desktop

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "nougat": {
      "type": "stdio",
      "command": "uvx",
      "args": ["nougat-mcp"],
      "env": {
        "NOUGAT_MCP_SETTINGS": "/absolute/path/to/settings.json"
      }
    }
  }
}
```

### Cursor

In Cursor MCP settings, add:

```json
{
  "mcpServers": {
    "nougat": {
      "command": "uvx",
      "args": ["nougat-mcp"],
      "env": {
        "NOUGAT_MCP_SETTINGS": "/absolute/path/to/settings.json"
      }
    }
  }
}
```

Note: Cursor MCP config location can vary by version/platform; use the MCP settings UI or your current JSON settings file.

## Showcase (Real Page Example)

A real extraction from page 5 of `src/2405.08770v1.pdf` is included:

- Input PDF page: [showcase/2405.08770v1_page5.pdf](https://github.com/svretina/nougat-mcp/blob/master/showcase/2405.08770v1_page5.pdf)
- Raw `mmd` output: [showcase/2405.08770v1_page5.mmd](https://github.com/svretina/nougat-mcp/blob/master/showcase/2405.08770v1_page5.mmd)
- Converted `md` output: [showcase/2405.08770v1_page5.md](https://github.com/svretina/nougat-mcp/blob/master/showcase/2405.08770v1_page5.md)

Quick comparison:

```text
# mmd
\[DV=V_{x}. \tag{3.2}\]

# md
$$
DV=V_{x}. \qquad\text{(3.2)}
$$
```

## Performance Notes

- First run may download model weights (~1.4 GB).
- CPU inference is significantly slower than GPU inference.
- Use page subsets whenever possible to reduce runtime.

## Compatibility Pins

To keep Nougat stable across environments, the package pins sensitive dependency ranges:

- `transformers>=4.35,<4.38`
- `albumentations>=1.3,<1.4`
- `pypdfium2<5.0`
- `huggingface-hub<1.0`
- `fsspec<=2025.10.0`

## Credits

- Nougat OCR: <https://github.com/facebookresearch/nougat>
- Paper: <https://arxiv.org/abs/2308.13418>

## License

GNU General Public License v3.0 (`LICENSE`).
