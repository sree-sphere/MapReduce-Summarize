import pytest
from unittest.mock import patch, MagicMock
from src.executor import Summarizer, SummaryConfig
from openai import OpenAIError
import os
import json
from fastapi.exceptions import HTTPException
from tests.fixtures import client,paragraphs
from requests.exceptions import ChunkedEncodingError

class TestLLMException:

    @patch.dict('os.environ', {}, clear=True)
    @patch('src.executor.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_openai_failure(self,mock_openai, client, paragraphs):
        mock_openai.return_value.chat.completions.create.side_effect = OpenAIError("Simulated OpenAIError")
        kwargs = {
            'paragraphs' : paragraphs,
            'stream' : False
            }
        response = client.post(url='/summarizer/v1/summarize', content=json.dumps(kwargs) )
        json_response = response.json()

        assert response.status_code == 503
        assert 'LLM unavailable' in json_response['message']
    

    @patch.dict('os.environ', {}, clear=True)
    @patch('src.executor.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_llm_code_failure(self,mock_openai, client, paragraphs):
        mock_openai.return_value.chat.completions.create.side_effect = Exception("Error processing chunk")
        kwargs = {
            'paragraphs' : paragraphs,
            'stream' : False
            }
        response = client.post(url='/summarizer/v1/summarize', content=json.dumps(kwargs) )
        json_response = response.json()

        assert response.status_code == 503
        assert 'Error processing chunk' in json_response['message']
    

    @patch.dict('os.environ', {}, clear=True)
    @patch('src.executor.AsyncOpenAI')
    @pytest.mark.asyncio
    async def test_streaming_api_output(self, mock_openai, client, paragraphs):
        kwargs = {
            'paragraphs' : paragraphs,
            'stream' : True
            }
        mock_openai.return_value.chat.completions.create.side_effect = Exception("Error processing chunk")
        with pytest.raises(ExceptionGroup):
            client.post(url='/summarizer/v1/summarize', content=json.dumps(kwargs) )