# Decision Log

Status: accepted

## 2026-09-03: Agent-operated deterministic pipeline

Use deterministic code for repeatable browser work and a repository Skill for contextual review. Agent review is first-class and only genuinely unresolved entries are handed to the user.

## 2026-09-03: Coverage and POI count are separate

Audit source-restaurant coverage independently from unique Google Maps POIs so shared venue listings are represented honestly.

## 2026-09-03: Runtime state is never source code

Datasets, outputs, screenshots, cookies, browser profiles, and secrets are ignored. Tests use synthetic fixtures only.

## 2026-09-03: Private GitHub repository by default

Repository creation is private unless the user explicitly requests public visibility. Publishing source code does not authorize a live Maps mutation or deployment.
