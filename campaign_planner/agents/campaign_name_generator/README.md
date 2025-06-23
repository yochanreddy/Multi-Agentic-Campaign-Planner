# Campaign Name Generator

## Overview
Generates unique and meaningful campaign names based on brand information and campaign parameters.

### Files

#### input.py
Defines the input requirements for campaign name generation:
- Brand information
- Campaign objectives
- Target audience details
- Campaign timing
- Ensures proper validation of date formats and required fields

#### output.py
Manages the campaign name output format:
- Enforces naming conventions with underscore separation
- Validates name length and character requirements
- Provides example formats for consistency
- Includes pattern validation for proper formatting

#### process.py
Implements the name generation logic:
- Asynchronous processing capability
- Integration with LLM for creative name generation
- State management and logging functionality