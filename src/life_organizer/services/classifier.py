"""Keyword-based classification service for user input."""

import re

from life_organizer.schemas.classification import ClassifiedInput
from life_organizer.schemas.enums import Category


class KeywordClassifier:
    """Keyword-based classifier for user input.

    Uses weighted keyword matching to determine the category of user input
    and extract relevant structured data (amounts, currencies, items, etc.).

    Attributes:
        keyword_config: Dictionary mapping categories to keyword weights
        confidence_threshold: Minimum confidence score for high-confidence classification
    """

    def __init__(
        self,
        keyword_config: dict[Category, dict[str, float | dict[str, float]]],
        confidence_threshold: float = 0.85,
    ) -> None:
        """Initialize the keyword classifier.

        Args:
            keyword_config: Category to keyword weights mapping
            confidence_threshold: Minimum score for high confidence (default: 0.85)
        """
        self.keyword_config = keyword_config
        self.confidence_threshold = confidence_threshold

    def classify(self, input_text: str) -> ClassifiedInput:
        """Classify user input and extract structured data.

        Args:
            input_text: Raw text input from user

        Returns:
            ClassifiedInput with category, confidence, extracted data, and raw input
        """
        # Normalize input for matching
        normalized_input = input_text.lower().strip()

        # Calculate scores for each category
        category_scores: dict[Category, float] = {}
        for category in [Category.EXPENSE, Category.SHOPPING, Category.REMINDER, Category.CALENDAR]:
            score = self._match_keywords(normalized_input, category)
            if score > 0:
                category_scores[category] = score

        # Determine best category and confidence
        if not category_scores:
            # No matches found
            return ClassifiedInput(
                category=Category.UNKNOWN,
                confidence=0.0,
                extracted_data={},
                raw_input=input_text,
                classifier_source="keyword",
            )

        # Get category with highest score
        best_category = max(category_scores, key=category_scores.get)  # type: ignore
        raw_score = category_scores[best_category]

        # Normalize confidence to 0.0-1.0 range
        # Raw score is sum of weights, normalize by max possible score for that category
        max_possible_score = self._get_max_score(best_category)
        confidence = min(raw_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0

        # Extract structured data based on category
        extracted_data = self._extract_data(normalized_input, best_category)

        return ClassifiedInput(
            category=best_category,
            confidence=confidence,
            extracted_data=extracted_data,
            raw_input=input_text,
            classifier_source="keyword",
        )

    def _match_keywords(self, text: str, category: Category) -> float:
        """Match keywords for a specific category and return weighted score.

        Args:
            text: Normalized input text (lowercase)
            category: Category to match against

        Returns:
            Weighted score based on keyword matches
        """
        if category not in self.keyword_config:
            return 0.0

        keywords = self.keyword_config[category].get("keywords", {})
        if not isinstance(keywords, dict):
            return 0.0

        score = 0.0

        # Sort keywords by length (longest first) to match phrases before words
        sorted_keywords = sorted(keywords.items(), key=lambda x: len(x[0]), reverse=True)

        # Track which parts of text we've matched to avoid double-counting
        matched_positions: set[tuple[int, int]] = set()

        for keyword, weight in sorted_keywords:
            # Find all occurrences of this keyword
            keyword_lower = keyword.lower()
            start = 0
            while True:
                pos = text.find(keyword_lower, start)
                if pos == -1:
                    break

                # Check if this position overlaps with already matched text
                end_pos = pos + len(keyword_lower)
                overlap = False
                for matched_start, matched_end in matched_positions:
                    if not (end_pos <= matched_start or pos >= matched_end):
                        overlap = True
                        break

                if not overlap:
                    score += weight
                    matched_positions.add((pos, end_pos))

                start = pos + 1

        return score

    def _get_max_score(self, category: Category) -> float:
        """Get maximum possible score for a category.

        For normalization purposes, we use the sum of top 3 keyword weights
        as a reasonable maximum expected score.

        Args:
            category: Category to get max score for

        Returns:
            Maximum possible score for normalization
        """
        if category not in self.keyword_config:
            return 1.0

        keywords = self.keyword_config[category].get("keywords", {})
        if not isinstance(keywords, dict):
            return 1.0

        # Get top 3 weights
        weights = sorted(keywords.values(), reverse=True)
        top_weights = weights[:3] if len(weights) >= 3 else weights

        return sum(top_weights) if top_weights else 1.0

    def _extract_data(self, text: str, category: Category) -> dict[str, object]:
        """Extract structured data from text based on category.

        Args:
            text: Normalized input text
            category: Classified category

        Returns:
            Dictionary with extracted structured data
        """
        data: dict[str, object] = {}

        if category == Category.EXPENSE:
            # Extract amount and currency
            amount_match = re.search(r"(\d+(?:[.,]\d{1,2})?)\s*(eur|euro|usd|dollar|€|\$)?", text)
            if amount_match:
                amount_str = amount_match.group(1).replace(",", ".")
                data["amount"] = float(amount_str)

                currency = amount_match.group(2)
                if currency:
                    # Normalize currency
                    currency_map = {
                        "eur": "EUR",
                        "euro": "EUR",
                        "€": "EUR",
                        "usd": "USD",
                        "dollar": "USD",
                        "$": "USD",
                    }
                    data["currency"] = currency_map.get(currency.lower(), currency.upper())
                else:
                    # Check if currency symbol appears elsewhere
                    if "€" in text or "eur" in text or "euro" in text:
                        data["currency"] = "EUR"
                    elif "$" in text or "usd" in text or "dollar" in text:
                        data["currency"] = "USD"

            # Extract merchant/category hints
            merchant_keywords = [
                "restaurant",
                "cafe",
                "coffee",
                "gas",
                "grocery",
                "supermarket",
                "amazon",
            ]
            for merchant in merchant_keywords:
                if merchant in text:
                    data["merchant_hint"] = merchant
                    break

        elif category == Category.SHOPPING:
            # Extract items (simple word extraction after common patterns)
            item_patterns = [
                r"out of\s+(\w+)",
                r"need\s+(\w+)",
                r"buy\s+(\w+)",
                r"add\s+(\w+)",
            ]
            items = []
            for pattern in item_patterns:
                matches = re.findall(pattern, text)
                items.extend(matches)

            # Also check for common standalone items
            common_items = ["milk", "bread", "eggs", "coffee"]
            for item in common_items:
                if item in text and item not in items:
                    items.append(item)

            if items:
                data["items"] = list(set(items))  # Remove duplicates

        elif category == Category.REMINDER:
            # Extract action hints
            action_keywords = ["call", "pick up", "take out", "refill", "send", "email"]
            for action in action_keywords:
                if action in text:
                    data["action"] = action
                    break

        elif category == Category.CALENDAR:
            # Extract time indicators
            time_keywords = ["tomorrow", "next week", "tonight", "today"]
            for time_keyword in time_keywords:
                if time_keyword in text:
                    data["time_reference"] = time_keyword
                    break

        return data
