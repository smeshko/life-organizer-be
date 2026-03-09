## [Unreleased] - 2026-03-09

### Added
- Apply rate limit decorator to POST /api/v1/budget
- Configure rate limiter in main.py
- Create rate_limit module with limiter instance
- Add slowapi dependency for rate limiting

### Fixed
- Add Retry-After header and test for rate limit responses
- Add type ignore for slowapi handler type mismatch

### Documentation
- Add rate limiting feature documentation

### Other
- Add rate limiting unit tests
