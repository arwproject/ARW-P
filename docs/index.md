# ARW-P: Agent-Ready Web Protocol

ARW-P (pronounced "R-Web-P") is an open standard that lets any website expose a fast, secure, machine-friendly lane for AI agents without altering the human experience. It provides structured endpoints and token-based access so bots can interact with your site predictably and responsibly.

## Why ARW-P?
- **Structured facts** to reduce hallucinations
- **Cheap bandwidth** compared to rendering full HTML
- **Safe action surface** through documented, typed APIs

## Core actors & trust model
| Actor | Responsibilities in ARW-P |
|-------|---------------------------|
| **Site Host** | Publishes discovery files and issues short-lived tokens |
| **Agent Provider** | Supplies public keys and respects documented endpoints |
| **Edge Gateway** (optional) | Authenticates, rate-limits, and shapes responses |
| **Human Visitor** | Continues using normal HTML/JS pages |

## Required artefacts (v0.1)
| File / Endpoint | Host path | Must contain |
|-----------------|-----------|--------------|
| `/.well-known/ai-token` | GET & POST | JWT meta and token grant |
| `/.well-known/agents.json` | GET | List of endpoints, scopes, rate limits, specVersion |
| `/ai/<pageId>.json` | GET | Slim content or OpenAPI ref |
| `/ai/search` | POST | Natural-language search endpoint |
| _Optional push channel_ | `/ai/stream/*` | Server-Sent Events for flash data |

## Minimal `agents.json` example
```json
{
  "$schema": "https://arw.dev/schemas/agents-0.1.json",
  "specVersion": "0.1",
  "endpoints": [
    {
      "path": "/ai/search",
      "method": "POST",
      "scope": "search",
      "description": "Natural-language search"
    }
  ]
}
```

Learn more in the [endpoint & token flows](flows.md) guide.
