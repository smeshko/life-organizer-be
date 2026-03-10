# Budget Screenshot Import (Claude Vision)

**Date:** 2026-03-10
**Related Files:** `src/life_organizer/api/routes/budget.py`, `src/life_organizer/services/claude_service.py`, `src/life_organizer/prompts/budget_vision_prompt_v1.txt`

## Overview

Adds a new `POST /api/v1/budget/images` endpoint that accepts Revolut transaction screenshots, extracts all visible transactions using Claude Vision API, and persists them through the existing `BudgetService` pipeline. This enables users to reconcile weeks of expenses by uploading screenshots instead of typing transactions manually.

## What Was Built

- **`POST /api/v1/budget/images`** - Multipart form-data endpoint accepting image files (PNG, JPEG, GIF, WebP)
- **`ClaudeService.parse_budget_images()`** - Vision method that sends base64-encoded images to Claude with a Revolut-specific extraction prompt
- **`budget_vision_prompt_v1.txt`** - Dedicated vision prompt with Revolut layout hints, merchant mappings, and deduplication instructions
- **Shared `_parse_llm_response()`** - Refactored response parsing used by both text and vision paths

## Technical Implementation

### Key Files

- `src/life_organizer/api/routes/budget.py`: Route handler with file validation (type allowlist, 20MB size limit, empty file check)
- `src/life_organizer/services/claude_service.py`: `parse_budget_images()` method with retry logic, `_parse_llm_response()` shared parser
- `src/life_organizer/prompts/budget_vision_prompt_v1.txt`: Vision extraction prompt with Revolut-specific layout rules and merchant-to-category reference

### Key Patterns

- **Multi-image single API call**: All uploaded images are sent in one Claude API request as separate `image` content blocks, followed by a text instruction block. This enables cross-image deduplication for overlapping screenshots.

- **Base64 image encoding with media type passthrough**: Each image is encoded via `base64.standard_b64encode()` and paired with its actual MIME type from the upload (not hardcoded), ensuring Claude receives correct format metadata.

- **Shared response parsing**: `_parse_llm_response()` handles JSON extraction, markdown fence stripping, `extracted_data` array unrolling, and `ClassifiedInput` validation — reused by both `parse_budget_text()` and `parse_budget_images()`.

- **File validation pipeline**: Route validates content type against an allowlist (`image/png`, `image/jpeg`, `image/gif`, `image/webp`), checks file size (20MB Anthropic limit), and rejects empty uploads before reading bytes.

### Code Examples

```python
# How the vision endpoint processes screenshots
image_data: list[tuple[bytes, str]] = []
for file in files:
    content = await file.read()
    image_data.append((content, file.content_type))

classified_list = await claude_service.parse_budget_images(image_data)
return await budget_service.create_entries(classified_list)
```

```python
# How images are sent to Claude Vision API
content_blocks = []
for image_bytes, media_type in images:
    encoded = base64.standard_b64encode(image_bytes).decode("utf-8")
    content_blocks.append({
        "type": "image",
        "source": {"type": "base64", "media_type": media_type, "data": encoded},
    })
content_blocks.append({"type": "text", "text": "Extract all transactions..."})

message = await self.client.messages.create(
    model=self.model, max_tokens=4000,
    system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": content_blocks}],
)
```

## How to Use

1. Capture one or more screenshots of your Revolut transaction history
2. Send a `POST` request to `/api/v1/budget/images` with `Content-Type: multipart/form-data`
3. Attach screenshots as `files` form fields (multiple files supported)
4. Each extracted transaction is returned as a `ProcessingResponse` with `success: true/false`
5. The same 10/minute rate limit applies as the text endpoint

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `CLAUDE_API_KEY` | env var | (required) | Anthropic API key for Claude Vision |
| Claude model | constructor arg | `claude-haiku-4-5` | Model used for vision extraction |
| Max file size | hardcoded | 20 MB | Per-image size limit (Anthropic API limit) |
| Allowed types | hardcoded | PNG, JPEG, GIF, WebP | Accepted image MIME types |
| Max tokens | hardcoded | 4000 | Response token limit for vision (vs 2000 for text) |

## Notes

- The `/images` route is separate from `/` (text) due to FastAPI not supporting two handlers on the same path with different content types
- Vision prompt uses the same date injection mechanism (`_inject_dates_into_prompt()`) as the text prompt
- The vision prompt includes the same merchant-to-category reference table as the text prompt for consistent categorization
- Empty array response from Claude (no transactions found) is surfaced as HTTP 422 to the client
- Retry behavior (3 attempts, exponential backoff) matches the text parsing path
