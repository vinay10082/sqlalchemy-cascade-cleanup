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
* `DATABASE_URI`
* `ENABLE_SOFT_DELETE` (boolean toggle)

## Quick Start & Usage
Defines the primary ORM models and executes the cleanup service to prune orphaned records recursively.

## Testing & CI
Executes transaction rollbacks in pytest to validate that cascading relationships perform without violating foreign key constraints.
