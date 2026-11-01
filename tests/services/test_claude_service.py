"""Tests for ClaudeService budget text and image parsing."""

import logging
from unittest.mock import AsyncMock, MagicMock

import anthropic
import pytest
from fastapi import HTTPException

from life_organizer.schemas.enums import Category
from life_organizer.services.claude_service import _REQUEST_TIMEOUT_SECONDS, ClaudeService


@pytest.fixture
def service() -> ClaudeService:
    """Create a ClaudeService instance with a fake API key."""
    return ClaudeService(api_key="test-key", model="claude-opus-5-5", effort="low")


def _block(block_type: str, text: str = "") -> MagicMock:
    """Create a mock content block of the given type."""
    block = MagicMock()
    block.type = block_type
    block.text = text
    return block


def _mock_claude_response(
    response_text: str,
    *,
    stop_reason: str = "end_turn",
    leading_blocks: tuple[MagicMock, ...] = (),
    refusal_category: str | None = None,
) -> AsyncMock:
    """Create a mock Anthropic beta messages.create response."""
    message = MagicMock()
    message.content = [*leading_blocks, _block("text", response_text)]
    message.stop_reason = stop_reason
    message.model = "claude-opus-5-5"
    if stop_reason == "refusal":
        message.stop_details.category = refusal_category
    return AsyncMock(return_value=message)


_BUDGET_JSON = (
    '[{"category": "budget", "confidence": 0.9, "extracted_data": {"amount": 5.0, '
    '"currency": "EUR", "transaction_type": "Expenses", "category": "Other", '
    '"date": "2026-03-09"}, "raw_input": "test"}]'
)


class TestParseBudgetText:
    """Tests for parse_budget_text method."""

    @pytest.mark.asyncio
    async def test_single_transaction(self, service: ClaudeService) -> None:
        """Single budget transaction should return one ClassifiedInput."""
        response_json = """[{
            "category": "budget",
            "confidence": 0.95,
            "extracted_data": {
                "amount": 4.50,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Eat out",
                "merchant": "coffee shop",
                "date": "2026-03-09"
            },
            "raw_input": "coffee 4.50"
        }]"""

        service.client.beta.messages.create = _mock_claude_response(response_json)

        results = await service.parse_budget_text("coffee 4.50")

        assert len(results) == 1
        assert results[0].category == Category.BUDGET
        assert results[0].confidence == 0.95
        assert results[0].extracted_data["amount"] == 4.50
        assert results[0].extracted_data["currency"] == "EUR"
        assert results[0].classifier_source == "llm"

    @pytest.mark.asyncio
    async def test_multi_transaction(self, service: ClaudeService) -> None:
        """Multiple transactions should return multiple ClassifiedInput objects."""
        response_json = """[
            {
                "category": "budget",
                "confidence": 0.9,
                "extracted_data": {
                    "amount": 12.0,
                    "currency": "EUR",
                    "transaction_type": "Expenses",
                    "category": "Eat out",
                    "merchant": null,
                    "date": "2026-03-09"
                },
                "raw_input": "lunch 12 eur"
            },
            {
                "category": "budget",
                "confidence": 0.9,
                "extracted_data": {
                    "amount": 4.50,
                    "currency": "EUR",
                    "transaction_type": "Expenses",
                    "category": "Eat out",
                    "merchant": null,
                    "date": "2026-03-09"
                },
                "raw_input": "coffee 4.50"
            }
        ]"""

        service.client.beta.messages.create = _mock_claude_response(response_json)

        results = await service.parse_budget_text("lunch 12 eur, coffee 4.50")

        assert len(results) == 2
        assert results[0].extracted_data["amount"] == 12.0
        assert results[1].extracted_data["amount"] == 4.50

    @pytest.mark.asyncio
    async def test_empty_input(self, service: ClaudeService) -> None:
        """Empty input should return ClassifiedInput with confidence 0.0."""
        results = await service.parse_budget_text("")

        assert len(results) == 1
        assert results[0].category == Category.BUDGET
        assert results[0].confidence == 0.0
        assert results[0].extracted_data == {}

    @pytest.mark.asyncio
    async def test_whitespace_input(self, service: ClaudeService) -> None:
        """Whitespace-only input should return ClassifiedInput with confidence 0.0."""
        results = await service.parse_budget_text("   ")

        assert len(results) == 1
        assert results[0].category == Category.BUDGET
        assert results[0].confidence == 0.0

    @pytest.mark.asyncio
    async def test_transaction_limit_exceeded(self, service: ClaudeService) -> None:
        """More than 15 transactions should raise HTTPException 422."""
        # 16 commas = ~17 transactions
        text = ", ".join(["item"] * 17)

        with pytest.raises(HTTPException) as exc_info:
            await service.parse_budget_text(text)

        assert exc_info.value.status_code == 422
        assert "Maximum 15 transactions" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_claude_api_error_raises_without_retry(self, service: ClaudeService) -> None:
        """A Claude API error is raised after a single attempt."""
        service.client.beta.messages.create = AsyncMock(
            side_effect=anthropic.APIError(
                message="Service unavailable", request=MagicMock(), body=None
            )
        )

        with pytest.raises(anthropic.APIError):
            await service.parse_budget_text("test 5")

        assert service.client.beta.messages.create.call_count == 1

    @pytest.mark.asyncio
    async def test_thinking_block_before_text_parses(self, service: ClaudeService) -> None:
        """A leading thinking block is skipped and the text block is parsed."""
        service.client.beta.messages.create = _mock_claude_response(
            _BUDGET_JSON, leading_blocks=(_block("thinking", "let me think"),)
        )

        results = await service.parse_budget_text("test 5")

        assert len(results) == 1
        assert results[0].category == Category.BUDGET
        assert results[0].extracted_data["amount"] == 5.0

    @pytest.mark.asyncio
    async def test_refusal_returns_unknown_with_error(
        self, service: ClaudeService, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A refusal becomes an UNKNOWN input carrying an error, and logs the category."""
        service.client.beta.messages.create = _mock_claude_response(
            "", stop_reason="refusal", refusal_category="general_harms"
        )

        with caplog.at_level(logging.WARNING):
            results = await service.parse_budget_text("test 5")

        assert len(results) == 1
        assert results[0].category == Category.UNKNOWN
        assert results[0].error == "Claude declined to process this input"
        assert "general_harms" in caplog.text

    @pytest.mark.asyncio
    async def test_no_text_block_returns_unknown(self, service: ClaudeService) -> None:
        """A response without any text block becomes UNKNOWN with no error."""
        message = MagicMock()
        message.content = [_block("thinking", "hmm")]
        message.stop_reason = "end_turn"
        service.client.beta.messages.create = AsyncMock(return_value=message)

        results = await service.parse_budget_text("test 5")

        assert len(results) == 1
        assert results[0].category == Category.UNKNOWN
        assert results[0].error is None

    @pytest.mark.asyncio
    async def test_request_uses_model_effort_and_fallback(self, service: ClaudeService) -> None:
        """The request carries the model, effort, fallback and beta flag."""
        mock_create = _mock_claude_response(_BUDGET_JSON)
        service.client.beta.messages.create = mock_create

        await service.parse_budget_text("test 5")

        kwargs = mock_create.call_args.kwargs
        assert kwargs["model"] == "claude-opus-5-5"
        assert kwargs["max_tokens"] == 16000
        assert kwargs["output_config"] == {"effort": "low"}
        assert kwargs["fallbacks"] == "default"
        assert kwargs["betas"] == ["server-side-fallback-2026-07-01"]

    def test_client_has_one_attempt_with_long_timeout(self, service: ClaudeService) -> None:
        """One attempt gets most of the iOS client's 60 s, and never exceeds it."""
        assert service.client.max_retries == 0
        assert service.client.timeout == _REQUEST_TIMEOUT_SECONDS
        assert 50 <= _REQUEST_TIMEOUT_SECONDS < 60

    @pytest.mark.asyncio
    async def test_json_parse_error_returns_unknown(self, service: ClaudeService) -> None:
        """Invalid JSON response should return UNKNOWN classification."""
        service.client.beta.messages.create = _mock_claude_response("not valid json")

        results = await service.parse_budget_text("coffee 5")

        assert len(results) == 1
        assert results[0].category == Category.UNKNOWN
        assert results[0].confidence == 0.0

    @pytest.mark.asyncio
    async def test_markdown_code_fences_stripped(self, service: ClaudeService) -> None:
        """Markdown code fences should be stripped from response."""
        response_json = '```json\n[{"category": "budget", "confidence": 0.9, "extracted_data": {"amount": 10.0, "currency": "EUR", "transaction_type": "Expenses", "category": "Groceries", "date": "2026-03-09"}, "raw_input": "groceries 10"}]\n```'

        service.client.beta.messages.create = _mock_claude_response(response_json)

        results = await service.parse_budget_text("groceries 10")

        assert len(results) == 1
        assert results[0].extracted_data["amount"] == 10.0
        assert results[0].extracted_data["category"] == "Groceries"

    @pytest.mark.asyncio
    async def test_unrolled_extracted_data_array(self, service: ClaudeService) -> None:
        """extracted_data as array should be unrolled into separate ClassifiedInputs."""
        response_json = """[{
            "category": "budget",
            "confidence": 0.8,
            "extracted_data": [
                {
                    "amount": 45.0,
                    "currency": "EUR",
                    "transaction_type": "Expenses",
                    "category": "Groceries",
                    "date": "2026-03-09"
                },
                {
                    "amount": 50.0,
                    "currency": "EUR",
                    "transaction_type": "Expenses",
                    "category": "Groceries",
                    "date": "2026-03-09"
                }
            ],
            "raw_input": "groceries 45,50"
        }]"""

        service.client.beta.messages.create = _mock_claude_response(response_json)

        results = await service.parse_budget_text("groceries 45,50")

        assert len(results) == 2
        assert results[0].extracted_data["amount"] == 45.0
        assert results[1].extracted_data["amount"] == 50.0

    @pytest.mark.asyncio
    async def test_category_always_budget(self, service: ClaudeService) -> None:
        """All returned items should have category=BUDGET regardless of LLM response."""
        response_json = '[{"category": "unknown", "confidence": 0.5, "extracted_data": {"amount": 5.0, "currency": "EUR", "transaction_type": "Expenses", "category": "Other", "date": "2026-03-09"}, "raw_input": "test"}]'

        service.client.beta.messages.create = _mock_claude_response(response_json)

        results = await service.parse_budget_text("test 5")

        assert results[0].category == Category.BUDGET


class TestGetSystemPromptWithCurrentDate:
    """Tests for _get_system_prompt_with_current_date."""

    def test_injects_today_date(self, service: ClaudeService) -> None:
        """System prompt should have today's date injected."""
        import datetime

        today = datetime.date.today()
        prompt = service._get_system_prompt_with_current_date()

        assert today.isoformat() in prompt
        assert "2025-11-04" not in prompt  # placeholder removed

    def test_injects_yesterday_date(self, service: ClaudeService) -> None:
        """System prompt should have yesterday's date injected."""
        import datetime

        yesterday = datetime.date.today() - datetime.timedelta(days=1)
        prompt = service._get_system_prompt_with_current_date()

        assert yesterday.isoformat() in prompt
        assert "2025-11-03" not in prompt  # placeholder removed


class TestEstimateTransactionCount:
    """Tests for _estimate_transaction_count."""

    def test_single_transaction(self, service: ClaudeService) -> None:
        """Single item should return 1."""
        assert service._estimate_transaction_count("coffee 5") == 1

    def test_comma_separated(self, service: ClaudeService) -> None:
        """Comma-separated items should count correctly."""
        assert service._estimate_transaction_count("coffee 5, lunch 12") == 2

    def test_and_separated(self, service: ClaudeService) -> None:
        """'and'-separated items should count correctly."""
        assert service._estimate_transaction_count("coffee 5 and lunch 12") == 2

    def test_empty_input(self, service: ClaudeService) -> None:
        """Empty input should return 0."""
        assert service._estimate_transaction_count("") == 0

    def test_mixed_separators(self, service: ClaudeService) -> None:
        """Mixed comma and 'and' separators should count correctly."""
        assert service._estimate_transaction_count("a 1, b 2 and c 3") == 3


class TestParseBudgetImages:
    """Tests for parse_budget_images method."""

    @pytest.mark.asyncio
    async def test_thinking_block_before_text_parses(self, service: ClaudeService) -> None:
        """A leading thinking block is skipped and the text block is parsed."""
        service.client.beta.messages.create = _mock_claude_response(
            _BUDGET_JSON, leading_blocks=(_block("thinking", "let me think"),)
        )

        results = await service.parse_budget_images([(b"fake-png-bytes", "image/png")])

        assert len(results) == 1
        assert results[0].category == Category.BUDGET
        assert results[0].extracted_data["amount"] == 5.0

    @pytest.mark.asyncio
    async def test_refusal_returns_unknown_with_error(
        self, service: ClaudeService, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A refusal becomes an UNKNOWN input carrying an error, and logs the category."""
        service.client.beta.messages.create = _mock_claude_response(
            "", stop_reason="refusal", refusal_category="cyber"
        )

        with caplog.at_level(logging.WARNING):
            results = await service.parse_budget_images([(b"fake-png-bytes", "image/png")])

        assert len(results) == 1
        assert results[0].category == Category.UNKNOWN
        assert results[0].error == "Claude declined to process this input"
        assert "cyber" in caplog.text

    @pytest.mark.asyncio
    async def test_single_image_returns_classified_inputs(self, service: ClaudeService) -> None:
        """Single image should return list of ClassifiedInput objects."""
        response_json = """[{
            "category": "budget",
            "confidence": 0.9,
            "extracted_data": {
                "amount": 4.50,
                "currency": "EUR",
                "transaction_type": "Expenses",
                "category": "Eat out",
                "merchant": "Starbucks",
                "date": "2026-03-09"
            },
            "raw_input": "Starbucks - €4.50"
        }]"""

        service.client.beta.messages.create = _mock_claude_response(response_json)

        results = await service.parse_budget_images([(b"fake-png-bytes", "image/png")])

        assert len(results) == 1
        assert results[0].category == Category.BUDGET
        assert results[0].confidence == 0.9
        assert results[0].extracted_data["amount"] == 4.50
        assert results[0].extracted_data["merchant"] == "Starbucks"
        assert results[0].classifier_source == "llm"

    @pytest.mark.asyncio
    async def test_multiple_images_returns_combined_list(self, service: ClaudeService) -> None:
        """Multiple images should return combined ClassifiedInput list."""
        response_json = """[
            {
                "category": "budget",
                "confidence": 0.9,
                "extracted_data": {
                    "amount": 12.0,
                    "currency": "EUR",
                    "transaction_type": "Expenses",
                    "category": "Groceries",
                    "merchant": "Lidl",
                    "date": "2026-03-08"
                },
                "raw_input": "Lidl - €12.00"
            },
            {
                "category": "budget",
                "confidence": 0.85,
                "extracted_data": {
                    "amount": 45.0,
                    "currency": "EUR",
                    "transaction_type": "Expenses",
                    "category": "Transport",
                    "merchant": "Bolt",
                    "date": "2026-03-09"
                },
                "raw_input": "Bolt - €45.00"
            }
        ]"""

        service.client.beta.messages.create = _mock_claude_response(response_json)

        results = await service.parse_budget_images(
            [(b"image1-bytes", "image/png"), (b"image2-bytes", "image/jpeg")]
        )

        assert len(results) == 2
        assert results[0].extracted_data["amount"] == 12.0
        assert results[1].extracted_data["amount"] == 45.0

    @pytest.mark.asyncio
    async def test_image_index_parsed_per_transaction(self, service: ClaudeService) -> None:
        """Each item keeps the image_index the model gave it."""
        item = (
            '{"category": "budget", "confidence": 0.9, "extracted_data": '
            '{"amount": %s, "currency": "EUR", "transaction_type": "Expenses", '
            '"category": "Groceries", "merchant": "Lidl", "date": "2026-03-08"}, '
            '"raw_input": "x", "image_index": %d}'
        )
        service.client.beta.messages.create = _mock_claude_response(
            "[" + item % (12.0, 0) + "," + item % (45.0, 1) + "]"
        )

        results = await service.parse_budget_images([(b"a", "image/png"), (b"b", "image/png")])

        assert [r.image_index for r in results] == [0, 1]

    @pytest.mark.asyncio
    async def test_failed_image_item_parsed(self, service: ClaudeService) -> None:
        """A failed-photo item keeps its error and image_index."""
        service.client.beta.messages.create = _mock_claude_response(
            '[{"category": "budget", "confidence": 0.0, "extracted_data": {}, '
            '"raw_input": "[image 2]", "image_index": 1, "error": "Blurry"}]'
        )

        results = await service.parse_budget_images([(b"a", "image/png"), (b"b", "image/png")])

        assert len(results) == 1
        assert results[0].error == "Blurry"
        assert results[0].image_index == 1
        assert results[0].extracted_data == {}

    @pytest.mark.asyncio
    async def test_out_of_range_image_index_dropped(self, service: ClaudeService) -> None:
        """An image_index outside the uploaded range becomes None."""
        service.client.beta.messages.create = _mock_claude_response(
            '[{"category": "budget", "confidence": 0.9, "extracted_data": '
            '{"amount": 1.0, "currency": "EUR", "transaction_type": "Expenses", '
            '"category": "Groceries", "date": "2026-03-08"}, '
            '"raw_input": "x", "image_index": 5}]'
        )

        results = await service.parse_budget_images([(b"a", "image/png"), (b"b", "image/png")])

        assert len(results) == 1
        assert results[0].image_index is None
        assert results[0].extracted_data["amount"] == 1.0

    @pytest.mark.asyncio
    async def test_unrolled_items_keep_image_index(self, service: ClaudeService) -> None:
        """Unrolling an extracted_data array copies image_index onto each result."""
        tx = (
            '{"amount": %s, "currency": "EUR", "transaction_type": "Expenses", '
            '"category": "Groceries", "date": "2026-03-08"}'
        )
        service.client.beta.messages.create = _mock_claude_response(
            '[{"category": "budget", "confidence": 0.9, "extracted_data": ['
            + tx % 1.0
            + ","
            + tx % 2.0
            + '], "raw_input": "x", "image_index": 1}]'
        )

        results = await service.parse_budget_images([(b"a", "image/png"), (b"b", "image/png")])

        assert [r.image_index for r in results] == [1, 1]
        assert [r.extracted_data["amount"] for r in results] == [1.0, 2.0]

    def test_vision_prompt_mentions_image_index(self, service: ClaudeService) -> None:
        """The vision prompt asks the model for image_index."""
        assert "image_index" in service._get_vision_prompt_with_current_date()

    @pytest.mark.asyncio
    async def test_api_error_raises_without_retry(self, service: ClaudeService) -> None:
        """An API error is raised after a single attempt."""
        service.client.beta.messages.create = AsyncMock(
            side_effect=anthropic.APIError(
                message="Service unavailable",
                request=MagicMock(),
                body=None,
            )
        )

        with pytest.raises(anthropic.APIError):
            await service.parse_budget_images([(b"fake-png-bytes", "image/png")])

        assert service.client.beta.messages.create.call_count == 1

    @pytest.mark.asyncio
    async def test_malformed_json_returns_unknown(self, service: ClaudeService) -> None:
        """Malformed JSON response should return unknown classification."""
        service.client.beta.messages.create = _mock_claude_response("not valid json at all")

        results = await service.parse_budget_images([(b"fake-png-bytes", "image/png")])

        assert len(results) == 1
        assert results[0].category == Category.UNKNOWN
        assert results[0].confidence == 0.0

    @pytest.mark.asyncio
    async def test_empty_image_list_returns_empty(self, service: ClaudeService) -> None:
        """Empty image list should return empty list."""
        results = await service.parse_budget_images([])

        assert results == []
