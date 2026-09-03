# Browser recovery

Use a dedicated Chrome profile and CDP port. Confirm `http://127.0.0.1:9223/json/version` responds and that Maps shows the expected Google account before mutating the list.

If Playwright opens the websocket but times out while enumerating targets, a crashed Maps tab may remain attached. List `http://127.0.0.1:9223/json/list`, close only stale page targets in the dedicated automation profile, and retry. Preserve the healthy Maps tab and the profile directory.

During a batch, `Page crashed` must escape ordinary candidate-error handling. Recreate the page and retry the same source record once. Recycle pages periodically even when no crash occurs. If Chrome exits, restart it with the same `--user-data-dir`; checkpointed source IDs will resume without duplicate saves.

Never delete or upload the profile. Never reuse a person's normal browsing profile for automation.
