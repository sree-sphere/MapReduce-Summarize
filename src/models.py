from pydantic import Field, BaseModel,field_validator
from typing import Optional, List, Literal
from fastapi.exceptions import RequestValidationError
from src.log import logger

class SummaryRequestModel(BaseModel):

    paragraphs: List[str] = Field(
        min_length=1,
        max_length=400,
        description="List of paragraphs to summarize"
    )
    primary_prompt: Optional[str] = Field(
        min_length=10,
        description="Primary instructions for base level summary generation",
        default=None
    )
    secondary_reduction_prompt: Optional[str] = Field(
        min_length=10,
        description="Secondary reduction instructions for summary generation based on primary summary",
        default=None
    )
    final_reduction_prompt: Optional[str] = Field(
        min_length=10,
        description="Final reduction instructions for summary generation based on secondary summary",
        default=None
    )
    system_prompt: Optional[str] = Field(
        min_length=10,
        description="Custom instructions for summary generation",
        default=None
    )
    primary_chunk_size: Optional[int] = 15
    secondary_chunk_size: Optional[int] = 10    # paragraphs per secondary chunk
    max_parallel_requests: Optional[int] = 10   # concurrent API requests
    temperature: Optional[float] = 0.3
    max_tokens_per_request: Optional[int] = 700
    stream: Optional[bool] = False
    # @validator('paragraphs') # deprecated in pydantic v2
    @field_validator('paragraphs')
    def validate_paragraphs(cls, v):
        if not all(isinstance(p, str) and p.strip() for p in v):
            raise RequestValidationError([{'msg':"All paragraph elements must be non-empty strings"}])
        return v

# Input data model is in JSON
class LinkData(BaseModel):
    json_data: dict  # Input JSON with links