# Cascading Data Cleanup

## Description
A relational data orchestrator managing referential integrity through ORM-level cascading and soft deletions.

## Architecture Overview
SQLAlchemy implementation utilizing `delete-orphan` cascades for hard deletes and timestamp mutation for logical soft deletes.

## Prerequisites
* Python 3.11+
* `sqlalchemy`
* PostgreSQL or SQLite

## Environment Variables
Configured via a `.env` file (see `.env.example`):
* `DATABASE_URI` - SQLAlchemy connection string (defaults to a local SQLite file)
* `ENABLE_SOFT_DELETE` - boolean toggle; `true` marks rows via `deleted_at` instead of hard-deleting them
* `SOFT_DELETE_RETENTION_DAYS` - how long soft-deleted rows are kept before `purge` removes them
* `SQL_ECHO` - boolean toggle for SQLAlchemy statement logging

## Quick Start & Usage
```
pip install -r requirements.txt
cp .env.example .env      # adjust as needed

python main.py init-db          # create tables
python main.py seed             # insert a sample User -> Post -> Comment tree
python main.py list             # inspect current data

python main.py delete-user 1    # soft- or hard-deletes User 1, cascading to Posts/Comments
python main.py restore-user 1   # undo a soft delete, cascading the restore
python main.py purge --days 30  # hard-delete soft-deleted rows past the retention window
python main.py prune-orphans    # remove rows whose parent record no longer exists
```

`main.py` is the entry point for all functionality; `models.py` defines the ORM models
(with `cascade="all, delete-orphan"` relationships and DB-level `ON DELETE CASCADE`),
and `cleanup_service.py` implements the soft-delete/restore/purge/prune-orphans logic.
