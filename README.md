# 🍫 Nougat-MCP

[![PyPI version](https://img.shields.io/pypi/v/nougat-mcp.svg)](https://pypi.org/project/nougat-mcp/)
[![Python versions](https://img.shields.io/pypi/pyversions/nougat-mcp.svg)](https://pypi.org/project/nougat-mcp/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![MCP Protocol](https://img.shields.io/badge/MCP-Standard-blue.svg)](https://modelcontextprotocol.io)

A **Model Context Protocol (MCP)** server that brings Meta's [Nougat](https://facebookresearch.github.io/nougat/) (Neural Optical Understanding for Academic Documents) to your AI agent ecosystem.

This server enables LLMs (like Claude, Codex, or Gemini) to **read, parse, and understand** complex scientific papers with high fidelity, preserving mathematical formulas, tables, and document structures.

---

## 🚀 Key Features

- **Scientific Precision**: Specifically trained by Meta to handle academic layouts that traditional OCR (like Tesseract) fails on.
- **LaTeX Math Support**: Converts complex equations into standard LaTeX/Markdown math delimiters.
- **Table Preservation**: Reconstructs data tables into readable Markdown format.
- **Process Isolation**: Securely executes Nougat in an isolated subprocess to manage memory-heavy Torch dependencies.
- **Async Compatible**: Built on `FastMCP` for high-performance interaction with modern AI clients.

## 🛠 Prerequisites

- **Python**: 3.10-3.13
- **Torch**: Required for model inference (installed automatically through dependencies).

## 📦 Installation

Install from PyPI:

```bash
uv pip install nougat-mcp
```

`nougat-mcp` installs `nougat-ocr` and compatible dependency versions automatically.

## ✅ Compatibility

To keep the server working out-of-the-box, this package constrains known-sensitive Nougat dependencies:

- `transformers` (<4.38)
- `albumentations` (<1.4)
- `pypdfium2` (<5)

## ⚙️ Configuration

### Antigravity / Gemini Desktop

Add to your `~/.gemini/settings.json`:

```json
"mcpServers": {
  "nougat": {
    "type": "stdio",
    "command": "uv",
    "args": [
      "--directory",
      "/path/to/nougat-mcp",
      "run",
      "nougat-mcp"
    ]
  }
}
```

You can pass a custom server settings file path using env:

```json
"mcpServers": {
  "nougat": {
    "type": "stdio",
    "command": "nougat-mcp",
    "env": {
      "NOUGAT_MCP_SETTINGS": "/absolute/path/to/settings.json"
    }
  }
}
```

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "nougat": {
      "command": "nougat-mcp"
    }
  }
}
```

## ⚙️ Server Settings

The server reads settings from:

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

## 🛠 Tools Provided

### `get_output_settings`

Returns resolved output settings so agents can read formatting preferences.

### `parse_research_paper`

**Arguments:**

- `file_path` (string): Absolute path to the local PDF file.
- `output_format` (string, optional): `"default"` (default, reads settings), `"mmd"` for raw Nougat output, or `"md"` for Markdown-oriented math delimiters.

**Output:**
Clean document text in the selected format:

- `"mmd"`: Nougat/Mathpix-style Markdown output.
- `"md"`: Converted Markdown with math delimiters rewritten to `$...$` and `$$...$$`, `\tag{...}` rewritten to visible equation labels, and KaTeX-incompatible sized delimiters normalized (for example `\bigl{\|}` -> `\bigl\|`).

## 🎯 Showcase (Page 5 Example)

To make the output format differences concrete, this repository includes a real extraction from page 5 of `src/2405.08770v1.pdf`:

- **Input page PDF**: `showcase/2405.08770v1_page5.pdf`
- **Raw Nougat output (`mmd`)**: `showcase/2405.08770v1_page5.mmd`
- **Converted Markdown output (`md`)**: `showcase/2405.08770v1_page5.md`

Quick conversion comparison:

```text
# mmd
\[DV=V_{x}. \tag{3.2}\]

# md
$$
DV=V_{x}. \qquad\text{(3.2)}
$$
```

## 🔗 Credits & Pointers

- **Original Project**: [Meta's Nougat-OCR](https://github.com/facebookresearch/nougat)
- **Paper**: [Nougat: Neural Optical Understanding for Academic Documents](https://arxiv.org/abs/2308.13418)
- **Model Weights**: Provided by Meta AI. *Note: Weights are automatically downloaded (~1.4GB) on first execution.*

## 📄 License

Distributed under the **GNU General Public License v3.0**. See `LICENSE` for more information.
