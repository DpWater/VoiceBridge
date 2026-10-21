# Contributing

Use Python 3.11+, keep providers behind the contracts in `app/providers/base.py`, and add automated coverage for behavior changes.

```bash
pip install -e '.[dev]'
pytest
ruff check .
```

Never add API keys, audio recordings, model weights, or private project context to commits. Platform automation requires explicit permission documentation and real-device validation.
