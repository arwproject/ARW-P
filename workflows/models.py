from django.db import models


class ExecutorChoices(models.TextChoices):
    LOCAL = "local", "Local Executor"
    CELERY = "celery", "Celery Executor"


class Workflow(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    default_executor = models.CharField(
        max_length=32, choices=ExecutorChoices.choices, default=ExecutorChoices.LOCAL
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class WorkflowNode(models.Model):
    TASK = "task"
    HUMAN = "human"
    BRANCH = "branch"
    NODE_KIND_CHOICES = [
        (TASK, "Task"),
        (HUMAN, "Human Gate"),
        (BRANCH, "Branch"),
    ]

    workflow = models.ForeignKey(Workflow, related_name="nodes", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    ref = models.SlugField(max_length=255)
    kind = models.CharField(max_length=32, choices=NODE_KIND_CHOICES, default=TASK)
    callable_path = models.CharField(
        max_length=512,
        help_text="Python path to invoke for this node. Required for task nodes.",
        blank=True,
    )
    executor = models.CharField(
        max_length=32, choices=ExecutorChoices.choices, null=True, blank=True
    )
    allow_parallel = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ("workflow", "ref")
        ordering = ["workflow_id", "order", "id"]

    def __str__(self) -> str:
        return f"{self.workflow.name}:{self.ref}"


class NodeParameter(models.Model):
    node = models.ForeignKey(WorkflowNode, related_name="parameters", on_delete=models.CASCADE)
    key = models.CharField(max_length=255)
    value = models.JSONField(default=dict, blank=True)
    required = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        unique_together = ("node", "key")
        ordering = ["node_id", "id"]

    def __str__(self) -> str:
        return f"{self.node.ref}:{self.key}"


class WorkflowEdge(models.Model):
    workflow = models.ForeignKey(Workflow, related_name="edges", on_delete=models.CASCADE)
    from_node = models.ForeignKey(
        WorkflowNode, related_name="outgoing_edges", on_delete=models.CASCADE
    )
    to_node = models.ForeignKey(
        WorkflowNode, related_name="incoming_edges", on_delete=models.CASCADE
    )
    condition = models.CharField(
        max_length=255,
        blank=True,
        help_text="Optional condition name to evaluate for branching.",
    )

    class Meta:
        unique_together = ("workflow", "from_node", "to_node", "condition")

    def __str__(self) -> str:
        return f"{self.from_node.ref} -> {self.to_node.ref}"


class RunStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    RUNNING = "running", "Running"
    PAUSED = "paused", "Paused"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class WorkflowRun(models.Model):
    workflow = models.ForeignKey(Workflow, related_name="runs", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=32, choices=RunStatus.choices, default=RunStatus.PENDING
    )
    context = models.JSONField(default=dict, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    current_node = models.ForeignKey(
        WorkflowNode, null=True, blank=True, on_delete=models.SET_NULL
    )
    executor = models.CharField(
        max_length=32, choices=ExecutorChoices.choices, default=ExecutorChoices.LOCAL
    )
    pause_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self) -> str:
        return f"Run {self.id} of {self.workflow.name}"


class NodeRun(models.Model):
    run = models.ForeignKey(WorkflowRun, related_name="node_runs", on_delete=models.CASCADE)
    node = models.ForeignKey(WorkflowNode, related_name="runs", on_delete=models.CASCADE)
    status = models.CharField(
        max_length=32, choices=RunStatus.choices, default=RunStatus.PENDING
    )
    output = models.JSONField(default=dict, blank=True)
    error = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    executor = models.CharField(
        max_length=32, choices=ExecutorChoices.choices, default=ExecutorChoices.LOCAL
    )

    class Meta:
        ordering = ["started_at"]

    def __str__(self) -> str:
        return f"NodeRun {self.id} for {self.node.ref}"
