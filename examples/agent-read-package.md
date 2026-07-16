# Agent Reading Example

Use this when an agent receives a CTL package folder and needs to understand it
without a database.

## Task Contract

```text
You are reading a CTL-Core package. Treat the files as the source of truth.
Do not rewrite original files. Read provenance before analysis. Use records and
OKF cards as indexes into the richer HTML and asset files.
```

## Read Order

1. Open `manifest.json` to identify the source, schema, record count, and parser adapters.
2. Open `manifests/provenance.json` to see where the source came from and how it was processed.
3. Open `assets/tables/ctl-records.json` for canonical records, copied asset paths, page numbers, bounding boxes, and semantic fragments.
4. Open `search.json` for fast text lookup.
5. Open `okf/index.md` for OKF-compatible card navigation.
6. Open `documents/*.html` for human-readable review.
7. Follow linked files under `assets/` when you need the original source, copied image, table crop, or other reusable part.

## CLI Checks

```shell
python -m ctl_core inspect output/demo-market-snapshot
python -m ctl_core validate output/demo-market-snapshot
python -m ctl_core search output/demo-market-snapshot "HTML"
```

## Rules For Agents

- Preserve original data exactly.
- Add analysis as a separate layer, never by overwriting source records.
- Keep citations pointed to CTL record IDs, source paths, page numbers, and asset paths.
- Prefer exact values from CTL records. Round or summarize only in downstream analysis.
- If a database index is missing, rebuild it from the CTL package instead of asking the user to re-ingest the source.
