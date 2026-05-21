# Contributing to Punyaku

Thanks for considering a contribution!

## Quick environment

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt -r requirements_dev.txt
```

## Workflow

1. Create a topic branch from `main`:

   ```bash
   git checkout -b feat/<short-description>
   ```

2. Run the lint + tests before committing:

   ```bash
   ruff check app tests
   QT_QPA_PLATFORM=offscreen pytest -q
   QT_QPA_PLATFORM=offscreen python -m app --check
   ```

3. Push and open a PR. Fill out the PR template (`.github/PULL_REQUEST_TEMPLATE.md`).

## Code style

- Python 3.10+ type hints required for new public APIs.
- Keep modules free of `import torch` / `import cv2` / `import librosa`
  at module scope. Use lazy imports inside functions instead.
- The engine layer (`app/engine/...`) must not import `PyQt6`.

## Adding an AI plugin

See [`docs/AI_PLUGINS.md`](docs/AI_PLUGINS.md) — drop a file under
`app/ai/<category>/` and use the `@register` decorator.

## Reporting issues

Please attach `logs/punyaku.log` (rotated, max 10 MB) and the output of
`python -m app --check` when filing a bug.
