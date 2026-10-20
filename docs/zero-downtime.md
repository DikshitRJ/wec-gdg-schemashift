# Zero-Downtime Migration Architecture

This document describes the production zero-downtime migration architecture for transitioning active workloads from MongoDB to PostgreSQL using SchemaShift.

---

## 1. Zero-Downtime Strategy Overview

Migrating a high-throughput, mission-critical application requires zero downtime and zero data loss. The migration is broken into five distinct operational phases:

```mermaid
flowchart LR
    Phase1["1. Schema Freeze & Baseline ETL"] --> Phase2["2. Dual-Writing & CDC Catch-up"]
    Phase2 --> Phase3["3. Shadow Reads & Spot Check"]
    Phase3 --> Phase4["4. Primary Cutover"]
    Phase4 --> Phase5["5. Decommission Legacy DB"]
```

---

## 2. Five-Phase Migration Lifecycle

### Phase 1: Baseline Bulk Migration
1. Run SchemaShift to produce the frozen schema map (`schema_map.frozen.json`), DDL migrations, and initial bulk ETL scripts.
2. Apply DDL to PostgreSQL: `001_schema.sql`.
3. Record the current MongoDB cluster timestamp $T_0$.
4. Stream historical records from MongoDB to PostgreSQL using `schemashift run --ci` or the generated bulk loader.

### Phase 2: Dual-Writing & Continuous Change Data Capture (CDC)
1. **Application Dual-Write Mode**:
   - Primary Writes $\to$ MongoDB (synchronous, source of truth).
   - Secondary Writes $\to$ PostgreSQL (asynchronous or via message queue like Kafka/RabbitMQ).
2. **CDC Ingestion**:
   - Alternatively, attach a CDC connector (such as Debezium or MongoDB Change Streams) capturing all insert/update/delete events starting from timestamp $T_0$.
   - Events are transformed according to `schema_map.frozen.json` and upserted into PostgreSQL using `ON CONFLICT (id) DO UPDATE`.

### Phase 3: Shadow Reads & Continuous Spot Verification
1. Applications continue serving read traffic from MongoDB.
2. **Shadow Reader Middleware**:
   - A configurable percentage of read requests (e.g. 10% $\to$ 50% $\to$ 100%) asynchronously queries PostgreSQL using the generated SQLAlchemy ORM layer.
   - Discrepancies between Mongo responses and PostgreSQL responses are logged without affecting customer latency or availability.
3. Run `schemashift verify` periodically to validate that checksums and row counts match within the acceptable replication lag window.

### Phase 4: Atomic Cutover Sequence
When replication lag reaches zero and shadow verification reports 100% agreement:
1. Enter brief maintenance drain window (e.g. 5–10 seconds) or enable PostgreSQL as primary write destination.
2. Toggle application environment variable:
   ```env
   DATA_BACKEND=sql
   PG_URI=postgresql://user:pass@pg-prod:5432/shop
   ```
3. PostgreSQL is now the single primary source of truth.
4. MongoDB is switched to read-only replica or dual-write reverse target for safety.

### Phase 5: Decommission & Cleanup
1. Retain MongoDB in read-only mode for 72 hours as an audit archive.
2. Confirm no traffic touches MongoDB.
3. Archive historical snapshot and decommission cluster.

---

## 3. Rollback & Disaster Recovery Protocol

If an unexpected regression occurs prior to Phase 5:
- **Phase 1-2 Failure**: Revert application configuration to single-write MongoDB. Execute `001_schema.down.sql` against PostgreSQL.
- **Phase 3 Failure**: Disable shadow read sampling. Inspect discrepancies in `workspace/out/reports/verify.json`.
- **Phase 4 Failure**: Flip `DATA_BACKEND=mongo`. Since reverse dual-write or forward CDC maintained parity, MongoDB contains all transactions.
