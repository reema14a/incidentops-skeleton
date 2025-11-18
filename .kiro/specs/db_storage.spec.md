---

name: IncidentOps SQLite Storage Layer
status: draft
description: Specification for persistent storage using SQLite for pipeline executions, audit summaries, governance analysis, and notification events.
----

IMPORTANT: Kiro must only create files when the corresponding task line with `- [ ]` is executed. Do not create tables, DB utilities, or migration scripts unless their tasks are started. Agents must not contain direct SQL; all DB access must go through the DB utility module.

# Overview

This spec introduces a lightweight persistent storage layer using SQLite to replace ad-hoc JSON persistence. The storage layer will provide reliable persistence for:

* Pipeline execution metadata
* Audit summary records
* Governance analysis results
* Compliance issues
* Notification events

The SQLite file will be located at data/db/incidents.db inside the project container.

# Goals

1. Replace JSON-only persistence with a structured SQLite DB.
2. Provide a single DB utility module for all reads and writes.
3. Ensure agents never issue SQL directly.
4. Make the UI read from the DB for dashboards, governance history, notifications, and audits.
5. Ensure migration compatibility and graceful fallbacks (continue to function if DB missing, optionally falling back to existing JSON if necessary).

# Database Access Layer

The DB utility module resides at db/db_util.py and exposes a clear, documented API for write and read operations. Agents and UI must use these APIs rather than direct SQL.

Public APIs to be implemented (names only; implementation is part of tasks):

* insert_pipeline_run(timestamp, alerts_count, raw_data_path)
* insert_audit_summary(run_id, audit_dict)
* insert_governance_analysis(run_id, gov_dict)
* insert_compliance_issues(run_id, issues_list)
* insert_notification_event(run_id, channel, status, response)
* get_pipeline_runs(limit)
* get_governance_history(limit)
* get_notifications(run_id)
* get_dashboard_metrics()
* get_compliance_stats()

DB writes must be transactional and must log (to pipeline.log) any DB errors without blocking the pipeline run.

# Schema (high level)

1. pipeline_runs

* id: integer primary key autoincrement
* timestamp: text
* alerts_count: integer
* raw_data_path: text (optional)

2. audit_summary

* run_id: integer (foreign key to pipeline_runs)
* status: text
* count: integer
* timestamp: text

3. governance_analysis

* run_id: integer
* risk: text
* escalation: text
* commentary: text

4. compliance_issues

* id: integer primary key autoincrement
* run_id: integer
* issue: text

5. notification_events

* id: integer primary key autoincrement
* run_id: integer
* channel: text
* status: text
* response: text

# Integration points

* Orchestrator: After OpsLog, after Governance, and after Notification stage, orchestrator inserts records via the DB utility APIs.
* NotificationAgent: Uses DB utility only for writing notification events; does not perform any SQL.
* UI: Dashboards, Governance page, Audit Logs page, and Notifications page should read from DB via DB utility read APIs.
* Backwards compatibility: If data/db/incidents.db is not present, the system will fall back to existing JSON persistence while emitting a warning in pipeline.log. The fallback behavior is a temporary compatibility mode.

# Security & File Location

* DB file location: data/db/incidents.db
* Ensure data/db/ is owned by application user inside container and not world-writable.
* Add data/db/incidents.db to .gitignore and never commit DB file.
* Do not store secrets in DB text columns.

# Migration policy

* On first run, db/db_util.py should initialize the DB and apply schema.
* Keep migrations simple and additive. Each migration should be a separate, idempotent SQL statement run by the DB utility during initialization.
* Migration history should be stored in a simple migrations table inside the DB.

# Performance & Concurrency

* Use short-lived SQLite connections per operation (connection-per-transaction).
* Wrap writes in transactions.
* Avoid long-running locks; keep writes small and quick.
* Reads may be performed concurrently; for long-running analytics, consider snapshotting or caching at the UI layer.

# Logging & Error Handling

* All DB errors must be written to logs/pipeline.log with an error level and a descriptive message.
* DB errors should not crash the entire pipeline. Fail gracefully, continue pipeline execution, and set a flag in the returned pipeline output indicating DB write status.

# Tests & Validation

* Unit tests for DB utility: schema creation, insertions, queries, transaction rollbacks.
* Integration test for orchestrator: insert and read back a full run (pipeline_runs + audit_summary + governance_analysis + notifications).
* UI tests verifying dashboard and governance pages read data correctly from the DB.

# Tasks 

## Phase 1 — DB Foundation

* [x] Create db/db_util.py with database initialization (database name defined in settings) skeleton (no agent integration yet)
* [x] Implement SQLite initialization logic so that data/db/incidents.db is created and tables are applied when DB utility is invoked
* [x] Create a local migrations mechanism that runs idempotent table creation statements on initialization
* [x] Add db connection management (context manager pattern) to db/db_util.py

## Phase 2 — Write APIs

* [x] Implement insert_pipeline_run(timestamp, alerts_count, raw_data_path=None)
* [x] Implement insert_audit_summary(run_id, audit_dict)
* [x] Implement insert_governance_analysis(run_id, gov_dict)
* [x] Implement insert_compliance_issues(run_id, issues_list)
* [x] Implement insert_notification_event(run_id, channel, status, response)

## Phase 3 — Read APIs

* [x] Implement get_pipeline_runs(limit=None)
* [x] Implement get_governance_history(limit=None)
* [x] Implement get_notifications(run_id=None)
* [x] Implement get_dashboard_metrics()
* [x] Implement get_compliance_stats()

## Phase 4 — Orchestrator Integration

* [ ] Update orchestrator to call DB write APIs at appropriate pipeline stages:
* [ ] Create pipeline_runs entry at pipeline start or after OpsLog
* [ ] Write audit_summary after OpsLog
* [ ] Write governance_analysis and compliance issues after Governance step
* [ ] Write notification_events after Notification step
* [ ] Ensure DB write failures are logged and set a flag in the returned pipeline output but do not abort pipeline execution

## Phase 5 — UI Integration

* [ ] Update Dashboard page to use get_dashboard_metrics instead of reading JSON
* [ ] Update Governance page to read historical governance from get_governance_history
* [ ] Update Notifications page to read events from get_notifications
* [ ] Update Audit Logs page to read from the DB
* [ ] Add a README snippet describing DB usage for developers
* [ ] Add refresh controls where applicable (manual and optional auto-refresh)

## Phase 6 — Tests & CI

* [ ] Add unit tests for DB utilities under tests/db directory
* [ ] Add integration tests that verify orchestrator writes to DB correctly
* [ ] Add UI tests that run with a temporary SQLite DB fixture
* [ ] Update CI to create a temporary data/db/incidents.db for tests and clean up after

## Phase 7 - Documentation & Steering Updates

* [ ] Update .kiro/steering/structure.md to mandate that only db/db_util.py may contain SQL
* [ ] Update .kiro/steering/standards.md with DB access patterns and transaction rules
* [ ] Add a small developer guide in docs/db.md describing how to inspect the DB, run migrations, and reset local DB
* [ ] Add a short section in README.md describing the new persistence layer and how to run locally

## Phase 8 - Verification Report
* [ ] Generate DB Storage End-to-End Verification Report summarizing:
- DB initialization behavior
- Schema validation
- Insert + read API correctness
- Orchestrator → DB integration correctness
- UI DB-backed rendering validation
- Fallback behavior when DB missing
- Test execution results
- Any performance observations
- Final readiness confirmation

# Acceptance Criteria

* Database initializes automatically in data/db/incidents.db
* Schema matches the tables defined in this spec
* Orchestrator writes all required records (run, audit, governance, notifications)
* UI reads DB-backed data for Dashboard, Audit, Governance, Notifications pages
* DB errors are logged and do not stop the pipeline
* JSON fallback works when DB is missing
* Tests pass for DB read/write operations
* CI uses a temp DB for test runs
* Steering docs reflect DB-only SQL rules
* README contains DB setup and usage description

# Notes

* Keep DB schema minimal initially; extend only when necessary.
* Continue to preserve backward compatibility by providing optional fallback to existing JSON files if the DB file is not present. This fallback must be implemented in db/db_util.py and not in agents or UI.
* All DB operations should produce helpful logs in logs/pipeline.log.

---