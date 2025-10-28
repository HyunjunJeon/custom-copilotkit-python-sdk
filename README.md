# Online Seminar Project

This project uses a customized version of CopilotKit Python SDK.

## Structure

```
.
├── copilotkit_sdk/     # Customized CopilotKit Python SDK
├── src/                # Application source code
├── docs/               # Documentation
└── tests/              # Tests
```

## Setup

```bash
# Install dependencies
uv sync

# Run the application
uv run python src/main.py
```

## CopilotKit SDK

This project includes a customized version of the CopilotKit Python SDK.

- Original source: https://github.com/CopilotKit/CopilotKit/tree/main/sdk-python
- See `docs/UPSTREAM_SYNC.md` for upstream synchronization instructions
- See `docs/CUSTOMIZATIONS.md` for details on customizations

## Requirements

- Python 3.13.9
- uv package manager
