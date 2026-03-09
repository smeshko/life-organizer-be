## [Unreleased] - 2026-03-09

### Added
- Create ClaudeService for budget text parsing
- Create BudgetService for budget entry persistence
- Add POST /api/v1/budget endpoint

### Changed
- Remove classifier router from main.py
- Delete classifier route file

### Fixed
- Correct test class name casing TestParsebudgetText -> TestParseBudgetText

### Documentation
- Add feature documentation for direct budget flow

### Other
- Update test_main to verify /process endpoint removed
