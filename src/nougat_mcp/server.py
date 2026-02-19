# Copyright (C) 2026 Stamatis Vretinaris
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.

import os
import re
import json
import subprocess
import tempfile
import sys
import importlib.util
from pathlib import Path
from typing import Literal
from mcp.server.fastmcp import FastMCP

# Initialize the server with a descriptive name
mcp = FastMCP("Nougat-OCR")

VALID_OUTPUT_FORMATS = {"mmd", "md"}
SETTINGS_ENV_VAR = "NOUGAT_MCP_SETTINGS"
DEFAULT_SETTINGS_FILENAME = "settings.json"


def is_nougat_available() -> bool:
    """Check if the Nougat predict module is importable."""
    return importlib.util.find_spec("predict") is not None


def load_server_settings() -> tuple[dict, str | None]:
    """Load settings from NOUGAT_MCP_SETTINGS or ./settings.json."""
    candidates: list[Path] = []
    env_path = os.getenv(SETTINGS_ENV_VAR)
    if env_path:
        candidates.append(Path(env_path).expanduser())
    candidates.append(Path.cwd() / DEFAULT_SETTINGS_FILENAME)

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve()) if candidate.exists() else str(candidate.absolute())
        if key in seen:
            continue
        seen.add(key)

        if not candidate.exists():
            continue

        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            return {}, str(candidate)

        if not isinstance(data, dict):
            return {}, str(candidate)

        nested = data.get("nougat_mcp")
        if isinstance(nested, dict):
            return nested, str(candidate)
        return data, str(candidate)

    return {}, None


def resolve_default_output_format(settings: dict) -> str:
    """Get the configured default output format with safe fallback."""
    value = settings.get("default_output_format", "mmd")
    if isinstance(value, str) and value in VALID_OUTPUT_FORMATS:
        return value
    return "mmd"


def resolve_md_conversion_settings(settings: dict) -> tuple[bool, bool]:
    """Resolve markdown conversion flags from settings."""
    rewrite_tags = settings.get("md_rewrite_tags", True)
    fix_sized_delimiters = settings.get("md_fix_sized_delimiters", True)
    return (
        rewrite_tags if isinstance(rewrite_tags, bool) else True,
        fix_sized_delimiters if isinstance(fix_sized_delimiters, bool) else True,
    )


def mmd_to_markdown(
    mmd_text: str,
    rewrite_tags: bool = True,
    fix_sized_delimiters: bool = True,
) -> str:
    """Convert Nougat-style math delimiters to common Markdown math delimiters."""
    # Display math: \[ ... \] -> $$ ... $$
    markdown = re.sub(r"\\\[(.*?)\\\]", r"$$\n\1\n$$", mmd_text, flags=re.DOTALL)
    # Inline math: \( ... \) -> $ ... $
    markdown = re.sub(r"\\\((.*?)\\\)", r"$\1$", markdown, flags=re.DOTALL)

    if fix_sized_delimiters:
        # Nougat sometimes outputs delimiters as \bigl{\|}, which KaTeX rejects.
        # Normalize to KaTeX-friendly \bigl\|.
        sized_delim = re.compile(r"\\(bigl|Bigl|biggl|Biggl|bigr|Bigr|biggr|Biggr)\{([^{}]+)\}")

        def _normalize_sized_delim(match: re.Match[str]) -> str:
            delim = match.group(2).strip()
            if not delim:
                return match.group(0)
            return f"\\{match.group(1)}{delim}"

        markdown = sized_delim.sub(_normalize_sized_delim, markdown)

    if rewrite_tags:
        # Equation tags are not universally supported; render as visible text labels.
        markdown = re.sub(r"\\tag\{([^{}]+)\}", r"\\qquad\\text{(\1)}", markdown)

    return markdown


@mcp.tool()
def get_output_settings() -> dict:
    """
    Return resolved output settings so agents can adapt behavior.
    Reads NOUGAT_MCP_SETTINGS or ./settings.json.
    """
    settings, source = load_server_settings()
    default_output_format = resolve_default_output_format(settings)
    rewrite_tags, fix_sized_delimiters = resolve_md_conversion_settings(settings)
    return {
        "settings_source": source,
        "default_output_format": default_output_format,
        "md_rewrite_tags": rewrite_tags,
        "md_fix_sized_delimiters": fix_sized_delimiters,
        "settings_env_var": SETTINGS_ENV_VAR,
    }


@mcp.tool()
def parse_research_paper(
    file_path: str,
    output_format: Literal["default", "mmd", "md"] = "default",
) -> str:
    """
    Highly accurate OCR for academic papers and scientific PDFs using Meta's Nougat model.
    Converts visual structures like tables, formulas, and multi-column layouts into clean Markdown.
    
    Args:
        file_path (str): The absolute path to the PDF file on the local system.
        output_format (str): "default" uses settings.json preferences.
            "mmd" returns raw Nougat output.
            "md" converts math delimiters for broader Markdown renderer compatibility.
    
    Returns:
        str: The extracted text in the requested markup format.
    """
    # Expand user path (e.g., ~/)
    file_path = os.path.abspath(os.path.expanduser(file_path))

    if not os.path.exists(file_path):
        return f"Error: File not found at '{file_path}'."
    
    if not file_path.lower().endswith(".pdf"):
        return "Error: The provided file is not a PDF. Nougat-OCR only supports PDF documents."

    if output_format not in {"default", "mmd", "md"}:
        return "Error: output_format must be 'default', 'mmd', or 'md'."

    settings, _ = load_server_settings()
    effective_output_format = resolve_default_output_format(settings) if output_format == "default" else output_format
    rewrite_tags, fix_sized_delimiters = resolve_md_conversion_settings(settings)

    if not is_nougat_available():
        return (
            "Error: Nougat is not available in the current Python environment. "
            "Please install nougat-ocr (it is included as a dependency of nougat-mcp)."
        )

    try:
        # Create a temporary directory to hold Nougat's output
        with tempfile.TemporaryDirectory() as temp_dir:
            
            # Run Nougat via the current Python interpreter
            # The first time this runs, it may download model weights (~1.4GB)
            # --out: Specifies output directory
            # We use subprocess to isolate the intensive Torch execution
            subprocess.run(
                [sys.executable, "-m", "predict", file_path, "--out", temp_dir],
                check=True,
                capture_output=True,
                text=True
            )
            
            # Nougat creates a Markdown file with a .mmd extension
            # Note: base_name might be different if the PDF name has dots
            # Nougat typically keeps the same base name
            pdf_path = Path(file_path)
            output_file = Path(temp_dir) / f"{pdf_path.stem}.mmd"
            
            # Read the extracted Markdown and return it
            if output_file.exists():
                raw_mmd = output_file.read_text(encoding="utf-8")
                return (
                    mmd_to_markdown(
                        raw_mmd,
                        rewrite_tags=rewrite_tags,
                        fix_sized_delimiters=fix_sized_delimiters,
                    )
                    if effective_output_format == "md"
                    else raw_mmd
                )
            else:
                # Sometimes Nougat might append a suffix or handle naming differently
                # Search for any .mmd file recursively as a fallback
                mmd_files = list(Path(temp_dir).rglob("*.mmd"))
                if mmd_files:
                    raw_mmd = mmd_files[0].read_text(encoding="utf-8")
                    return (
                        mmd_to_markdown(
                            raw_mmd,
                            rewrite_tags=rewrite_tags,
                            fix_sized_delimiters=fix_sized_delimiters,
                        )
                        if effective_output_format == "md"
                        else raw_mmd
                    )
                
                return f"Error: Nougat execution succeeded but no .mmd file was found in {temp_dir}."
                
    except subprocess.CalledProcessError as e:
        stderr_msg = e.stderr.strip() if e.stderr else "Unknown error"
        return f"Error running Nougat: {stderr_msg}"
    except Exception as e:
        return f"An unexpected error occurred during extraction: {str(e)}"

def main():
    """Main entry point for the MCP server."""
    # Default to stdio transport for local use with Claude/Cursor
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
