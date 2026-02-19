# Walkthrough: Nougat-OCR MCP Server

## Accomplishments

1. **Refactored to Production Standards**: Transitioned from a flat script to a `src`-layout Python package.
2. **Robust Tooling**: Improved the `parse_research_paper` tool with:
    - Path expansion and absolute path resolution.
    - CLI availability check (`shutil.which`).
    - Fallback logic to find `.mmd` files if naming deviates from the PDF stem.
    - Clearer error messages for non-PDF files or missing dependencies.
3. **Comprehensive Metadata**: Added detailed docstrings for tool parameters to help LLMs understand how to use the server.
4. **Publishing Ready**:
    - Added `LICENSE` (MIT).
    - Added `README.md` with configuration examples.
    - Updated `pyproject.toml` with entry points and metadata.

## Structure

```text
src/nougat_mcp/
├── __init__.py
├── server.py  # The MCP Server
└── main.py    # Placeholder for future expansion
```

## How to Test

1. Install in editable mode: `pip install -e .`
2. Run the server: `nougat-mcp`
3. Try parsing a paper via an MCP client:

    ```python
    # Tool call
    parse_research_paper(file_path="/path/to/paper.pdf")
    ```

## Performance Note

`nougat-ocr` downloads model weights on the first run (~1.4GB). Ensure the server has enough timeout if being initialized from a cold start.
