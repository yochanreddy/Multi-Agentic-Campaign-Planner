# Campaign & Creative Planner

A Python-based marketing campaign and creative planning system that uses AI to generate, analyze, and optimize marketing campaigns and creatives across multiple digital platforms.

## Overview

The Campaign & Creative Planner is a sophisticated tool that helps marketers and businesses plan their digital marketing campaigns and generate creatives efficiently. It provides recommendations for ad channels, audience segments, budget allocation, campaign scheduling, and generates optimized creatives for different platforms.

## Structure

The project is organized into several key components:

### Campaign Planner Agents

- **ad_channel_recommender**: Recommends optimal advertising platforms based on campaign requirements
- **audience_segment_analyzer**: Analyzes and segments target audiences
- **brand_industry_classifier**: Classifies brands into relevant industry categories
- **campaign_name_generator**: Generates unique and meaningful campaign names
- **campaign_schedule_recommender**: Suggests optimal campaign timing
- **marketing_budget_allocator**: Allocates budget across different marketing channels

### Creative Planner Agents

- **prompt_generator**: Generates optimized prompts for image generation
- **image_generator**: Creates campaign images based on prompts
- **image_analyzer**: Analyzes generated images for quality and relevance
- **mask_generator**: Creates masks for image editing
- **cta_generator**: Generates call-to-action text
- **text_layering**: Adds text overlays to images

### Core Components

- **campaign_planner/graph.py**: Main orchestration component for the campaign planning workflow
- **creative_planner/graph.py**: Main orchestration component for the creative planning workflow
- **base/**: Contains base classes and shared functionality

## Key Features

### Campaign Planning Features

- Multi-platform ad channel recommendations
- Automated campaign naming
- Budget allocation optimization
- Schedule planning
- Industry classification
- Audience segmentation

### Creative Generation Features

- AI-powered image generation
- Image analysis and optimization
- Text overlay generation
- Call-to-action generation
- Multi-platform creative adaptation
- Creative quality assessment

## Input Requirements

### Campaign Planning Inputs

- Brand information (name, description)
- Campaign objectives
- Target audience demographics
- Geographic locations
- Psychographic traits
- Integrated ad platforms

### Creative Generation Inputs

- Brand information
- Campaign objectives
- Target audience details
- Platform-specific requirements
- Creative direction (optional)
- Industry context

## Output

### Campaign Planning Outputs

- Recommended ad platforms
- Campaign schedule
- Budget allocation
- Campaign naming
- Target audience segments

### Creative Generation Outputs

- Generated campaign images
- Optimized text overlays
- Platform-specific creatives
- Call-to-action elements
- Creative quality metrics

## Installation

1. Install `uv` in the system (if not already installed)

2. Clone the repository:
```bash
git clone <repository-url>
cd nyx-campaign-agent
```

3. Create and activate the virtual environment:
```bash
uv sync
source .venv/bin/activate
```

4. Install dependencies:
```bash
uv pip install -r requirements.txt
```

5. Install ODBC Driver for SQL Server:

For macOS:
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18 mssql-tools18
```

For Ubuntu/Debian:
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/$(lsb_release -rs)/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18
```

For Windows:
- Download the Microsoft ODBC Driver 18 for SQL Server from the [Microsoft Download Center](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
- Run the downloaded installer and follow the installation wizard

## Usage

1. Start the FastAPI server:
```bash
python3 main.py
```

The server will start and be available at:
- API Documentation: http://localhost:8000/docs
- ReDoc Documentation: http://localhost:8000/redoc

2. The server will automatically reload when you make changes to the code.

## Environment Variables

Make sure to set up the following environment variables:
- `LOG_LEVEL`: Set to "DEBUG" for development or "INFO" for production
- `PGSQL_HOST`: PostgreSQL host
- `PGSQL_DATABASE_NAME`: PostgreSQL database name
- `PGSQL_USERNAME`: PostgreSQL username
- `PGSQL_PASSWORD`: PostgreSQL password
- `STORAGE_PROVIDER`: Set to either "GCP" or "AZURE"
- For GCP:
  - `GCP_TYPE`
  - `GCP_PROJECT_ID`
  - `GCP_PRI_KEY_ID`
  - `GCP_PRI_KEY`
  - `GCP_CLIENT_EMAIL`
  - `GCP_CLIENT_ID`
  - `GCP_AUTH_URI`
  - `GCP_TOKEN_URI`
  - `GCP_AUTH_PROVIDER`
  - `GCP_CLIENT_CERT_URL`
  - `GCP_UNIVERSE_DOMAIN`
  - `BRAND_GCP_BUCKET_NAME`
- For Azure:
  - `AZURE_STORAGE_CONNECTION_STRING`
  - `AZURE_CONTAINER_NAME`
  - `AZURE_STORAGE_ACCOUNT`
  - `AZURE_STORAGE_KEY`

## API Endpoints

### Campaign Planning Endpoints

- `POST /request_campaign_plan`: Submit a new campaign planning request
- `GET /status_campaign_plan/{request_id}`: Check campaign planning status
- `GET /get_campaign_plan/{request_id}`: Get campaign planning results

### Creative Generation Endpoints

- `POST /request_creative_plan`: Submit a new creative generation request
- `GET /status_creative_plan/{request_id}`: Check creative generation status
- `GET /get_creative_plan/{request_id}`: Get creative generation results

## Dependencies

- Python 3.12
- FastAPI
- Pydantic
- LangChain
- OpenAI GPT-4
- Image generation and processing libraries
- PostgreSQL (for state management)
- Uvicorn (ASGI server)
