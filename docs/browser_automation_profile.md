# OS-Level Browser Automation Profile & Constraints Analysis

## 1. System Inventory & OS-Level Binaries
- **Primary Binary**: `/usr/bin/google-chrome`
- **Headless Capabilities**: Native Chrome Headless v2 (`--headless=new`)
- **Package Status**: No `playwright` or `selenium` installed in current Python environment (`.venv`). Node.js environment has `npm` / `corepack` / `@qwen-code/qwen-code`.

## 2. Runtime Constraints & Arguments
- **Headless Execution Flags**:
  - `--headless=new` (modern headless engine)
  - `--no-sandbox` (required for containerized/sandboxed Linux environments)
  - `--disable-gpu` (disables hardware acceleration in non-X11/headless contexts)
  - `--remote-debugging-port=9222` (for CDP / Chrome DevTools Protocol connections)
- **Interpreter Constraints**:
  - The live Python interpreter (`/home/cable/local/lib/python3.13`) does not include the standard C `_ssl` module.
  - Python browser automation wrappers depending on `anyio` or `httpx` with SSL verification must be scoped or bypassed (`no:anyio` in pytest, direct HTTP/CDP over socket or local subprocess wrappers).

## 3. Function & Routing Contract
- **CDP Endpoint Format**: `ws://localhost:9222/devtools/browser/<id>`
- **Routing Destination**: Embedded MCP tools (`mangrove_platform/mcp/apparat_server.py`) route tool requests to internal phase handlers without triggering external HTTP/SSL network dependencies.
