# Workflow Orchestration Engine (Django)

This repository now includes a self-contained Django orchestration service that stores workflows, nodes, parameters, and run state in a database. Workflows can be executed locally or through Celery, paused for human intervention, and resumed without losing progress.

## Core concepts
- **Workflow**: A directed graph with nodes, edges, and a default executor (`local` or `celery`).
- **Node**: Supports `task`, `branch`, and `human` kinds. Task nodes call a Python function via a dotted path (e.g., `workflows.sample_tasks.echo`).
- **Parameters**: Stored per node and passed as keyword arguments into the callable. A parameter value of `{"from_context": "key"}` pulls data from the run context.
- **Edges**: Define graph flow. If `condition` is set, the engine follows the edge when `context[condition]` is truthy.
- **Runs**: Persisted in `WorkflowRun` and `NodeRun` rows with statuses (`pending`, `running`, `paused`, `completed`, `failed`).

## Running locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Celery can run eagerly (no broker) when `CELERY_TASK_ALWAYS_EAGER=true` in the environment. For real brokers, set `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.

## Creating a workflow
POST `/api/workflows/` with nodes, parameters, and edges:
```json
{
  "name": "demo",
  "description": "Echo then branch",
  "default_executor": "local",
  "nodes": [
    {
      "name": "Echo",
      "ref": "echo",
      "kind": "task",
      "callable_path": "workflows.sample_tasks.echo",
      "parameters": [{"key": "message", "value": "hello agent"}],
      "order": 1
    },
    {
      "name": "Wait",
      "ref": "approval",
      "kind": "human",
      "order": 2
    },
    {
      "name": "Add",
      "ref": "add",
      "kind": "task",
      "callable_path": "workflows.sample_tasks.add",
      "parameters": [{"key": "a", "value": 1}, {"key": "b", "value": {"from_context": "sum"}}],
      "order": 3
    }
  ],
  "edges": [
    {"from_ref": "echo", "to_ref": "approval"},
    {"from_ref": "approval", "to_ref": "add"}
  ]
}
```

## Trigger, pause, and resume
- **Trigger a run**: `POST /api/workflows/{id}/trigger` with optional `context` and `executor`.
- **Pause a run**: `POST /api/runs/{id}/pause` with an optional `reason`.
- **Resume a run**: `POST /api/runs/{id}/resume` with optional context updates. Human nodes automatically pause the run with `pause_reason="Awaiting human input"` until you resume.

Responses include the current run state, node runs, and context so clients can display progress or hand off between workers.
