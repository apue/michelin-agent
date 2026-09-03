# Agent review and override contract

Review every `unmatched.csv` row with the signed-in browser. Try, in order: full name and city, base name, folded name, slug/brand form, Michelin coordinates, street address, hotel or venue name, and targeted public-web evidence. Confirm at least title plus city/address; use coordinates or an authoritative address when names differ substantially.

Write a JSON array:

```json
[
  {
    "source_ids": ["restaurant-id"],
    "query": "Current Maps brand name and street address",
    "expected_title": "Current Maps title",
    "expected_address": "City or distinctive address fragment"
  },
  {
    "source_ids": ["restaurant-one", "restaurant-two"],
    "maps_url": "https://www.google.com/maps/...",
    "expected_title": "Shared venue POI",
    "expected_address": "City",
    "note": "Restaurant one: award | cuisine | price; Restaurant two: award | cuisine | price"
  }
]
```

The machine-readable form is `schemas/review-overrides.schema.json`.

`query` or `maps_url` is required. `source_ids` may contain more than one ID only when Google Maps genuinely exposes a shared POI. `expected_title` and `expected_address` are runtime guards, not descriptive comments. Omit `note` for a single source record to use the generated Michelin note.

After `apply-reviews`, inspect the new evidence in `audit.json` and rerun `verify`. Leave a restaurant unresolved rather than inventing a POI when both Maps and authoritative address evidence are insufficient.
