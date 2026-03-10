## [Unreleased] - 2026-03-10

### Added
- Create meals ORM models (Recipe, MealHistory, RecipeFeedback)
- Export meals models from db.models package
- Create alembic migration for meals schema and tables

### Fixed
- Align times_made server_default and add ondelete FK tests
- Add ondelete SET NULL to nullable foreign keys

### Documentation
- Add meals schema feature documentation

### Other
- Add unit tests for meals models
