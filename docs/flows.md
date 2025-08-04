# 🔄 Endpoint & Token Flows

**Complete guide to implementing ARW-P authentication and API interactions**

*From discovery to production-ready implementations*

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
    }
  },
  "endpoints": [
    {
      "path": "/ai/search",
      "method": "POST",
      "scope": "search",
      "description": "Semantic search across all content"
    },
    {
      "path": "/ai/content/{id}",
      "method": "GET", 
      "scope": "content",
      "description": "Retrieve structured content by ID"
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
            version: process.env.API_VERSION
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
  "algorithm": "ES256"
}
```

### Step 2: Generate Cryptographic Proof

The agent must sign the nonce with their private key:

```javascript
// Agent-side implementation (conceptual)
async function generateProof(nonce, privateKey) {
    const payload = {
        nonce: nonce,
        timestamp: Date.now(),
        agent: {
            id: "agent-12345",
            version: "1.0.0"
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
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "scope": "search content",
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

        // Generate access token
        const accessToken = jwt.sign(
            {
                sub: agent.id,
                scopes: ['search', 'content'],
                iat: Math.floor(Date.now() / 1000),
                exp: Math.floor(Date.now() / 1000) + 3600
            },
            process.env.JWT_SECRET,
            { algorithm: 'HS256' }
        );

        // Clean up nonce
        await redis.del(`nonce:${nonce}`);

        res.json({
            token: accessToken,
            tokenType: 'Bearer',
            expiresIn: 3600,
            scope: 'search content'
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
      "snippet": "Scientists develop new sustainable energy technology that increases solar efficiency by 40%",
      "relevance": 0.95,
      "metadata": {
        "author": "Dr. Sarah Chen",
        "publishDate": "2024-01-10T09:00:00Z",
        "category": "technology",
        "tags": ["solar", "renewable", "innovation"],
        "readTime": "8 min"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalPages": 16,
    "hasNext": true
  }
}
```

---

## 🔄 Complete Flow Summary

Here's the complete interaction flow:

```
1. DISCOVERY PHASE
   Agent → GET /.well-known/agents.json
   Site  → Returns capabilities and requirements

2. AUTHENTICATION PHASE
   Agent → GET /.well-known/ai-token
   Site  → Returns challenge with nonce
   
   Agent → Signs nonce with private key
   Agent → POST /.well-known/ai-token with proof
   Site  → Verifies signature and returns JWT token

3. API USAGE PHASE
   Agent → POST /ai/search with Bearer token
   Site  → Validates token and returns results
   
   (Multiple API calls can be made with the same token)

4. TOKEN REFRESH (Optional)
   Agent → POST refresh token
   Site  → Returns new access token
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
    "timestamp": "2024-01-15T10:30:00Z"
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

## 🎯 Next Steps

Ready to implement ARW-P? Here's your action plan:

1. **🔧 Setup Discovery Files** - Create `/.well-known/agents.json`
2. **🔐 Implement Authentication** - Add token exchange endpoints
3. **⚡ Create API Endpoints** - Build your AI-friendly APIs
4. **🧪 Test Integration** - Validate with test agents
5. **📊 Monitor Usage** - Track performance and usage patterns

---

**Questions? Need help?**

[📖 Documentation](/) • [💬 Community Forum](https://github.com/arwproject/arw-p/discussions) • [🐛 Report Issues](https://github.com/arwproject/arw-p/issues)
