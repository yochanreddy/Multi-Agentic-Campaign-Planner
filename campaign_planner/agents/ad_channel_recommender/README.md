# Ad Channel Recommender

## Overview
This component recommends digital advertising platforms based on campaign requirements and target audience characteristics.

### Files

#### input.py
Defines the input schema for the ad channel recommender using Pydantic models. Captures essential campaign information including:
- Brand details
- Campaign objective
- Target audience demographics
- Geographic locations
- Psychographic traits
- Available ad platforms

#### output.py
Handles the output formatting for ad channel recommendations:
- Defines the output schema for recommended platforms
- Supports multiple channel types (Meta, Google, LinkedIn, TikTok)
- Includes validation and logging functionality

#### process.py
Contains the core processing logic:
- Implements async processing of recommendations
- Integrates with LLM for intelligent platform selection
- Handles state management and logging