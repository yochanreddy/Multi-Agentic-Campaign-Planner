# Campaign Schedule Recommender

## Overview
Recommends optimal campaign timing and duration based on various factors.

### Files

#### input.py
Defines input requirements for schedule recommendations:
- Brand and industry information
- Target audience details
- Platform preferences
- Campaign objectives
- Geographic considerations

#### output.py
Manages schedule output formatting:
- Campaign start and end dates
- Date format validation
- Pattern matching for consistency
- Proper date string formatting

#### process.py
Implements the scheduling logic:
- Asynchronous processing
- Integration with LLM for intelligent timing recommendations
- Consideration of seasonal factors
- State management and logging