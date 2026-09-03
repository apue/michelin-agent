# Acceptance Criteria

Status: accepted

1. A scope compiles to the correct Michelin facet filter for city, region, or country.
2. Paginated Algolia responses normalize into unique restaurant records and a run manifest.
3. Query generation handles accents, Vietnamese `đ`, parenthetical branches, slug aliases, and city aliases.
4. Matching accepts credible direct/list results and records every query and candidate used in its decision.
5. Each successful save has a persisted note containing award, cuisine, and price.
6. A crashed browser page is recreated; a rerun skips completed records.
7. Agent-reviewed overrides can map one POI to one or more source restaurants with recorded evidence.
8. Verification fails on missing source records, duplicate IDs, unresolved statuses, wrong list count, empty notes, or note-set mismatch.
9. The shipped Skill covers acquisition, execution, review, verification, failure recovery, and user handoff.
10. The Git repository contains no restaurant dataset, run output, screenshot, browser profile, credential, cache, or country-specific executable.

## Validation

- Standard-library unit and contract tests.
- CLI help and package build smoke tests.
- Skill frontmatter/scaffold validation.
- Repository secret/data hygiene scan.
- Git tracked-file audit before push.

## Out of Scope

- A live destructive Google Maps acceptance run during repository refactoring.
- Guaranteeing future selectors without maintenance.
