# Development

Diversion is a Streamlit app backed by Google Routes, Places, and OpenAI.
The repository follows py-canon; see `pyproject.toml` and `.copier-answers.yml`.

- Install: `uv sync --frozen --all-groups`
- Run: `uv run streamlit run app.py`
- Validate: `make ci` and `make conformance`
- Docker: `make ci-docker` using standard Python images

Code lives in `src/diversion/`; `app.py` is the deployment entry point.
Keep tests offline and use fake credentials. Do not read or commit `.env`.
The README is included by Sphinx; edit setup instructions there.
PyPI publication is deferred; see `docs/migration.md`.
