# Conditional Documentation Guide

This guide helps you find relevant documentation based on what you're working on.

## Instructions

- Review the task you need to perform
- Check the conditions below
- Read the relevant documentation before proceeding
- Only read documentation if conditions match your task

## Documentation Map

- docs/features/misclassification-feedback-model.md
  - Conditions:
    - When working with the feedback schema or misclassification data
    - When adding new models to the feedback domain
    - When building API endpoints for classification corrections
    - When implementing the classification feedback loop (Epic 2)

- docs/features/direct-budget-flow.md
  - Conditions:
    - When creating new LLM-powered services in the budget domain
    - When modifying the budget transaction processing pipeline
    - When adding new transaction types or currencies to BudgetService
    - When troubleshooting Claude API integration or retry behavior

- docs/features/rate-limiting-llm-endpoints.md
  - Conditions:
    - When adding rate limiting to a new LLM-hitting endpoint
    - When creating new endpoints that call the Claude API (e.g., meals/suggest)
    - When modifying the rate limit configuration or exception handling for slowapi
    - When troubleshooting 429 responses or Retry-After header behavior

- docs/features/budget-screenshot-import.md
  - Conditions:
    - When adding Claude Vision API support to new endpoints
    - When implementing image-based data extraction for the budget domain
    - When modifying the Revolut screenshot parsing prompt or extraction logic
    - When extending the budget import pipeline with new input modalities (e.g., PDF, OCR)

- docs/features/meals-schema-and-models.md
  - Conditions:
    - When creating ORM models or migrations for the meals domain
    - When building API endpoints for recipes, meal history, or recipe feedback
    - When adding new tables to the meals schema namespace
    - When implementing meal planning features (Epic 3: FR13-FR22)

- docs/features/meal-suggestion-endpoint.md
  - Conditions:
    - When adding new LLM-powered suggestion endpoints to the meals domain
    - When modifying the meal suggestion prompt, context gathering, or response parsing
    - When building new service orchestrators that combine DB queries with Claude API calls
    - When extending meal suggestions with new context sources (e.g., dietary restrictions, seasonal ingredients)

- docs/features/meal-feedback-endpoint.md
  - Conditions:
    - When adding feedback or rating endpoints to the meals domain
    - When implementing recipe auto-save logic for LLM-generated content
    - When creating non-LLM meal endpoints that use `Depends(get_db)` session injection
    - When working with the meal feedback loop (FR20, FR21, FR22)
