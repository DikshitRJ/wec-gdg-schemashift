## Task ID: SchemaShift

#### `Backend Engineering`, `Databases`, `Developer Tools`, `ORM`, `Agentic Workflows`

Mentors: [Nishant A S](https://github.com/NishantAS) ([+91 6360219728](https://wa.me/916360219728)), [Kushagra Tiwari](https://github.com/Kushagra1122) ([+91 8318661731](https://wa.me/918318661731))

Difficulty: `Hard`

### Description

Build **SchemaShift**, a developer tool that helps teams migrate an application from a **non-SQL (NoSQL) database to a SQL database**.

Teams often start with a document store for speed of iteration, then need relational structure, stronger consistency, and better performance at larger scale. SchemaShift should make that transition practical: inspect the source data, generate the migration scripts, move the data, and update the application's ORM / data-access layer so the app can run against the new database.

You may orchestrate the pipeline with **n8n** and/or **LangGraph**. **Every layer must be hybrid**: combine deterministic and non-deterministic parts, choose wisely which side owns what, and **justify the split** in the README. Prefer deterministic ownership wherever correctness, reproducibility, or production safety is required; use non-deterministic assist for suggestion, ranking, and explanation - never as the sole writer of production side effects.

> **Note:** More deterministic is better. Within each hybrid layer, push as much as possible onto the deterministic side. Non-deterministic pieces should be the smallest useful assist - not the default path. Submissions that keep side effects, scripts, match-%, and verification reproducible will score higher than ones that lean on the LLM for core behavior.

As a stretch goal, support the reverse direction (**SQL → NoSQL**) and a **zero-downtime** migration path.

### Hybrid Design Rule (Required for Every Layer)

SchemaShift must not be “all rules” or “all vibes.” For **each layer**, implement a **hybrid** design:

| Layer | Deterministic side (required) | Non-deterministic side (required assist) | Hybrid outcome |
| --- | --- | --- | --- |
| **Inspect / Infer** | Sample docs, type stats, structural rules, frozen candidate fields | LLM/agent proposes names, relations, embed-vs-table choices | Frozen schema map only after gate |
| **Similarity / Match %** | Normalization + fuzzy/token/type scoring → reproducible `%` | Embeddings / LLM explain *why* scores look that way, flag ambiguous pairs | Report: overall `%`, per-entity `%`, mismatches |
| **Script generation** | DDL / ETL / rollback from frozen map (same inputs → same scripts) | Agent drafts comments, migration notes, risk warnings | Reviewable scripts + narrative |
| **Data migration** | Loaders, FK order, batches, retries, typed transforms | Agent helps diagnose failures / suggest remaps (applied only after re-freeze) | Safe load + assisted recovery |
| **Verify / rollback** | Counts, checksums, spot-checks, rollback scripts | Agent summarizes drift and likely causes | Pass/fail is deterministic |
| **ORM migration** | Models/config from frozen map | Agent suggests query idioms / refactor notes for manual review | Runnable ORM + guided diffs |
| **Orchestration (n8n / LangGraph)** | Deterministic nodes for execute/verify/cutover | Agent nodes for suggest/rank/explain + human-in-the-loop | Explicit graph with gates |

**Non-deterministic path requirements** (whenever that side runs):

1. **Report DB / schema similarity** - how similar source NoSQL is to proposed/target SQL (collections↔tables, fields↔columns, types, relations).
2. **Publish match percentage** - overall `%` plus per-entity / per-field scores (matched vs guessed vs needs review).
3. **Optimize with scoring and normalization** - normalize names/types/shapes first, then score (embedding similarity and/or fuzzy/token overlap). Do not trust raw LLM output alone for the `%`.
4. **Gate low-confidence mappings** - below a documented threshold, require human approval before freezing the schema map.

**Justification requirement:** In the README, for **every layer**, document: hybrid split → what is deterministic → what is non-deterministic → why → safety gate → match-% (where applicable).

### Features to Implement

1. **Source Inspection & Schema Inference (Hybrid)**
  - Connect to a sample NoSQL database (e.g. MongoDB) containing realistic nested documents and collections.
  - **Deterministic:** structural sampling, type frequency stats, rule-based candidate fields/keys.
  - **Non-deterministic:** agent/LLM proposes naming, relations, and embed-vs-table choices.
  - Infer a target relational schema: tables, columns, primary keys, foreign keys, and indexes.
  - Handle nested objects and arrays with a clear, documented strategy (embedding vs. separate tables / join tables).
  - Present the proposed schema in a readable format (CLI output, JSON/YAML report, or a simple UI).
  - Persist a **frozen schema map** only after the hybrid gate; downstream layers consume that map.
2. **Similarity Report & Match Percentage (Hybrid)**
  - Compare source and target database structures and **point out how similar they are** (what aligns cleanly vs. what diverges).
  - Output an explicit **match percentage** (overall and broken down by collection/table and field/column).
  - **Deterministic core:** normalization + fuzzy/token/type scoring that can recompute the `%`.
  - **Non-deterministic assist:** embeddings and/or LLM explanations for ambiguous pairs and reviewer-facing narrative.
  - Optimize with **normalization + scoring** before trusting any LLM-suggested mapping.
  - Surface low-similarity areas so users know where review is required before scripts are generated.
3. **Migration Script Generation (Hybrid)**
  - Automatically generate **all** scripts needed for the move, including at least:
    - SQL DDL to create the target schema
    - Data transformation / load scripts or a documented ETL pipeline
    - Rollback or cleanup scripts where appropriate
  - **Deterministic:** script bodies from the frozen map (reviewable, runnable, reproducible for the sample dataset).
  - **Non-deterministic:** comments, risk notes, and human-readable migration summaries.
  - Persist generated artifacts in a clear directory structure (e.g. `migrations/`, `etl/`, `orm/`).
4. **Data Migration (Hybrid)**
  - Execute the migration against a target SQL database (e.g. PostgreSQL or MySQL) using **deterministic** loaders.
  - Preserve referential integrity and handle type conversions (ObjectIds, dates, nested values, nulls).
  - Provide progress reporting and a post-migration verification step that compares record counts and spot-checks critical fields.
  - **Non-deterministic assist:** diagnose failed rows / suggest remaps; re-run only after the schema map is updated and re-frozen.
  - Fail loudly with actionable errors when data cannot be mapped cleanly.
5. **ORM / Application Layer Migration (Hybrid)**
  - After data is migrated, update (or generate) the application's data-access layer for the new SQL database.
  - **Deterministic:** models/schemas and connection setup from the frozen map.
  - **Non-deterministic:** suggest query refactors / idiomatic examples for reviewer acceptance.
  - Support at least one concrete path, for example:
    - Mongoose / native Mongo driver → Prisma, Drizzle, TypeORM, or Sequelize
  - Generate enough repository/query examples that the sample app can perform basic CRUD on the new database.
  - Document what was changed and what still needs manual review.
6. **Orchestration with n8n and/or LangGraph (Hybrid)**
  - Model the migration pipeline as an explicit workflow using **n8n**, **LangGraph**, or both.
  - Every major stage in the graph must expose both sides: deterministic execute/verify nodes and non-deterministic suggest/explain nodes, with a human-in-the-loop gate where confidence is low.
  - Include workflow nodes that emit the **similarity report** and **match %** before approval.
  - Document the graph/workflow: stages, hybrid split, inputs/outputs, approval gates, and failure handling.
  - Provide a runnable path (exported n8n workflow and/or LangGraph app) that reviewers can follow for the sample migration.
7. **Minimal Sample / Seed (Do Not Overbuild)**
  - Provide a **thin** sample: seed NoSQL data (and optionally a tiny script or stub CRUD) is enough to prove the migration.
  - Do **not** spend significant time on a polished demo UI or full product app - reviewers care about SchemaShift (inference, hybrid pipeline, scripts, match %, ORM update), not the demo.
  - After migration, show the SQL side works with the generated ORM (even a short script or few endpoints is fine).
  - Seed data should be nested enough to exercise inference and relations, but keep the surface area small.

### Bonus Features

*The features above are already the Hard submission. Any bonus below is above that line.*

1. **Zero-Downtime Migration**
  - Design a dual-write / shadow-read / cutover strategy so the application can keep serving traffic during migration.
  - Document the phases (e.g. schema create → backfill → dual write → verify → cutover → decommission).
  - Provide tooling or scripts that support at least one safe cutover path with rollback.
  - **Hybrid:** cutover/dual-write control stays **deterministic**; agents may advise on risk and phase readiness only.
  - If you cannot fully implement the scripts/tooling, still add a dedicated **README** (e.g. `docs/zero-downtime.md`) that clearly explains the strategy, phases, failure modes, rollback plan, and what would be deterministic vs agent-assisted - reviewers will weigh a solid written design when code is incomplete.
2. **Interactive Schema Review**
  - Let the user approve or tweak inferred mappings (rename tables/columns, choose embedding vs. relation) before scripts are generated.
  - A LangGraph interrupt / n8n wait node (or equivalent) for human approval is encouraged.
3. **Bidirectional Migration (SQL → NoSQL)**
  - Support migrating from SQL back to a document store.
  - Generate the corresponding scripts, schema/document model, and ORM updates for the reverse direction.
  - Keep the same **hybrid-per-layer** rule for the reverse path.

### Tips

- Design every layer as hybrid: deterministic for truth/side effects, non-deterministic for suggest/explain - justify both.
- Start with the thin seed, the frozen map, and deterministic DDL. Add the load and the match percentage before you build the workflow graph.
- Keep the sample minimal; put effort into the migration pipeline, not a demo product.
- Freeze the schema map early; regenerate DDL/ETL only from that artifact so runs stay reproducible.
- Make generated SQL and ORM output human-readable - reviewers will read the scripts.
- Prefer explicit mapping rules over magic; document every nested-document decision.
- If you use an LLM, treat it as a planner/suggester - never as the sole writer of production data.
- Normalize before you score; score before you trust a match percentage.
- Show reviewers both the similarity narrative (“these DBs are X% aligned”) and the mismatched fields that drag the score down.
- For zero downtime, study expand/contract and dual-write patterns before coding.
- Keep configuration in a file (source URI, target URI, mapping overrides) rather than hardcoding credentials.
- In the README, include a table: layer → deterministic part → non-deterministic part → justification → safety gate → match-%.
- The README must include the commands to run the sample migration locally. A public URL is optional and only if a small UI exists.

### Useful Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/current/)
- [MongoDB Schema Design Patterns](https://www.mongodb.com/docs/manual/data-modeling/)
- [Prisma Schema Reference](https://www.prisma.io/docs/orm/prisma-schema)
- [Expand/Contract Database Migration Pattern](https://openpracticelibrary.com/practice/expand-and-contract-pattern/)
- [Dual Writes and Data Consistency](https://martinfowler.com/articles/patterns-of-distributed-systems/dual-writes.html)
- [n8n Documentation](https://docs.n8n.io/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangGraph Human-in-the-Loop](https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/)
