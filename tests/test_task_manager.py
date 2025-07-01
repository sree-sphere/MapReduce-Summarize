import pytest
import asyncio
import json
from tests.fixtures import (task_id,
                            task_manager)

class TestTaskManager:
    """This will test the async queue management functionality implemented"""
    
    @pytest.mark.asyncio
    async def test_create_subscriber(self, task_manager, task_id):
        queue = await task_manager.create_subscriber(task_id)
        assert queue in task_manager.tasks[task_id]['subscribers']
        assert isinstance(queue, asyncio.Queue)
    
    @pytest.mark.asyncio
    async def test_remove_subscriber(self, task_manager,task_id):
        queue = await task_manager.create_subscriber(task_id)
        await task_manager.remove_subscriber(task_id, queue)
        assert queue not in task_manager.tasks[task_id]['subscribers']
    
    @pytest.mark.asyncio
    async def test_broadcast_progress(self, task_manager,task_id):
        queue = await task_manager.create_subscriber(task_id)
        event_type = "update"
        data = {"progress": 50}
        await task_manager.broadcast_progress(task_id, event_type, data)
        event = await queue.get()
        assert event == {'type': event_type, **data}
    
    def test_cleanup_task(self, task_manager, task_id):
        task_manager.cleanup_task(task_id)
        assert task_id not in task_manager.tasks
    
    @pytest.mark.asyncio
    async def test_remove_subscriber_nonexistent_task(self,task_manager, task_id):
        queue = asyncio.Queue()
        await task_manager.remove_subscriber(task_id, queue)
        # Ensure no exceptions are raised even if task_id doesn't exist
