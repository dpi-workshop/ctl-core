# Database Adapter Contract

Database adapters are rebuildable index writers. They read CTL package files and
write optional search, SQL, graph, vector, or analytics indexes. They do not own
the source data.

```text
CTL package -> database adapter -> rebuildable index
```

The CTL package remains the durable source of truth.

## Required Inputs

A database adapter should read these package files when they are present:

| File | Purpose |
| --- | --- |
| `manifest.json` | package identity, schema version, source id, adapter list |
| `manifests/provenance.json` | source custody, parser details, timestamps, traceability |
| `assets/tables/ctl-records.json` | canonical CTL records |
| `search.json` | lightweight text search rows |
| `okf/index.md` | OKF-compatible catalogue entry point |

Adapters may read `documents/*.html` and linked assets when they need richer
HTML fragments, image paths, table crops, or derived embeddings. They should not
modify source package files.

## Required Outputs

Database adapters should write their outputs under an index-specific folder:

```text
indexes/
  sqlite/
    ctl-index.sqlite
    index-manifest.json
  sqlite-vec/
    ctl-vector-index.sqlite
    index-manifest.json
```

The `index-manifest.json` file should record:

- adapter name and version
- upstream dependency name and version
- source package path or package id
- source package schema version
- created timestamp
- indexed record count
- embedding model and dimensions when vectors are used
- tables/collections created
- whether network access was used
- whether credentials were required

## Safety Rules

Database adapters must:

- preserve original CTL files
- use relative paths when storing references back to package assets
- keep CTL record ids intact
- fail gracefully when optional dependencies are missing
- make indexes delete-safe and rebuildable
- record enough metadata to reproduce the index

Database adapters must not:

- parse original PDFs, documents, videos, or websites directly
- mutate `assets/original/`
- rewrite `ctl-records.json`
- overwrite provenance
- hide credentials in package folders
- treat the database as the authoritative memory layer

## Baseline Tables

SQL-style adapters should start with a small common shape:

```text
ctl_package
ctl_records
ctl_record_text
ctl_record_links
ctl_record_assets
ctl_record_tags
ctl_index_runs
```

Vector adapters may add:

```text
ctl_embeddings
ctl_embedding_models
ctl_vector_queries
```

Graph adapters may add:

```text
ctl_nodes
ctl_edges
ctl_graph_runs
```

Exact database schemas can vary, but the CTL record id must remain the join key
back to the package.

## SQLite Implementation Plan

SQLite is the first local index target because it is small, portable, and
already available in Python through the standard library.

Initial implementation:

1. Add a script or CLI command that reads a CTL package and writes
   `indexes/sqlite/ctl-index.sqlite`.
2. Create tables for package metadata, records, text rows, links, tags, and
   assets.
3. Add SQLite FTS for keyword search over record text and HTML fragments.
4. Write `indexes/sqlite/index-manifest.json`.
5. Add smoke tests that build a CTL package, create the SQLite index, and query
   at least one known record.

SQLite should require no network access and no credentials.

## SQLite-vec Implementation Plan

SQLite-vec is the first lightweight local vector target. It should be optional,
detected at runtime, and never vendored into CTL-Core.

Initial implementation:

1. Reuse the SQLite index tables.
2. Detect whether `sqlite-vec` is installed.
3. If it is missing, print install guidance and exit cleanly.
4. Add vector metadata tables for embedding model name, dimensions, and record
   ids.
5. Accept embeddings from a user-provided embedding provider or precomputed
   embedding file. Do not require any hosted model provider in CTL-Core.
6. Write vectors into `indexes/sqlite-vec/ctl-vector-index.sqlite`.
7. Add a sample query path that returns CTL record ids and distances.
8. Record the embedding model and dimensions in
   `indexes/sqlite-vec/index-manifest.json`.

SQLite-vec should sit between plain SQLite keyword search and heavier vector
stores such as Qdrant or LanceDB.

## Future Adapter Targets

After SQLite and SQLite-vec, promote database adapters in this order:

1. DuckDB for local analytics.
2. Kuzu for embedded graph queries.
3. PostgreSQL for multi-user/server deployments.
4. Qdrant for serious vector search.
5. LanceDB for local multimodal vectors.
6. MongoDB for document-shaped workflow metadata.
7. Neo4j/Cypher export for server graph workflows.
8. libSQL/Turso local for SQLite-compatible experiments.

Each adapter should follow the same rule:

```text
The database is an index. The CTL package is the source.
```
