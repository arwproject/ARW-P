from django.test import TestCase, override_settings

from workflows.execution import ExecutionService
from workflows.models import (
    ExecutorChoices,
    NodeParameter,
    RunStatus,
    Workflow,
    WorkflowEdge,
    WorkflowNode,
)


class ExecutionServiceTests(TestCase):
    def setUp(self) -> None:
        self.workflow = Workflow.objects.create(
            name="demo",
            description="Demo workflow",
            default_executor=ExecutorChoices.LOCAL,
        )
        self.echo = WorkflowNode.objects.create(
            workflow=self.workflow,
            name="Echo",
            ref="echo",
            kind=WorkflowNode.TASK,
            callable_path="workflows.sample_tasks.echo",
            order=1,
        )
        NodeParameter.objects.create(node=self.echo, key="message", value="hello")
        self.approval = WorkflowNode.objects.create(
            workflow=self.workflow,
            name="Approval",
            ref="approval",
            kind=WorkflowNode.HUMAN,
            order=2,
        )
        self.addition = WorkflowNode.objects.create(
            workflow=self.workflow,
            name="Add",
            ref="add",
            kind=WorkflowNode.TASK,
            callable_path="workflows.sample_tasks.add",
            order=3,
        )
        NodeParameter.objects.create(node=self.addition, key="a", value=1)
        NodeParameter.objects.create(node=self.addition, key="b", value={"from_context": "sum"})
        WorkflowEdge.objects.create(workflow=self.workflow, from_node=self.echo, to_node=self.approval)
        WorkflowEdge.objects.create(workflow=self.workflow, from_node=self.approval, to_node=self.addition)

    def test_run_pauses_on_human_node(self):
        service = ExecutionService()
        run = service.start_workflow(self.workflow, context={"sum": 1})

        self.assertEqual(run.status, RunStatus.PAUSED)
        self.assertEqual(run.pause_reason, "Awaiting human input")
        self.assertEqual(run.current_node, self.approval)
        self.assertIn("message", run.context)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True)
    def test_resume_completes_remaining_nodes(self):
        service = ExecutionService()
        run = service.start_workflow(self.workflow, context={"sum": 2})
        resumed = service.resume_run(run, context_update={"sum": 3})

        self.assertEqual(resumed.status, RunStatus.COMPLETED)
        self.assertEqual(resumed.context.get("sum"), 4)
        self.assertIsNone(resumed.current_node)
