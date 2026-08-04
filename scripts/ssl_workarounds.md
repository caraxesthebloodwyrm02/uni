Short-term workarounds for missing C-extension modules (_ssl, _ctypes, _sqlite3, ...):

1) Use system Python (dnf install python3) which includes system-built C extensions.

2) Avoid importing packages that pull httpcore2/httpx/truststore. For example, pin or replace libraries that trigger those imports.

3) Vendor pure-Python fallbacks (where available) or use external CLI tools: curl for HTTP, sqlite3 CLI for DB work.

4) Detect missing modules at runtime and fail fast with helpful error messages to avoid unexpected monkeypatching.

Commands to verify current environment:
  .venv/bin/python -c "import ssl; print(getattr(ssl, '__file__', 'no-file'))"
  .venv/bin/python -c "import importlib,sys; print([m for m in ['_ssl','_ctypes','_sqlite3'] if importlib.util.find_spec(m) is None])"

