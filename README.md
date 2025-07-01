# MapReduce-Style Text Summarizer

## Overview
A FastAPI-based text summarization service that implements a MapReduce-style approach for efficient processing of large documents. Inspired by the research paper "Efficient Text Summarization with MapReduce".

## Key Features
- **Hierarchical summarization**: Two-stage processing (primary and secondary chunks) for efficient handling of large texts
- **Real-time progress tracking**: SSE (Server-Sent Events) for streaming progress updates
- **Customizable prompts**: Supports custom system and reduction prompts at each stage
- **Parallel processing**: Configurable chunk sizes and parallel request limits
- **Observability**: OpenTelemetry integration for distributed tracing

### Key Files

- **Dockerfile**: Defines the container image build.
- **monitoring/otel.py**: Sets up OpenTelemetry tracing and metrics.
- **prompt\_templates/**: Contains `.txt` files for different prompt stages:

  1. `system_prompt.txt` – Base system instructions.
  2. `primary_prompt.txt` – Initial summarization instructions.
  3. `secondary_reduction_prompt.txt` – Intermediate reduction instructions.
  4. `final_reduction_prompt.txt` – Final refinement instructions.
- **src/endpoints.py**: FastAPI routes for starting the summarization pipeline and retrieving status.
- **src/executor.py**: Core logic orchestrating streaming interactions with the LLM.
- **src/log.py**: Logger configuration and helper functions.
- **src/models.py**: Pydantic models for request/response validation.

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-org/your-repo.git
   cd your-repo
   ```

2. Create & activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

- **Environment Variables**:

```bash
OPENAI_API_KEY=your_openai_key
BASE_URL=your_openai_api_base_url
LLM_MODEL=your_preferred_model
OTEL_EXPORTER=your_otel_endpoint  # Optional for tracing
APP_NAME=summarizer  # Optional service name for tracing
```

## Running Locally

```bash
uvicorn src.endpoints:app --reload
```

## Docker Usage

Build the image:

```bash
docker build -t summarizer .
```

Run a container:

```bash
docker run -p 8009:8009 \
  -e OPENAI_API_KEY=api_key \
  -e BASE_URL=openai_base_url \
  -e LLM_MODEL=model_name \
  summarizer
```
(Other variables like OTEL_EXPORTER are optional)

or with ```.env``` file

```bash
docker run -p 8009:8009 --env-file .env summarizer
```

## Payload Example

```json
{
  "paragraphs": ["text paragraph 1", "text paragraph 2"],
  "primary_prompt": "Summarize this text focusing on key points:",
  "secondary_reduction_prompt": "Combine these summaries preserving important information:",
  "final_reduction_prompt": "Create a concise final summary:",
  "system_prompt": "You are a helpful AI assistant that summarizes text.",
  "stream": true
}
```