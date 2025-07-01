from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Dict
import os

from src.log import logger
from src.executor import new_router
from monitoring.otel import tracer


# Metadata for Swagger documentation
tags_metadata = [
    {
        "name": "Summary",
        "description": "These APIs trigger summarization tasks in asynchronous mode.",
    },
]

# Versioned app
app_v1 = FastAPI(openapi_tags=tags_metadata,
                title="Streaming Summary Generator")

app = FastAPI()
app.mount("/summarizer/v1",app_v1)


origins = ["*"]
app_v1.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


LOG_FOLDER = "logs"
os.makedirs(LOG_FOLDER, exist_ok=True)

# Helper function to log
def log_error(data, error):
    logger.error(f"Error: {error}, Data: {data}")

invalid_dtype = "Invalid data type, expected a dictionary"

# Global Exception Handler for Request Validation Errors
@app_v1.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Log the validation error
    logger.error(f"Validation error: {exc}")
    log_error({"request_body": await request.body()}, exc)
    
    # Return a custom error response
    return JSONResponse(
        status_code=422,
        content={"message": "Invalid input format", "details": exc.errors()},
    )

# Exception: HTTP exceptions
@app_v1.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )
    
# Attach router for summarization tasks
app_v1.include_router(new_router, tags=['Summary'])