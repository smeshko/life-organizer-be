## [Unreleased] - 2026-03-10

### Added
- Add POST /images route for screenshot upload
- Add parse_budget_images method to ClaudeService
- Create vision prompt for revolut screenshot extraction
- Add python-multipart dependency

### Fixed
- Cycle 2 - guard non-dict LLM items, add file validation (empty/type allowlist/size limit)
- Cycle 1 - pass actual media type to Claude Vision, catch ValueError in response parsing

### Documentation
- Add feature documentation for budget screenshot import

### Other
- Add unit tests for ClaudeService vision parsing
- Add unit tests for image upload route
