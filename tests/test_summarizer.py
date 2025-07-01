import pytest
import asyncio
import json
from tests.fixtures import (summarizer,client,
                            task_id,
                            system_prompt,primary_prompt,secondary_reduction_prompt,final_reduction_prompt,
                            paragraphs,
                            secondary_summaries,
                            task_manager)


class TestSummarizer:
    """This will test the individual modules in order as called by API"""

    @pytest.mark.asyncio
    async def test_create_chunks(self,summarizer,paragraphs):
        primary_chunks, primary_count, secondary_count = summarizer.create_chunks(paragraphs)
        assert primary_chunks[0] == paragraphs
        assert primary_count == 1
        assert secondary_count == 1
        self.primary_count = primary_count
        self.primary_chunks = primary_chunks

    
    @pytest.mark.asyncio
    async def test_process_primary_chunk(self,summarizer,paragraphs,task_id,system_prompt,primary_prompt):
        primary_tasks = [summarizer.process_primary_chunk(task_id, idx, chunk, 1,system_prompt,primary_prompt)
                    for idx, chunk in enumerate([paragraphs])]
        primary_summaries = await asyncio.gather(*primary_tasks)
        assert isinstance(primary_summaries, list)
        assert isinstance(primary_summaries[0], str)
    
    @pytest.mark.asyncio
    async def test_process_secondary_chunk(self, summarizer, paragraphs,task_id,system_prompt,secondary_reduction_prompt):
        chunk_size = 3  # Number of primary summaries to combine
        primary_summaries = paragraphs
        secondary_chunks = [
            primary_summaries[i:i + chunk_size]
            for i in range(0, len(primary_summaries), chunk_size)
        ]
        
        secondary_tasks = [
            summarizer.process_secondary_chunk(task_id, idx, chunk, len(secondary_chunks),system_prompt, secondary_reduction_prompt)
            for idx, chunk in enumerate(secondary_chunks)
        ]
        secondary_summaries = await asyncio.gather(*secondary_tasks)

        assert isinstance(secondary_summaries, list)
        assert isinstance(secondary_summaries[0], str)

    @pytest.mark.asyncio
    async def test_generate_final_summary(self,task_id, summarizer, secondary_summaries, system_prompt, final_reduction_prompt):
        full_summary = []
        async for token in summarizer.generate_final_summary(task_id, secondary_summaries,system_prompt,final_reduction_prompt):
            full_summary.append(token)
            assert isinstance(token, str)
        assert len(full_summary) > 50
