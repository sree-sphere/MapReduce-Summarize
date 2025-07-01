import os
from src.models import SummaryRequestModel
from src.log import logger
from typing import List, Dict, Optional, AsyncGenerator, Tuple
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import Field
import asyncio
import json
from collections import defaultdict
import uuid
from collections import defaultdict
import uuid
from openai import AsyncOpenAI,OpenAIError
from dotenv import load_dotenv
from dataclasses import dataclass
from dataclasses import dataclass
from datetime import datetime
import time
from monitoring.otel import tracer

load_dotenv()

@dataclass
class SummaryConfig:
    primary_chunk_size: int = 10
    secondary_chunk_size: int = 10
    max_parallel_requests: int = 10
    model: str = os.getenv('LLM_MODEL')
    temperature: float = 0.3
    max_tokens_per_request: int = 800

class TaskManager:
    def __init__(self):
        self.tasks = defaultdict(lambda: {
            'primary_progress': 0,
            'secondary_progress': 0,
            'primary_chunks': [],
            'secondary_chunks': [],
            'subscribers': set()
        })

    async def create_subscriber(self, task_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.tasks[task_id]['subscribers'].add(queue)
        return queue

    async def remove_subscriber(self, task_id: str, queue: asyncio.Queue):
        if task_id in self.tasks:
            self.tasks[task_id]['subscribers'].discard(queue)

    async def broadcast_progress(self, task_id: str, event_type: str, data: Dict):
        event = {'type': event_type, **data}
        for queue in self.tasks[task_id]['subscribers']:
            await queue.put(event)

    def cleanup_task(self, task_id: str):
        if task_id in self.tasks:
            del self.tasks[task_id]


class Summarizer:
    def __init__(self, api_key: str, config: Optional[SummaryConfig] = None):
        self.client = AsyncOpenAI(api_key=api_key,
                                  base_url=os.getenv("BASE_URL")
                                  )
        self.config = config or SummaryConfig()
        self.task_manager = TaskManager()

    def create_chunks(self, paragraphs: List[str]) -> Tuple[List[List[str]], int, int]:
        # Create primary chunks
        primary_chunks = [
            paragraphs[i:i + self.config.primary_chunk_size]
            for i in range(0, len(paragraphs), self.config.primary_chunk_size)
        ]
        
        # Create secondary chunks
        secondary_chunks = []
        for primary in primary_chunks:
            chunk_group = [
                primary[i:i + self.config.secondary_chunk_size]
                for i in range(0, len(primary), self.config.secondary_chunk_size)
            ]
            secondary_chunks.extend(chunk_group)
            
        return primary_chunks, len(primary_chunks), len(secondary_chunks)

    async def process_chunk(self, system_prompt: str, 
                          user_prompt: str) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens_per_request,
                stream=False
            )
            return response.choices[0].message.content
                
        except OpenAIError as e:
            raise HTTPException(503, detail=f"LLM unavailable.\n{e}")
        except Exception as e:
            logger.error(f"Error processing chunk: {str(e)}")
            return ""

    async def process_primary_chunk(self, task_id: str, chunk_idx: int, 
                                  chunks: List[str], total_chunks: int,
                                  system_prompt:str,
                                  primary_prompt:str) -> str:
        
        content = "\n\n".join(chunks)
        user_prompt = primary_prompt + f"\n\nContent:\n{content}"
        
        summary = await self.process_chunk(system_prompt, user_prompt)
        progress = int(((chunk_idx + 1) / total_chunks) * 100)
        
        await self.task_manager.broadcast_progress(task_id, "primary_progress", {
            "progress": progress,
            "chunk": chunk_idx + 1,
            "total": total_chunks,
            "summary": summary
        })
        
        return summary

    async def process_secondary_chunk(self, task_id: str, chunk_idx: int,
                                    chunks: List[str], total_chunks: int,
                                    system_prompt:str, secondary_reduction_prompt:str) -> str:
        
        content = "\n\n".join(chunks)
        user_prompt = secondary_reduction_prompt + f"\n\nContent:\n{content}"
        
        summary = await self.process_chunk(system_prompt, user_prompt)
        progress = int(((chunk_idx + 1) / total_chunks) * 100)
        
        await self.task_manager.broadcast_progress(task_id, "secondary_progress", {
            "progress": progress,
            "chunk": chunk_idx + 1,
            "total": total_chunks,
            "summary": summary
        })
        
        return summary

    async def generate_final_summary(self, task_id: str, summaries: List[str],
                                    system_prompt:str, final_reduction_prompt:str
                                    ) -> AsyncGenerator[str, None]:
        
        content = "\n\n".join(summaries)
        user_prompt = final_reduction_prompt + f"\n\nContent:\n{content}"
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens_per_request,
                stream=True
            )
            
            async for chunk in response:
                if chunk.choices[0].delta.content:
                    token = chunk.choices[0].delta.content
                    await self.task_manager.broadcast_progress(task_id, "final_summary", {
                        "token": token
                    })
                    yield token
        except Exception as e:
            raise HTTPException(503, detail=f"LLM error in generating final summary .{e}")

    async def process_text(self, task_id: str, paragraphs: List[str],
                           system_prompt:str, primary_prompt:str, secondary_reduction_prompt:str, final_reduction_prompt:str
                           ) -> None:
        try:
            # Create chunks
            primary_chunks, primary_count, *_ = self.create_chunks(paragraphs)
            logger.info(f"Primary count: {primary_count}")
            if primary_count>1:
                # Process primary chunks
                primary_tasks = [
                    self.process_primary_chunk(task_id, idx, chunk, primary_count,system_prompt,primary_prompt)
                    for idx, chunk in enumerate(primary_chunks)
                ]
                with tracer.start_as_current_span("primary_summarization"):
                    primary_summaries = await asyncio.gather(*primary_tasks)
            else:
                primary_summaries = primary_chunks[0]
                logger.info(f"Skipping to secondary processing as initial chunk size is {len(primary_chunks)}.......")

            # Process secondary chunks
            chunk_size = 3  # Number of primary summaries to combine
            secondary_chunks = [
                primary_summaries[i:i + chunk_size]
                for i in range(0, len(primary_summaries), chunk_size)
            ]
            
            secondary_tasks = [
                self.process_secondary_chunk(task_id, idx, chunk, len(secondary_chunks),system_prompt, secondary_reduction_prompt)
                for idx, chunk in enumerate(secondary_chunks)
            ]
            with tracer.start_as_current_span("secondary_summarization"):
                secondary_summaries = await asyncio.gather(*secondary_tasks)
            
            # Generate final summary
            await self.task_manager.broadcast_progress(task_id, "status", {
                "message": "Generating final summary..."
            })
            
            with tracer.start_as_current_span("final_summarization"):
                async for _ in self.generate_final_summary(task_id, secondary_summaries,system_prompt,final_reduction_prompt):
                    # generate final summary
                    pass
                
            await self.task_manager.broadcast_progress(task_id, "completed", {
                "message": "Summary generation completed"
            })
        except Exception as e:
            await self.task_manager.broadcast_progress(task_id, "error", {
                "message": str(e)
            })
            raise




new_router = APIRouter()

def get_working_prompts(input_prompt_field: Optional[str], prompt_type:str)->str:
    """Helper function to initialise default prompts in case of no input"""
    if not input_prompt_field:
        with open(os.path.join("prompt_templates",f"{prompt_type}.txt"), "r") as f:
            prompt = f.read()
            logger.info(f"No {prompt_type} provided. Proceeding with default prompt")
    else:
        prompt = input_prompt_field
    
    return prompt


async def get_full_text(event_generator):
    full_summary = []
    start_time = time.time()
    async for line in event_generator():
        if line.startswith('data: '):
            event_data = json.loads(line[6:])
            if event_data['type'] in ['final_summary']:
                full_summary.append(event_data['token'])
            elif event_data['type']=='error':
                full_summary.append(event_data['message'])
    full_summary = ''.join(full_summary)
    status_code = 200
    if event_data['type'] == 'error':
        status_code = 500
    
    total_time = time.time() - start_time
    return full_summary,total_time, status_code


# Update the /summarize endpoint
@new_router.post("/summarize")
async def create_summary(request: SummaryRequestModel):
    task_id = str(uuid.uuid4())
    with tracer.start_as_current_span("summarize") as start_trace:

        primary_prompt = get_working_prompts(request.primary_prompt, "primary_prompt")
        secondary_reduction_prompt = get_working_prompts(request.secondary_reduction_prompt, "secondary_reduction_prompt")
        final_reduction_prompt = get_working_prompts(request.final_reduction_prompt, "final_reduction_prompt")
        system_prompt = get_working_prompts(request.system_prompt, "system_prompt")
        logger.info(f"primary_chunk_size: {request.primary_chunk_size}")
        logger.info(f"secondary_chunk_size: {request.secondary_chunk_size}")
        logger.info(f"max_parallel_requests: {request.max_parallel_requests}")
        logger.info(f"temperature: {request.temperature}")
        logger.info(f"max_tokens_per_request: {request.max_tokens_per_request}")
        
        try:
            summarizer = Summarizer(
                os.getenv("OPENAI_API_KEY"),
                SummaryConfig(
                    model = os.getenv('LLM_MODEL'),
                    primary_chunk_size = request.primary_chunk_size,
                    secondary_chunk_size = request.secondary_chunk_size,
                    max_parallel_requests= request.max_parallel_requests,
                    temperature= request.temperature,
                    max_tokens_per_request = request.max_tokens_per_request
                )

            )
        except OpenAIError as e:
            raise HTTPException(status_code=503, detail=f"Error in initialising the LLM model\n{e}")
        
        async def event_generator():
            start_trace.add_event(f"Created subscriber with task_id: {task_id}", timestamp=int(time.time()))
            queue = await summarizer.task_manager.create_subscriber(task_id)
            try:
                # Start processing in background
                start_trace.add_event("Started Summarization process in background", timestamp=int(time.time()))
                process_task = asyncio.create_task(
                    summarizer.process_text(task_id,
                                            request.paragraphs,
                                            system_prompt,
                                            primary_prompt,
                                            secondary_reduction_prompt,
                                            final_reduction_prompt)
                )
                while True:
                    event = await queue.get()
                    if event['type'] in ['error','completed']:
                        yield f"data: {json.dumps(event)}\n\n"
                        break
                    else:
                        yield f"data: {json.dumps(event)}\n\n"
                        
                await process_task
            except asyncio.CancelledError:
                raise HTTPException(status_code=503, detail="Task was cancelled.")
            except HTTPException as e:
                raise e
            except Exception as e:
                print("EXCEPTION")
                raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
            finally:
                await summarizer.task_manager.remove_subscriber(task_id, queue)
                summarizer.task_manager.cleanup_task(task_id)
        
        if request.stream:
            return StreamingResponse(
                event_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Content-Type": "text/event-stream"
                }
            )
        else:  
            full_summary,total_time,status_code = await get_full_text(event_generator)
            return JSONResponse(content= {'summary' : full_summary,
                                        'time_taken (sec)' : total_time},
                                status_code= status_code,
                                media_type="text/event-stream")