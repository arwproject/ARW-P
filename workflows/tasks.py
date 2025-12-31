from celery import shared_task

from .execution import ExecutionService


@shared_task
def execute_node_task(node_run_id: int, context: dict) -> int:
    service = ExecutionService()
    run = service.complete_async_node(node_run_id=node_run_id, context=context)
    return run.id
