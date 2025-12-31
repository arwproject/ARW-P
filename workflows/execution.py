from collections import deque
from typing import Dict, Iterable, List, Optional, Sequence

from django.utils import timezone

from .executors import ExecutionResult, ExecutorRegistry
from .models import (
    ExecutorChoices,
    NodeRun,
    RunStatus,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
    WorkflowRun,
)
from .runners import NodeRunner


class ExecutionService:
    def __init__(self, executor_registry: Optional[ExecutorRegistry] = None):
        self.executor_registry = executor_registry or ExecutorRegistry()
        self.runner = NodeRunner()

    def start_workflow(
        self,
        workflow: Workflow,
        context: Optional[Dict] = None,
        executor: Optional[str] = None,
    ) -> WorkflowRun:
        run = WorkflowRun.objects.create(
            workflow=workflow,
            status=RunStatus.RUNNING,
            context=context or {},
            executor=executor or workflow.default_executor,
        )
        initial_nodes = self._entry_nodes(workflow)
        self._execute_queue(run=run, nodes=initial_nodes)
        return run

    def resume_run(self, run: WorkflowRun, context_update: Optional[Dict] = None) -> WorkflowRun:
        if run.status not in {RunStatus.PAUSED, RunStatus.PENDING, RunStatus.RUNNING}:
            return run

        updated_context = dict(run.context)
        if context_update:
            updated_context.update(context_update)
        run.context = updated_context
        run.status = RunStatus.RUNNING
        run.pause_reason = ""
        run.save(update_fields=["context", "status", "pause_reason"])

        start_nodes: Sequence[WorkflowNode]
        if run.current_node:
            start_nodes = self._next_nodes(run.current_node, run.context)
        else:
            start_nodes = self._entry_nodes(run.workflow)

        self._execute_queue(run=run, nodes=start_nodes)
        return run

    def pause_run(self, run: WorkflowRun, reason: str = "") -> WorkflowRun:
        if run.status not in {RunStatus.RUNNING, RunStatus.PAUSED}:
            return run
        run.status = RunStatus.PAUSED
        run.pause_reason = reason or "Paused manually"
        run.save(update_fields=["status", "pause_reason"])
        return run

    def complete_async_node(self, node_run_id: int, context: Optional[Dict] = None) -> WorkflowRun:
        node_run = (
            NodeRun.objects.select_related("run", "node", "run__workflow")
            .prefetch_related("node__outgoing_edges", "node__incoming_edges")
            .get(pk=node_run_id)
        )
        run = node_run.run
        run_context = dict(run.context)
        if context:
            run_context.update(context)
        output = self.runner.run(node=node_run.node, context=run_context)
        node_run.output = output
        node_run.status = RunStatus.COMPLETED
        node_run.finished_at = timezone.now()
        node_run.save(update_fields=["output", "status", "finished_at"])
        self._apply_output(run=run, output=output)
        next_nodes = self._next_nodes(node_run.node, run.context)
        self._execute_queue(run=run, nodes=next_nodes)
        return run

    def _execute_queue(self, run: WorkflowRun, nodes: Iterable[WorkflowNode]) -> None:
        queue: deque[WorkflowNode] = deque(nodes)
        while queue and run.status not in {RunStatus.PAUSED, RunStatus.FAILED}:
            node = queue.popleft()
            execution_result = self._execute_node(run=run, node=node)
            if execution_result.paused or execution_result.pending:
                return
            next_nodes = self._next_nodes(node, run.context)
            queue.extend(next_nodes)

        if run.status == RunStatus.RUNNING and not queue:
            run.status = RunStatus.COMPLETED
            run.finished_at = timezone.now()
            run.current_node = None
            run.save(update_fields=["status", "finished_at", "current_node"])

    def _execute_node(self, run: WorkflowRun, node: WorkflowNode) -> ExecutionResult:
        node_run = NodeRun.objects.create(
            run=run,
            node=node,
            status=RunStatus.RUNNING,
            executor=node.executor or run.executor or ExecutorChoices.LOCAL,
        )
        run.current_node = node
        run.save(update_fields=["current_node"])

        if node.kind == WorkflowNode.HUMAN:
            node_run.status = RunStatus.PAUSED
            node_run.finished_at = timezone.now()
            node_run.save(update_fields=["status", "finished_at"])
            run.status = RunStatus.PAUSED
            run.pause_reason = "Awaiting human input"
            run.save(update_fields=["status", "pause_reason"])
            return ExecutionResult(output={}, paused=True)

        if node.kind == WorkflowNode.BRANCH:
            node_run.status = RunStatus.COMPLETED
            node_run.finished_at = timezone.now()
            node_run.save(update_fields=["status", "finished_at"])
            return ExecutionResult(output={})

        executor = self.executor_registry.get_executor(node.executor or run.executor)
        try:
            result = executor.execute(node=node, node_run=node_run, context=run.context)
        except Exception as exc:
            node_run.status = RunStatus.FAILED
            node_run.error = str(exc)
            node_run.finished_at = timezone.now()
            node_run.save(update_fields=["status", "error", "finished_at"])
            run.status = RunStatus.FAILED
            run.pause_reason = str(exc)
            run.save(update_fields=["status", "pause_reason"])
            return ExecutionResult(output={}, pending=False)

        if result.pending:
            run.status = RunStatus.RUNNING
            run.save(update_fields=["status"])
            return result

        self._apply_output(run=run, output=result.output)
        return result

    def _apply_output(self, run: WorkflowRun, output: Dict) -> None:
        if not isinstance(output, dict):
            return
        context = dict(run.context)
        context.update(output)
        run.context = context
        run.save(update_fields=["context"])

    def _entry_nodes(self, workflow: Workflow) -> List[WorkflowNode]:
        nodes_with_incoming = set(
            WorkflowEdge.objects.filter(workflow=workflow).values_list("to_node_id", flat=True)
        )
        candidates = list(workflow.nodes.exclude(id__in=nodes_with_incoming).order_by("order", "id"))
        if candidates:
            return candidates
        return list(workflow.nodes.order_by("order", "id"))

    def _next_nodes(self, node: WorkflowNode, context: Dict) -> List[WorkflowNode]:
        outgoing = WorkflowEdge.objects.filter(from_node=node)
        selected: List[WorkflowNode] = []
        for edge in outgoing:
            if not edge.condition:
                selected.append(edge.to_node)
            elif context.get(edge.condition):
                selected.append(edge.to_node)
        return selected
