# Database And Index Adapters

Database/index adapters rebuild searchable indexes from CTL packages.

They may:

- read CTL package files
- write local or remote indexes
- create SQL, graph, vector, or search-store records

They must not:

- parse original source documents directly
- alter CTL package source-of-truth files
- connect to social platforms
- manage workflow jobs

Database adapters are optional acceleration layers. CTL package files remain
the durable source.

See [../../../docs/database-adapter-contract.md](../../../docs/database-adapter-contract.md)
for the shared contract, safety rules, baseline tables, and SQLite/SQLite-vec
implementation plan.

Examples:

- SQLite
- SQLite-vec
- DuckDB
- PostgreSQL
- MongoDB
- Qdrant
- Kuzu
- Neo4j
- LanceDB
- libSQL/Turso local

## Lightweight Local Vector Option

`sqlite-vec` belongs between plain SQLite and heavier vector stores such as
Qdrant or LanceDB. It should be treated as an optional local vector index:

- CTL package files remain the source of truth.
- SQLite FTS can handle keyword search.
- `sqlite-vec` can hold rebuildable embeddings for semantic search.
- The resulting `.sqlite` file can sit beside a CTL package and be deleted or
  rebuilt without damaging the package.

Do not vendor `sqlite-vec` into CTL-Core. Detect whether the user installed it,
then fail gracefully with install guidance when it is unavailable.
