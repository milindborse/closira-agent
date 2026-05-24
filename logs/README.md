# Logs

This folder is created automatically and used for local runtime logs.

- `app.log` — main rotating application log
- `events.jsonl` — structured event stream (one JSON record per line)
- `sop_gaps.jsonl` — SOP gap detections (questions that were out-of-scope or low-confidence)

These files are intended for local debugging/iteration and are typically ignored by git.
