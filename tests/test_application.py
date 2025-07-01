import pytest
import asyncio
import json
from tests.fixtures import (summarizer,client,
                            task_id,
                            system_prompt,primary_prompt,secondary_reduction_prompt,final_reduction_prompt,
                            paragraphs,
                            secondary_summaries,
                            task_manager)


class TestApplication:
    """This will test the whole application via API endpoint"""
    
    def test_api_input_validation(self, client, paragraphs):
        kwargs = {
            'paragraphs' : paragraphs[0],   # passing as str format
            }
        response = client.post(url='/summarizer/v1/summarize', content=json.dumps(kwargs))
        res = response.json()
        assert response.status_code == 422
        assert res['details'][0]['msg'] == "Input should be a valid list"

        kwargs = {
            'paragraphs' : [""],   # empty string
            }
        response = client.post(url='/summarizer/v1/summarize', content=json.dumps(kwargs))
        res = response.json()
        assert response.status_code == 422
        assert res['details'][0]['msg'].startswith("All paragraph elements must be non-empty strings")    
    

    def test_streaming_api_output(self, client, paragraphs):
        kwargs = {
            'paragraphs' : paragraphs,
            'stream' : True
            }
        response = client.post(url='/summarizer/v1/summarize', content=json.dumps(kwargs) )
        text_response = response.text.strip()

        assert response.status_code == 200
        assert text_response.startswith('data')
        assert 'Generating final summary' in text_response
        assert 'progress' in text_response
        assert text_response.endswith('"Summary generation completed"}')
    

    def test_static_api_output(self, client, paragraphs, system_prompt):
        kwargs = {
            'paragraphs' : paragraphs*20,
            'system_prompt' : system_prompt,
            'stream' : False
            }
        response = client.post(url='/summarizer/v1/summarize', content=json.dumps(kwargs) )
        json_response = response.json()

        assert response.status_code == 200
        assert 'summary' in json_response.keys()
        assert 'time_taken (sec)' in json_response.keys()
        assert isinstance(json_response['summary'], str)