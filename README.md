# ARW-P

The **Agent-Ready Web Protocol** gives websites a dedicated, machine-friendly lane for AI agents. It defines discovery files, token handshakes and lightweight endpoints so bots can search, read and take limited actions without scraping HTML.

## Documentation
Public docs are generated with [MkDocs](https://www.mkdocs.org/) and served via GitHub Pages. After enabling Pages, they will be available at:
```
https://arwproject.github.io/ARW-P/
```

## Django workflow orchestration engine
A Django service is included for defining and executing workflows with pluggable executors (local or Celery) and resumable run state.

### Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Set `CELERY_TASK_ALWAYS_EAGER=true` to execute Celery nodes without a broker. For real brokers, configure `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND`.

### Create and trigger a workflow
POST `/api/workflows/` with nodes, parameters, and edges, then trigger it:
```bash
curl -X POST http://localhost:8000/api/workflows/ \
  -H "Content-Type: application/json" \
  -d @workflow.json

curl -X POST http://localhost:8000/api/workflows/1/trigger \
  -H "Content-Type: application/json" \
  -d '{"context": {"sum": 4}}'
```

Additional API docs live in [`docs/workflow-engine.md`](docs/workflow-engine.md).

## Contributing
1. Fork the repo and create a branch.
2. Add or update documentation in the `docs/` folder.
3. Run `mkdocs build` to verify the site.
4. Open a Pull Request.

## License
This project is licensed under the terms of the [MIT License](LICENSE).
