"""Configuration for prompt validation integration tests.

This module handles environment configuration for tests that make real API calls
to Claude Haiku to validate system prompt behavior.
"""

import os

import pytest


def get_anthropic_api_key() -> str | None:
    """Get Anthropic API key from environment.

    Returns:
        API key if found, None otherwise
    """
    return os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("CLAUDE_API_KEY")


def skip_if_no_api_key():
    """Pytest decorator to skip tests if API key is not available.

    Usage:
        @skip_if_no_api_key()
        def test_something():
            ...
    """
    api_key = get_anthropic_api_key()
    return pytest.mark.skipif(
        api_key is None,
        reason="ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable not set",
    )


# Test configuration constants
class PromptValidationConfig:
    """Configuration constants for prompt validation tests."""

    # Minimum confidence threshold for successful extractions
    MIN_CONFIDENCE_THRESHOLD = 0.7

    # Tolerance for float comparisons (amounts)
    AMOUNT_TOLERANCE = 0.01

    # Maximum time to wait for API response (seconds)
    API_TIMEOUT = 30

    # Whether to log full request/response details
    VERBOSE_LOGGING = os.environ.get("PROMPT_VALIDATION_VERBOSE", "false").lower() == "true"

    # Directory for test result logging
    RESULTS_DIR = "test_results"

    # Whether to enable result logging
    ENABLE_RESULT_LOGGING = (
        os.environ.get("PROMPT_VALIDATION_LOG_RESULTS", "false").lower() == "true"
    )
