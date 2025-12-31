from dataclasses import dataclass, field
from typing import Dict, Optional

from django.conf import settings
from django.utils import timezone

from .models import ExecutorChoices, NodeRun, RunStatus, WorkflowNode
from .runners import NodeRunner


@dataclass
class ExecutionResult:
    output: Dict
    pending: bool = False
    paused: bool = False
    metadata: Dict = field(default_factory=dict)


class BaseExecutor:
    name = "base"

    def execute(self, node: WorkflowNode, node_run: NodeRun, context: Dict) -> ExecutionResult:
        raise NotImplementedError


class LocalExecutor(BaseExecutor):
    name = ExecutorChoices.LOCAL

    def execute(self, node: WorkflowNode, node_run: NodeRun, context: Dict) -> ExecutionResult:
        runner = NodeRunner()
        output = runner.run(node=node, context=context)
        node_run.output = output
        node_run.status = RunStatus.COMPLETED
        node_run.finished_at = timezone.now()
        node_run.save(update_fields=["output", "status", "finished_at"])
        return ExecutionResult(output=output or {})


class CeleryExecutor(BaseExecutor):
    name = ExecutorChoices.CELERY

    def execute(self, node: WorkflowNode, node_run: NodeRun, context: Dict) -> ExecutionResult:
        if settings.CELERY_TASK_ALWAYS_EAGER:
            local_executor = LocalExecutor()
            return local_executor.execute(node=node, node_run=node_run, context=context)

        from .tasks import execute_node_task

        async_result = execute_node_task.delay(node_run.id, context)
        node_run.status = RunStatus.RUNNING
        node_run.output = {"task_id": async_result.id}
        node_run.save(update_fields=["status", "output"])
        return ExecutionResult(output=node_run.output, pending=True, metadata={"task_id": async_result.id})


class ExecutorRegistry:
    def __init__(self):
        self._executors = {
            ExecutorChoices.LOCAL: LocalExecutor(),
            ExecutorChoices.CELERY: CeleryExecutor(),
        }

    def get_executor(self, name: Optional[str]) -> BaseExecutor:
        key = name or ExecutorChoices.LOCAL
        executor = self._executors.get(key)
        if executor is None:
            return self._executors[ExecutorChoices.LOCAL]
        return executor
