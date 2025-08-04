# 🔄 Endpoint & Token Flows

**Complete guide to implementing ARW-P authentication and API interactions**

*From discovery to production-ready implementations*

---

## 📖 Overview

This guide provides a comprehensive walkthrough of how AI agents securely interact with ARW-P-enabled websites. The flow consists of four main phases:

1. **🔍 Discovery Phase** - Agent discovers capabilities
2. **🔐 Agent Authentication Phase** - Secure agent identity verification  
3. **👤 User Delegation Phase** - User-specific token delegation
4. **⚡ API Usage Phase** - Making authenticated requests

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

## 👤 Phase 2.5: User Delegation Authentication

**CRITICAL**: For agents acting on behalf of specific users (booking flights, making purchases, accessing private content), a second authentication layer is required.

### Understanding the Two-Token Pattern

ARW-P implements a **two-token pattern** for user delegation:

1. **Agent Token** - Verifies the agent's identity to the site
2. **User Token** - Proves the agent has permission to act for a specific user

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Agent Provider │    │   Your Website   │    │   Human User    │
│                 │    │                 │    │                 │
│ 1. Get Agent    │───▶│ Issue Agent     │    │                 │
│    Token        │◀───│ Token           │    │                 │
│                 │    │                 │    │                 │
│ 2. Request User │───▶│ Redirect to     │───▶│ 3. User Login   │
│    Delegation   │    │ User Auth       │    │    & Consent    │
│                 │    │                 │    │                 │
│ 4. Receive      │◀───│ Issue User      │◀───│ Grant Permission│
│    User Token   │    │ Token           │    │                 │
│                 │    │                 │    │                 │
│ 5. Combined     │───▶│ Validate Both   │    │                 │
│    API Calls    │    │ Tokens          │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Step 1: Agent Requests User Delegation

After obtaining an agent token, the agent must request permission to act on behalf of a user:

```bash
curl -X POST https://example.com/.well-known/user-delegate \
  -H "Authorization: Bearer <AGENT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user@example.com",
    "scopes": ["booking", "payments", "profile"],
    "callback_url": "https://agent-provider.com/auth/callback",
    "purpose": "Book flight and hotel for business trip",
    "session_duration": 3600
  }'
```

**Response:**
```json
{
  "delegation_request_id": "del_abc123",
  "user_auth_url": "https://example.com/auth/delegate?request_id=del_abc123",
  "expires_at": "2024-01-15T10:35:00Z",
  "required_scopes": ["booking", "payments"],
  "status": "pending_user_consent"
}
```

### Step 2: User Consent Flow

The user must explicitly grant permission for the agent to act on their behalf:

```bash
# User is redirected to the auth URL and logs in
GET https://example.com/auth/delegate?request_id=del_abc123

# After user login and consent, they're redirected back with a code
GET https://agent-provider.com/auth/callback?code=auth_xyz789&request_id=del_abc123
```

### Step 3: Agent Exchanges Code for User Token

```bash
curl -X POST https://example.com/.well-known/user-token \
  -H "Authorization: Bearer <AGENT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "delegation_request_id": "del_abc123",
    "authorization_code": "auth_xyz789",
    "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
  }'
```

**Success Response:**
```json
{
  "user_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "booking payments profile",
  "user_info": {
    "user_id": "user@example.com",
    "name": "John Doe",
    "verified": true
  },
  "delegation_expires_at": "2024-01-15T11:30:00Z"
}
```

### Step 4: Making User-Delegated API Calls

When making API calls that require user context, include both tokens:

```bash
curl -X POST https://example.com/ai/bookings/create \
  -H "Authorization: Bearer <AGENT_TOKEN>" \
  -H "X-User-Token: Bearer <USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "flight": {
      "from": "NYC",
      "to": "LAX", 
      "date": "2024-02-15",
      "passengers": 1
    },
    "payment_method": "user_default"
  }'
```

**Alternative: Combined JWT Token Pattern**

Some implementations may prefer a single combined token:

```bash
curl -X POST https://example.com/.well-known/combined-token \
  -H "Authorization: Bearer <AGENT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "user_token": "<USER_TOKEN>",
    "requested_scopes": ["booking", "payments"]
  }'
```

**Combined Token Response:**
```json
{
  "combined_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer", 
  "expires_in": 3600,
  "contains": {
    "agent_id": "agent-12345",
    "user_id": "user@example.com",
    "scopes": ["booking", "payments"],
    "delegation_id": "del_abc123"
  }
}
```

### User Delegation Security Requirements

1. **Explicit User Consent** - Users must actively approve each delegation request
2. **Scope Limitation** - User tokens are restricted to explicitly granted scopes
3. **Time Bounds** - User delegations must have explicit expiration times  
4. **Revocation** - Users can revoke agent permissions at any time
5. **Audit Trail** - All user-delegated actions must be logged and auditable

### Implementation Example: User Delegation Endpoint

```javascript
app.post('/.well-known/user-delegate', authenticateAgent, async (req, res) => {
    try {
        const { user_id, scopes, callback_url, purpose, session_duration } = req.body;
        const agentId = req.agent.id;

        // Validate requested scopes
        const allowedScopes = ['booking', 'payments', 'profile', 'preferences'];
        const validScopes = scopes.filter(scope => allowedScopes.includes(scope));
        
        if (validScopes.length === 0) {
            return res.status(400).json({
                error: 'invalid_scope',
                error_description: 'No valid scopes requested'
            });
        }

        // Create delegation request
        const delegationRequest = {
            id: `del_${generateId()}`,
            agent_id: agentId,
            user_id: user_id,
            scopes: validScopes,
            callback_url: callback_url,
            purpose: purpose,
            status: 'pending_user_consent',
            created_at: new Date(),
            expires_at: new Date(Date.now() + 10 * 60 * 1000), // 10 minutes
            session_duration: Math.min(session_duration || 3600, 7200) // Max 2 hours
        };

        await redis.setex(
            `delegation:${delegationRequest.id}`, 
            600, 
            JSON.stringify(delegationRequest)
        );

        res.json({
            delegation_request_id: delegationRequest.id,
            user_auth_url: `${process.env.BASE_URL}/auth/delegate?request_id=${delegationRequest.id}`,
            expires_at: delegationRequest.expires_at,
            required_scopes: validScopes,
            status: 'pending_user_consent'
        });

    } catch (error) {
        console.error('Delegation request error:', error);
        res.status(500).json({
            error: 'server_error',
            error_description: 'Failed to create delegation request'
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

---

## 🚀 Complete cURL Flow Demonstration

Here's a complete, executable cURL demonstration of the full ARW-P handshake including user delegation:

### Phase 1: Agent Provider Setup

First, the agent provider needs to have their public key registered and available:

```bash
# Agent Provider's public key (would be available at a well-known URL)
curl https://agent-provider.com/.well-known/public-key.pem
```

### Phase 2: Agent Identity Authentication

```bash
# Step 1: Request challenge nonce
curl -X GET https://example.com/.well-known/ai-token \
  -H "User-Agent: MyAI-Agent/1.0"

# Response:
# {
#   "nonce": "nonce_abc123def456",
#   "tokenEndpoint": "https://example.com/.well-known/ai-token",
#   "expiresAt": "2024-01-15T10:35:00Z",
#   "algorithm": "ES256"
# }

# Step 2: Sign the nonce with agent's private key (conceptual - would be done programmatically)
# SIGNATURE = sign_with_private_key(nonce + timestamp + agent_id)

# Step 3: Exchange signed nonce for agent token
curl -X POST https://example.com/.well-known/ai-token \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyAI-Agent/1.0" \
  -d '{
    "nonce": "nonce_abc123def456",
    "proof": "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6Im5vbmNlX2FiYzEyM2RlZjQ1NiIsInRpbWVzdGFtcCI6MTcwNTMxNTgwMCwiYWdlbnQiOnsiaWQiOiJhZ2VudC0xMjM0NSIsInZlcnNpb24iOiIxLjAuMCJ9fQ.signature_here",
    "agent": {
      "id": "agent-12345",
      "publicKey": "-----BEGIN PUBLIC KEY-----\nMFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...\n-----END PUBLIC KEY-----",
      "requestedScopes": ["search", "content", "booking"]
    }
  }'

# Response:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.agent_token_payload.signature",
#   "tokenType": "Bearer",
#   "expiresIn": 3600,
#   "scope": "search content booking",
#   "rateLimits": {
#     "remaining": 100,
#     "resetAt": "2024-01-15T11:30:00Z"
#   }
# }
```

### Phase 3: User Delegation Request

```bash
# Step 1: Agent requests permission to act on behalf of user
curl -X POST https://example.com/.well-known/user-delegate \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.agent_token_payload.signature" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "john.doe@email.com",
    "scopes": ["booking", "payments", "profile"],
    "callback_url": "https://agent-provider.com/auth/callback/12345",
    "purpose": "Book a flight and hotel for business trip to San Francisco",
    "session_duration": 3600
  }'

# Response:
# {
#   "delegation_request_id": "del_xyz789",
#   "user_auth_url": "https://example.com/auth/delegate?request_id=del_xyz789",
#   "expires_at": "2024-01-15T10:40:00Z",
#   "required_scopes": ["booking", "payments"],
#   "status": "pending_user_consent"
# }
```

### Phase 4: User Consent (Human Step)

```bash
# User visits the auth URL and grants consent (human step)
# After consent, user is redirected to:
# https://agent-provider.com/auth/callback/12345?code=auth_code_987&request_id=del_xyz789
```

### Phase 5: Exchange Authorization Code for User Token

```bash
# Step 2: Agent exchanges authorization code for user token
curl -X POST https://example.com/.well-known/user-token \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.agent_token_payload.signature" \
  -H "Content-Type: application/json" \
  -d '{
    "delegation_request_id": "del_xyz789",
    "authorization_code": "auth_code_987",
    "code_verifier": "dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk"
  }'

# Response:
# {
#   "user_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.user_token_payload.signature",
#   "token_type": "Bearer",
#   "expires_in": 3600,
#   "scope": "booking payments profile",
#   "user_info": {
#     "user_id": "john.doe@email.com",
#     "name": "John Doe",
#     "verified": true,
#     "account_level": "premium"
#   },
#   "delegation_expires_at": "2024-01-15T11:35:00Z"
# }
```

### Phase 6: Making User-Delegated API Calls

```bash
# Step 1: Search for flights (agent token only - public data)
curl -X POST https://example.com/ai/flights/search \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.agent_token_payload.signature" \
  -H "Content-Type: application/json" \
  -d '{
    "from": "JFK",
    "to": "SFO",
    "departure_date": "2024-02-15",
    "return_date": "2024-02-18",
    "passengers": 1,
    "class": "business"
  }'

# Response:
# {
#   "results": [
#     {
#       "flight_id": "UA123",
#       "airline": "United Airlines",
#       "price": 899,
#       "departure": "2024-02-15T08:00:00Z",
#       "arrival": "2024-02-15T14:30:00Z",
#       "available_seats": 12
#     }
#   ],
#   "search_id": "search_abc123"
# }

# Step 2: Book the flight (requires both tokens - user action)
curl -X POST https://example.com/ai/flights/book \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.agent_token_payload.signature" \
  -H "X-User-Token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.user_token_payload.signature" \
  -H "Content-Type: application/json" \
  -d '{
    "flight_id": "UA123",
    "search_id": "search_abc123",
    "passenger_info": {
      "name": "John Doe",
      "email": "john.doe@email.com",
      "phone": "+1-555-0123"
    },
    "payment_method": "user_default",
    "seat_preference": "aisle"
  }'

# Response:
# {
#   "booking_id": "book_def456",
#   "status": "confirmed",
#   "confirmation_code": "ABC123",
#   "total_price": 899,
#   "payment_status": "processed",
#   "booking_details": {
#     "flight": "UA123",
#     "departure": "2024-02-15T08:00:00Z",
#     "seat": "3A",
#     "gate": "TBD"
#   },
#   "booking_timestamp": "2024-01-15T10:45:00Z"
# }

# Step 3: Get booking confirmation (user-specific data)
curl -X GET https://example.com/ai/bookings/book_def456 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.agent_token_payload.signature" \
  -H "X-User-Token: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.user_token_payload.signature"

# Response:
# {
#   "booking_id": "book_def456",
#   "status": "confirmed",
#   "confirmation_code": "ABC123",
#   "user_id": "john.doe@email.com",
#   "created_by_agent": "agent-12345",
#   "booking_details": { ... },
#   "modification_allowed": true,
#   "cancellation_deadline": "2024-02-08T23:59:59Z"
# }
```

### Error Handling Examples

```bash
# Invalid token example
curl -X POST https://example.com/ai/flights/book \
  -H "Authorization: Bearer invalid_token" \
  -H "X-User-Token: Bearer user_token" \
  -H "Content-Type: application/json" \
  -d '{"flight_id": "UA123"}'

# Response (401 Unauthorized):
# {
#   "error": "invalid_token",
#   "error_description": "The provided agent token is invalid or expired",
#   "error_code": 4010,
#   "timestamp": "2024-01-15T10:50:00Z"
# }

# Rate limit exceeded example
curl -X POST https://example.com/ai/search \
  -H "Authorization: Bearer valid_token"

# Response (429 Too Many Requests):
# {
#   "error": "rate_limit_exceeded",
#   "error_description": "Rate limit exceeded for this agent",
#   "error_code": 4291,
#   "details": {
#     "limit": 100,
#     "remaining": 0,
#     "resetAt": "2024-01-15T11:00:00Z",
#     "retryAfter": 300
#   }
# }
```

### Security Validation

```bash
# Verify token signature (conceptual - for site implementers)
# 1. Extract JWT header and payload
# 2. Verify signature using agent's public key
# 3. Check token expiration
# 4. Validate nonce was issued by this site
# 5. Ensure scopes match requested permissions

# Example token payload (decoded):
# {
#   "iss": "https://example.com",
#   "sub": "agent-12345",
#   "aud": "ai-api",
#   "exp": 1705317600,
#   "iat": 1705314000,
#   "scopes": ["search", "content", "booking"],
#   "nonce_hash": "sha256_of_original_nonce",
#   "rate_limits": {
#     "requests_per_hour": 100,
#     "burst_limit": 10
#   }
# }
```

This complete cURL flow demonstrates the full ARW-P authentication and API usage pattern, including both agent identity verification and user delegation for sensitive operations.
