# Codebase Map

Status: current

## Entry Points

- `michelin_maps/cli.py`: `michelin-maps` command and five workflow stages.
- `skills/michelin-maps-e2e/SKILL.md`: future-agent operating workflow.
- `AGENTS.md`: repository routing, toolchain, data, and authorization constraints.

## Package

- `domain.py`: source scope and normalized restaurant/candidate models.
- `michelin.py`: public Algolia acquisition and completeness checks.
- `queries.py`: base-name, transliteration, city aliases, and query cascade.
- `matching.py`: segmented similarity, coordinate distance, and acceptance guards.
- `maps.py`: CDP lifecycle, Maps extraction, save/note actions, list creation, and verification.
- `pipeline.py`: automatic run, recovery, checkpoints, and reviewed mappings.
- `artifacts.py`: manifest/audit IO, coverage counts, CSV, and summary.

## Contracts and Documentation

- `schemas/review-overrides.schema.json`: agent review handoff schema.
- `skills/michelin-maps-e2e/references/`: review and browser-recovery procedures.
- `docs/harness/`: specification, architecture, decisions, acceptance, validation, and problem evidence.

## Tests

- `test_domain_queries.py`: scope and Unicode/query regressions.
- `test_matching.py`: candidate scoring, coordinate parsing, and city guard.
- `test_michelin.py`: Algolia pagination, headers, and normalization contract.
- `test_artifacts.py`: coverage, shared POIs, and unresolved validation.

## Local-only State

- `.automation/`: signed-in dedicated Chrome profile; relevant to execution, ignored by Git.
- `.venv/`: local uv environment; ignored by Git.
- `.runs/`: fetched selections and execution artifacts; created on demand and ignored by Git.
