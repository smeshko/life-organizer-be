## [Unreleased] - 2026-03-10

### Added
- Add GET and PUT /plan/{year} budget endpoints
- Add get_plan and upsert_plan service methods
- Add pydantic schemas for budget plan endpoints
- Add BudgetPlan ORM model
- Add alembic migration for budget.plans table

### Fixed
- Deduplicate budget plan entries before upsert

### Documentation
- Add feature documentation for budget plan CRUD endpoints

### Other
- Add unit tests for budget plan API endpoints
- Add unit tests for get_plan and upsert_plan service methods
