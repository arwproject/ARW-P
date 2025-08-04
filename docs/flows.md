# 🔄 Endpoint & Token Flows

<div align="center">

**Complete guide to implementing ARW-P authentication and API interactions**

*From discovery to production-ready implementations*

</div>

---

## 📖 Overview

This guide provides a comprehensive walkthrough of how AI agents securely interact with ARW-P-enabled websites. The flow consists of three main phases:

1. **🔍 Discovery Phase** - Agent discovers capabilities
2. **🔐 Authentication Phase** - Secure token exchange  
3. **⚡ API Usage Phase** - Making authenticated requests

---

## 🔍 Phase 1: Discovery

Before any interaction, agents must discover what capabilities your site offers.

### Step 1: Capability Discovery

The agent starts by fetching your site's capabilities:

```bash
curl https://example.com/.well-known/agents.json
```

**Response:**
```json
{
  "$schema": "https://arw.dev/schemas/agents-0.1.json",
  "specVersion": "0.1",
  "meta": {
    "name": "Example Corp API",
    "description": "AI-friendly access to our platform",
    "version": "1.2.0",
    "contact": {
      "email": "api@example.com",
      "url": "https://example.com/developer"
    }
  },
  "authentication": {
    "required": true,
    "schemes": ["bearer"],
    "tokenTtl": 3600,
    "scopes": ["search", "content", "analytics"]
  },
  "rateLimits": {
    "default": {
      "requests": 100,
      "windowMs": 60000,
      "scope": "global"
    },
    "burst": {
      "allowed": true,
      "maxBurst": 10
    }
  },
  "endpoints": [
    {
      "path": "/ai/search",
      "method": "POST",
      "scope": "search",
      "description": "Semantic search across all content",
      "rateLimits": {
        "requests": 50,
        "windowMs": 60000
      }
    },
    {
      "path": "/ai/content/{id}",
      "method": "GET", 
      "scope": "content",
      "description": "Retrieve structured content by ID"
    },
    {
      "path": "/ai/analytics/summary",
      "method": "GET",
      "scope": "analytics", 
      "description": "Get usage analytics summary"
    }
  ]
}
```

### Implementation Example

```javascript
// Server-side implementation
app.get('/.well-known/agents.json', (req, res) => {
    const capabilities = {
        $schema: "https://arw.dev/schemas/agents-0.1.json",
        specVersion: "0.1",
        meta: {
            name: process.env.API_NAME,
            description: "AI-friendly access to our platform",
            version: process.env.API_VERSION,
            contact: {
                email: process.env.CONTACT_EMAIL,
                url: process.env.DEVELOPER_URL
            }
        },
        authentication: {
            required: true,
            schemes: ["bearer"],
            tokenTtl: 3600
        },
        endpoints: getAvailableEndpoints(),
        rateLimits: getRateLimitConfig()
    };

    res.set({
        'Cache-Control': 'public, max-age=3600',
        'Content-Type': 'application/json'
    });
    
    res.json(capabilities);
});
```

---

## 🔐 Phase 2: Authentication

ARW-P uses a challenge-response authentication mechanism with cryptographic signatures.

### Step 1: Request Authentication Challenge

```bash
curl https://example.com/.well-known/ai-token
```

**Response:**
```json
{
  "nonce": "abc123def456",
  "tokenEndpoint": "https://example.com/.well-known/ai-token",
  "expiresAt": "2024-01-15T10:30:00Z",
  "algorithm": "ES256",
  "challenge": {
    "format": "jwt",
    "claims": {
      "iss": "example.com",
      "aud": "ai-agents",
      "exp": 1705315800
    }
  }
}
```

### Step 2: Generate Cryptographic Proof

The agent must sign the nonce with their private key:

```javascript
// Agent-side implementation (conceptual)
import { signJWT } from './crypto-utils';

async function generateProof(nonce, privateKey) {
    const payload = {
        nonce: nonce,
        timestamp: Date.now(),
        agent: {
            id: "agent-12345",
            version: "1.0.0",
            capabilities: ["search", "content"]
        }
    };
    
    return await signJWT(payload, privateKey, {
        algorithm: 'ES256',
        expiresIn: '5m'
    });
}
```

### Step 3: Exchange Proof for Token

```bash
curl -X POST https://example.com/.well-known/ai-token \
  -H "Content-Type: application/json" \
  -d '{
    "nonce": "abc123def456",
    "proof": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9...",
    "agent": {
      "id": "agent-12345",
      "publicKey": "-----BEGIN PUBLIC KEY-----\n...",
      "requestedScopes": ["search", "content"]
    }
  }'
```

**Success Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZ2VudC0xMjM0NSIsInNjb3BlcyI6WyJzZWFyY2giLCJjb250ZW50Il0sImlhdCI6MTcwNTMxMjIwMCwiZXhwIjoxNzA1MzE1ODAwfQ.signature",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "scope": "search content",
  "refreshToken": "refresh_token_here",
  "rateLimits": {
    "remaining": 100,
    "resetAt": "2024-01-15T11:30:00Z"
  }
}
```

**Error Response:**
```json
{
  "error": "invalid_proof",
  "error_description": "The provided cryptographic proof is invalid",
  "error_code": 4001,
  "retryAfter": 60
}
```

### Server-Side Token Exchange Implementation

```javascript
app.post('/.well-known/ai-token', async (req, res) => {
    try {
        const { nonce, proof, agent } = req.body;

        // Validate request structure
        if (!nonce || !proof || !agent?.id) {
            return res.status(400).json({
                error: 'invalid_request',
                error_description: 'Missing required parameters'
            });
        }

        // Verify nonce exists and hasn't expired
        const storedChallenge = await redis.get(`nonce:${nonce}`);
        if (!storedChallenge) {
            return res.status(400).json({
                error: 'invalid_nonce',
                error_description: 'Nonce not found or expired'
            });
        }

        // Verify cryptographic proof
        const isValidProof = await cryptoUtils.verifySignature(
            proof,
            agent.publicKey,
            nonce
        );

        if (!isValidProof) {
            return res.status(401).json({
                error: 'invalid_proof',
                error_description: 'Cryptographic proof verification failed'
            });
        }

        // Check agent authorization
        const authorizedScopes = await checkAgentAuthorization(
            agent.id,
            agent.requestedScopes
        );

        if (authorizedScopes.length === 0) {
            return res.status(403).json({
                error: 'insufficient_scope',
                error_description: 'Agent not authorized for requested scopes'
            });
        }

        // Generate access token
        const accessToken = jwt.sign(
            {
                sub: agent.id,
                scopes: authorizedScopes,
                iat: Math.floor(Date.now() / 1000),
                exp: Math.floor(Date.now() / 1000) + 3600
            },
            process.env.JWT_SECRET,
            { algorithm: 'HS256' }
        );

        // Generate refresh token (optional)
        const refreshToken = await generateRefreshToken(agent.id);

        // Clean up nonce
        await redis.del(`nonce:${nonce}`);

        // Track token issuance
        await auditLog.log({
            event: 'token_issued',
            agentId: agent.id,
            scopes: authorizedScopes,
            timestamp: new Date()
        });

        res.json({
            token: accessToken,
            tokenType: 'Bearer',
            expiresIn: 3600,
            scope: authorizedScopes.join(' '),
            refreshToken,
            rateLimits: await getRateLimitStatus(agent.id)
        });

    } catch (error) {
        console.error('Token exchange error:', error);
        res.status(500).json({
            error: 'server_error',
            error_description: 'Internal server error during token exchange'
        });
    }
});
```

---

## ⚡ Phase 3: API Usage

With a valid token, agents can now make authenticated requests to your endpoints.

### Making Authenticated Requests

```bash
curl https://example.com/ai/search \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyAI-Agent/1.0" \
  -d '{
    "q": "sustainable energy solutions",
    "limit": 10,
    "filters": {
      "category": ["technology", "environment"],
      "publishedAfter": "2023-01-01"
    },
    "options": {
      "includeSnippets": true,
      "highlightTerms": true
    }
  }'
```

**Success Response:**
```json
{
  "query": "sustainable energy solutions", 
  "took": 23,
  "total": 156,
  "results": [
    {
      "id": "art-123",
      "title": "Revolutionary Solar Panel Technology",
      "url": "/articles/solar-panel-breakthrough",
      "snippet": "Scientists develop new <mark>sustainable energy</mark> technology that increases solar efficiency by 40%",
      "relevance": 0.95,
      "metadata": {
        "author": "Dr. Sarah Chen",
        "publishDate": "2024-01-10T09:00:00Z",
        "category": "technology",
        "tags": ["solar", "renewable", "innovation"],
        "readTime": "8 min",
        "language": "en"
      },
      "analytics": {
        "views": 15420,
        "shares": 89,
        "rating": 4.7
      }
    }
  ],
  "facets": {
    "categories": [
      {"name": "Technology", "count": 89, "selected": true},
      {"name": "Environment", "count": 67, "selected": true},
      {"name": "Business", "count": 34, "selected": false}
    ],
    "timeRange": [
      {"period": "Last month", "count": 23},
      {"period": "Last 3 months", "count": 67},
      {"period": "Last year", "count": 156}
    ]
  },
  "suggestions": [
    "wind energy innovations",
    "battery storage solutions",
    "green hydrogen technology"
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalPages": 16,
    "hasNext": true,
    "nextCursor": "eyJzY29yZSI6MC45NSwiaWQiOiJhcnQtMTIzIn0="
  },
  "meta": {
    "requestId": "req-abc123",
    "timestamp": "2024-01-15T10:30:00Z",
    "version": "1.2.0"
  }
}
```

### Advanced Content Retrieval

```bash
curl https://example.com/ai/content/art-123 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Accept: application/json"
```

**Response:**
```json
{
  "id": "art-123",
  "type": "article",
  "title": "Revolutionary Solar Panel Technology",
  "content": {
    "abstract": "This article explores breakthrough solar panel technology that promises to revolutionize renewable energy adoption worldwide.",
    "sections": [
      {
        "heading": "Introduction",
        "content": "The renewable energy sector has seen remarkable progress...",
        "wordCount": 156
      },
      {
        "heading": "Technical Innovation", 
        "content": "The new photovoltaic cells utilize a novel perovskite structure...",
        "wordCount": 234
      }
    ],
    "keyPoints": [
      "40% efficiency improvement over traditional panels",
      "Lower manufacturing costs due to simplified process",
      "Enhanced durability in extreme weather conditions"
    ],
    "totalWordCount": 1250
  },
  "metadata": {
    "author": {
      "name": "Dr. Sarah Chen",
      "bio": "Leading researcher in photovoltaic technology",
      "credentials": ["PhD Physics", "MIT Solar Research Lab"]
    },
    "publishDate": "2024-01-10T09:00:00Z",
    "lastModified": "2024-01-12T14:30:00Z",
    "category": "technology",
    "tags": ["solar", "renewable", "innovation", "efficiency"],
    "seo": {
      "metaDescription": "Discover breakthrough solar panel technology...",
      "focusKeywords": ["solar panels", "renewable energy", "efficiency"]
    }
  },
  "media": [
    {
      "type": "image",
      "url": "/images/solar-panel-lab.jpg",
      "alt": "Researchers testing new solar panel prototypes",
      "caption": "Testing the new high-efficiency solar panels"
    }
  ],
  "references": [
    {
      "title": "Perovskite Solar Cells: Progress and Challenges",
      "authors": ["Chen, S.", "Johnson, M."],
      "journal": "Nature Energy",
      "year": 2023,
      "doi": "10.1038/s41560-023-01234-5"
    }
  ]
}
```

---

## 🔄 Complete Flow Diagram

```mermaid
sequenceDiagram
    participant Agent as 🤖 AI Agent
    participant Discovery as 🔍 Discovery Service
    participant Auth as 🔐 Auth Service
    participant API as ⚡ API Service
    participant Cache as 💾 Cache Layer
    participant DB as 🗄️ Database

    Note over Agent,DB: Phase 1: Discovery
    Agent->>Discovery: GET /.well-known/agents.json
    Discovery->>Cache: Check cached capabilities
    alt Cache Hit
        Cache-->>Discovery: Return cached data
    else Cache Miss
        Discovery->>DB: Fetch current capabilities
        DB-->>Discovery: Return capabilities
        Discovery->>Cache: Store in cache
    end
    Discovery-->>Agent: Capabilities + Rate Limits

    Note over Agent,DB: Phase 2: Authentication
    Agent->>Auth: GET /.well-known/ai-token
    Auth->>Cache: Generate & store nonce
    Auth-->>Agent: Challenge with nonce

    Agent->>Agent: Sign nonce with private key
    Agent->>Auth: POST with signed proof
    Auth->>Cache: Verify nonce exists
    Auth->>Auth: Verify cryptographic signature
    Auth->>DB: Check agent authorization
    alt Valid Signature & Authorized
        Auth->>Cache: Store token metadata
        Auth-->>Agent: Access token + refresh token
    else Invalid/Unauthorized
        Auth-->>Agent: Error response
    end

    Note over Agent,DB: Phase 3: API Usage
    loop Multiple API Calls
        Agent->>API: Request with Bearer token
        API->>Cache: Validate token & check rate limits
        alt Valid Token & Within Limits
            API->>DB: Fetch requested data
            DB-->>API: Return data
            API->>Cache: Update rate limit counters
            API-->>Agent: Structured response
        else Invalid Token
            API-->>Agent: 401 Unauthorized
        else Rate Limited
            API-->>Agent: 429 Too Many Requests
        end
    end

    Note over Agent,DB: Optional: Token Refresh
    Agent->>Auth: POST refresh token
    Auth->>Cache: Validate refresh token
    alt Valid Refresh Token
        Auth->>Cache: Generate new access token
        Auth-->>Agent: New access token
    else Invalid Refresh Token
        Auth-->>Agent: Re-authentication required
    end
```

---

## 🛡️ Security Best Practices

### Token Security

```javascript
// Implement secure token storage
class TokenManager {
    constructor() {
        this.tokens = new Map();
        this.cleanupInterval = setInterval(() => {
            this.cleanupExpiredTokens();
        }, 60000); // Cleanup every minute
    }

    storeToken(agentId, tokenData) {
        this.tokens.set(agentId, {
            ...tokenData,
            createdAt: Date.now(),
            lastUsed: Date.now()
        });
    }

    validateToken(token) {
        try {
            const decoded = jwt.verify(token, process.env.JWT_SECRET);
            const tokenData = this.tokens.get(decoded.sub);
            
            if (!tokenData) {
                throw new Error('Token not found');
            }

            // Update last used timestamp
            tokenData.lastUsed = Date.now();
            
            return decoded;
        } catch (error) {
            throw new Error('Invalid token');
        }
    }

    cleanupExpiredTokens() {
        const now = Date.now();
        for (const [agentId, tokenData] of this.tokens) {
            if (now - tokenData.lastUsed > 24 * 60 * 60 * 1000) {
                this.tokens.delete(agentId);
            }
        }
    }
}
```

### Rate Limiting Implementation

```javascript
class RateLimiter {
    constructor() {
        this.limits = new Map();
    }

    async checkLimit(agentId, endpoint, limits) {
        const key = `${agentId}:${endpoint}`;
        const now = Date.now();
        const windowMs = limits.windowMs || 60000;
        
        let usage = this.limits.get(key) || {
            count: 0,
            resetTime: now + windowMs
        };

        // Reset if window expired
        if (now >= usage.resetTime) {
            usage = {
                count: 0,
                resetTime: now + windowMs
            };
        }

        // Check if limit exceeded
        if (usage.count >= limits.requests) {
            throw new Error(`Rate limit exceeded. Try again in ${Math.ceil((usage.resetTime - now) / 1000)} seconds`);
        }

        // Increment usage
        usage.count++;
        this.limits.set(key, usage);

        return {
            remaining: limits.requests - usage.count,
            resetTime: usage.resetTime
        };
    }
}
```

---

## 🚨 Error Handling

### Common Error Responses

| Status Code | Error Type | Description | Retry Strategy |
|-------------|------------|-------------|----------------|
| 400 | `invalid_request` | Malformed request parameters | Don't retry, fix request |
| 401 | `invalid_token` | Token expired or invalid | Refresh token or re-authenticate |
| 403 | `insufficient_scope` | Token lacks required permissions | Request appropriate scopes |
| 429 | `rate_limit_exceeded` | Too many requests | Retry after specified delay |
| 500 | `server_error` | Internal server error | Retry with exponential backoff |

### Error Response Format

```json
{
  "error": "rate_limit_exceeded",
  "error_description": "Request limit exceeded for this time window",
  "error_code": 4291,
  "details": {
    "limit": 100,
    "remaining": 0,
    "resetAt": "2024-01-15T11:00:00Z",
    "retryAfter": 300
  },
  "meta": {
    "requestId": "req-abc123",
    "timestamp": "2024-01-15T10:30:00Z",
    "documentation": "https://example.com/docs/errors#rate-limiting"
  }
}
```

### Client-Side Error Handling

```javascript
class ARWPClient {
    async makeRequest(endpoint, options = {}) {
        const maxRetries = options.maxRetries || 3;
        let attempt = 0;

        while (attempt < maxRetries) {
            try {
                const response = await this.executeRequest(endpoint, options);
                return response;
            } catch (error) {
                attempt++;
                
                if (error.status === 429) {
                    // Rate limited - wait and retry
                    const retryAfter = error.retryAfter || Math.pow(2, attempt) * 1000;
                    await this.sleep(retryAfter);
                    continue;
                } else if (error.status === 401) {
                    // Token expired - refresh and retry
                    await this.refreshToken();
                    continue;
                } else if (error.status >= 500 && attempt < maxRetries) {
                    // Server error - exponential backoff
                    await this.sleep(Math.pow(2, attempt) * 1000);
                    continue;
                } else {
                    // Don't retry other errors
                    throw error;
                }
            }
        }
        
        throw new Error(`Max retries (${maxRetries}) exceeded`);
    }

    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
```

---

## 📊 Monitoring & Analytics

### Request Logging

```javascript
// Comprehensive request logging
app.use('/ai/*', (req, res, next) => {
    const startTime = Date.now();
    const requestId = generateRequestId();
    
    req.requestId = requestId;
    req.startTime = startTime;

    res.on('finish', () => {
        const duration = Date.now() - startTime;
        const logData = {
            requestId,
            method: req.method,
            path: req.path,
            agentId: req.agentId,
            statusCode: res.statusCode,
            duration,
            userAgent: req.get('User-Agent'),
            ip: req.ip,
            timestamp: new Date().toISOString()
        };

        // Log to analytics service
        analytics.track('api_request', logData);
        
        // Update metrics
        metrics.requestDuration.observe(
            { endpoint: req.path, status: res.statusCode },
            duration
        );
    });

    next();
});
```

### Performance Metrics

```javascript
// Key metrics to track
const metrics = {
    requestCount: new Counter('arwp_requests_total', ['endpoint', 'method', 'status']),
    requestDuration: new Histogram('arwp_request_duration_ms', ['endpoint', 'status']),
    activeTokens: new Gauge('arwp_active_tokens'),
    rateLimitHits: new Counter('arwp_rate_limit_hits', ['agentId', 'endpoint']),
    authFailures: new Counter('arwp_auth_failures', ['reason']),
    dataTransfer: new Counter('arwp_bytes_transferred', ['direction'])
};

// Dashboard query examples
const dashboardQueries = {
    requestRate: 'rate(arwp_requests_total[5m])',
    errorRate: 'rate(arwp_requests_total{status=~"4..|5.."}[5m])',
    avgResponseTime: 'avg(arwp_request_duration_ms) by (endpoint)',
    topAgents: 'topk(10, sum by (agentId) (arwp_requests_total))'
};
```

---

## 🎯 Next Steps

Ready to implement ARW-P? Here's your action plan:

1. **🔧 [Setup Guide](setup.md)** - Step-by-step implementation
2. **📚 [API Reference](api-reference.md)** - Complete endpoint documentation  
3. **🧪 [Testing Tools](testing.md)** - Validation and debugging utilities
4. **🏗️ [Examples](examples.md)** - Real-world implementation patterns
5. **🤝 [Community](https://github.com/arwproject/arw-p/discussions)** - Get help and share experiences

---

<div align="center">

**Questions? Need help?**

[📖 Documentation](/) • [💬 Community Forum](https://github.com/arwproject/arw-p/discussions) • [🐛 Report Issues](https://github.com/arwproject/arw-p/issues)

</div>
