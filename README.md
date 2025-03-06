# Campaign Planner

A Python-based marketing campaign planning system that uses AI to generate, analyze, and optimize marketing campaigns across multiple digital platforms.

## Overview

The Campaign Planner is a sophisticated tool that helps marketers and businesses plan their digital marketing campaigns efficiently. It provides recommendations for ad channels, audience segments, budget allocation, and campaign scheduling.

## Structure

The project is organized into several key components:

### Agents

- **ad_channel_recommender**: Recommends optimal advertising platforms based on campaign requirements
- **audience_segment_analyzer**: Analyzes and segments target audiences
- **brand_industry_classifier**: Classifies brands into relevant industry categories
- **campaign_name_generator**: Generates unique and meaningful campaign names
- **campaign_schedule_recommender**: Suggests optimal campaign timing
- **marketing_budget_allocator**: Allocates budget across different marketing channels

### Core Components

- **graph.py**: Main orchestration component for the campaign planning workflow
- **base/**: Contains base classes and shared functionality

## Key Features

- Multi-platform ad channel recommendations
- Automated campaign naming
- Budget allocation optimization
- Schedule planning
- Industry classification
- Audience segmentation

## Input Requirements

The system accepts various inputs including:
- Brand information (name, description)
- Campaign objectives
- Target audience demographics
- Geographic locations
- Psychographic traits
- Integrated ad platforms

## Output

The system generates comprehensive campaign recommendations including:
- Recommended ad platforms
- Campaign schedule
- Budget allocation
- Campaign naming
- Target audience segments

## Installation
1. Install `uv` in the system
2. Run the following command to create new environment
    ```bash
    uv sync
    ```

## Usage
```bash
uvicorn main:app
```

## Dependencies

- Python 3.x
- Pydantic
- LangChain
- OpenAI GPT-4