from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Workflow",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("default_executor", models.CharField(choices=[("local", "Local Executor"), ("celery", "Celery Executor")], default="local", max_length=32)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="WorkflowNode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("ref", models.SlugField(max_length=255)),
                ("kind", models.CharField(choices=[("task", "Task"), ("human", "Human Gate"), ("branch", "Branch")], default="task", max_length=32)),
                ("callable_path", models.CharField(blank=True, help_text="Python path to invoke for this node. Required for task nodes.", max_length=512)),
                ("executor", models.CharField(blank=True, choices=[("local", "Local Executor"), ("celery", "Celery Executor")], max_length=32, null=True)),
                ("allow_parallel", models.BooleanField(default=False)),
                ("order", models.PositiveIntegerField(default=0)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="nodes", to="workflows.workflow")),
            ],
            options={
                "ordering": ["workflow_id", "order", "id"],
                "unique_together": {("workflow", "ref")},
            },
        ),
        migrations.CreateModel(
            name="WorkflowRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("paused", "Paused"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=32)),
                ("context", models.JSONField(blank=True, default=dict)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("executor", models.CharField(choices=[("local", "Local Executor"), ("celery", "Celery Executor")], default="local", max_length=32)),
                ("pause_reason", models.CharField(blank=True, max_length=255)),
                ("current_node", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="workflows.workflownode")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="runs", to="workflows.workflow")),
            ],
            options={
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="WorkflowEdge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("condition", models.CharField(blank=True, help_text="Optional condition name to evaluate for branching.", max_length=255)),
                ("from_node", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="outgoing_edges", to="workflows.workflownode")),
                ("to_node", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="incoming_edges", to="workflows.workflownode")),
                ("workflow", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="edges", to="workflows.workflow")),
            ],
            options={
                "unique_together": {("workflow", "from_node", "to_node", "condition")},
            },
        ),
        migrations.CreateModel(
            name="NodeRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("running", "Running"), ("paused", "Paused"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=32)),
                ("output", models.JSONField(blank=True, default=dict)),
                ("error", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
                ("executor", models.CharField(choices=[("local", "Local Executor"), ("celery", "Celery Executor")], default="local", max_length=32)),
                ("node", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="runs", to="workflows.workflownode")),
                ("run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="node_runs", to="workflows.workflowrun")),
            ],
            options={
                "ordering": ["started_at"],
            },
        ),
        migrations.CreateModel(
            name="NodeParameter",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("key", models.CharField(max_length=255)),
                ("value", models.JSONField(blank=True, default=dict)),
                ("required", models.BooleanField(default=False)),
                ("description", models.TextField(blank=True)),
                ("node", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="parameters", to="workflows.workflownode")),
            ],
            options={
                "ordering": ["node_id", "id"],
                "unique_together": {("node", "key")},
            },
        ),
    ]
