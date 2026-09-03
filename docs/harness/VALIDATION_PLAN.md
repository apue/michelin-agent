# Validation Plan

Status: accepted

## Modes

- `contract-test`: domain schemas, scope filters, audit transitions, and shared-POI mappings.
- `regression-test`: Unicode/query/matcher behaviors observed in the Vietnam E2E run.
- `smoke-test`: CLI entry point and package build.
- `schema-check`: Skill validation and JSON review schema.
- `trace-review`: repository hygiene and tracked-file audit.

## Commands

```bash
uv run python -m unittest discover -s tests -v
uv run michelin-maps --help
uv build
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/michelin-maps-e2e
git status --short
git ls-files
```

## Pass Criteria

- All tests and commands exit zero.
- No runtime or private data is tracked.
- No country-specific runtime module remains.
- README, Skill, CLI help, and schemas agree.

## Known Gap

Live Google Maps behavior depends on the current UI and is verified during an authorized import, not by CI.
