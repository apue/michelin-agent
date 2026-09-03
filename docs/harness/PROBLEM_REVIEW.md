# Problem Review

Status: resolved

## Symptom

The first real `fetch --scope city:bangkok` smoke test returned HTTP 403 while fake-session unit tests passed.

## Evidence

- Response body: `Method not allowed with this referer`.
- The same payload and public key failed with the library's minimal headers.
- Adding Michelin `Origin`, same-origin `Referer`, and a browser user agent returned HTTP 200; changing JSON to `text/plain` was unnecessary.

## Diagnosis

Triage: contract-mismatch. Michelin's Algolia edge policy validates browser-origin headers. The client omitted that part of the public-search request contract.

## Repair

Add the required origin headers in `MichelinClient` and a regression assertion in `test_michelin.py`. Keep JSON encoding and the existing query contract unchanged.

## Validation

The focused test must fail before the fix, then all tests plus live city and country fetch smoke tests must pass.
