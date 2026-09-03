# Repository instructions

## Workflow routing

For requests to fetch a Michelin selection and save it to Google Maps, read and follow `skills/michelin-maps-e2e/SKILL.md` before acting. Read only the linked reference needed for the current stage.

## Toolchain

- Use `uv` and the repository `pyproject.toml`/`uv.lock`.
- Run tests with `uv run python -m unittest discover -s tests -v`.
- Use the `michelin-maps` CLI instead of country-specific scripts.

## Data boundary

- Put all fetched manifests, audits, review overrides, screenshots, and reports under `.runs/`.
- Never stage or force-add `.runs/`, `data/`, `.automation/`, `.pw-profile/`, `.env`, or browser/profile artifacts.
- Test fixtures must be synthetic and must not contain scraped restaurant datasets.

## External mutations

Fetching and discovery are read-only. Creating lists, saving POIs, and editing notes require an explicit user request authorizing those Google Maps changes. Never bypass authentication or access controls.
