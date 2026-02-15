# Raysurfer Code Caching CLI

[Website](https://www.raysurfer.com) · [Docs](https://docs.raysurfer.com) · [Dashboard](https://www.raysurfer.com/dashboard/api-keys)

CLI tool for searching, uploading, voting, and browsing cached code snippets from the Raysurfer API.

## Installation

```bash
pip install raysurfer-code-caching-cli
```

Or with uv:

```bash
uv pip install raysurfer-code-caching-cli
```

## Setup

```bash
export RAYSURFER_API_KEY=your_api_key_here
```

Get your key from the [dashboard](https://www.raysurfer.com/dashboard/api-keys).

## Commands

```bash
# Search for cached code
raysurfer search "Parse CSV and generate chart"

# Include community public snippets in search
raysurfer search "Parse CSV and generate chart" --public

# Upload code after successful execution
raysurfer upload "Generate bar chart" chart.py

# Vote on cached code
raysurfer vote abc123 --up

# Browse cached patterns
raysurfer patterns
```

## Development

```bash
# Install in dev mode
uv pip install -e .

# Run CLI
uv run raysurfer --help
```

## License

MIT
