# 🤖 ARW-P: Agent-Ready Web Protocol

**The future-ready protocol that bridges AI agents and web services**

*Enabling seamless AI-to-web interactions without compromising human experiences*

![Version](https://img.shields.io/badge/version-1.0-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Status](https://img.shields.io/badge/status-Beta-orange.svg)

---

## 🚀 What is ARW-P?

**ARW-P** (pronounced "R-Web-P") is an open standard protocol that empowers websites to expose dedicated, high-performance lanes for AI agents while preserving the optimal human user experience. Think of it as creating a "fast lane" for bots alongside the regular web traffic.

### 🎯 Key Benefits

**🔍 Structured Data**
- Reduces AI hallucinations with precise, typed responses
- Eliminates HTML parsing complexity
- Provides consistent, machine-readable formats

**⚡ Performance**
- 10x cheaper bandwidth compared to full HTML rendering
- Millisecond response times for agent queries
- Efficient token-based authentication

**🛡️ Security & Control**
- Documented, scoped API endpoints
- Rate limiting and access controls
- Audit trails for all agent interactions

**🌐 Universal Compatibility**
- Works alongside existing web infrastructure
- No changes to human-facing pages
- Progressive enhancement approach

---

## 🏗️ Architecture Overview

ARW-P creates a parallel interaction layer that coexists with your existing web presence:

```
┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐
│   Traditional Web   │    │    ARW-P Layer      │    │   Your Website      │
│                     │    │                     │    │                     │
│ 👤 Human User       │    │ 🤖 AI Agent        │    │ 🖥️ Web Server       │
│ 🌐 Web Browser     │────│ ⚡ ARW-P Endpoints  │────│ 🗄️ Database         │
│ 📄 HTML Pages      │    │ 🔍 Discovery Files │    │ 🔌 Existing APIs   │
└─────────────────────┘    └─────────────────────┘    └─────────────────────┘
```

**Flow:**
1. Humans use regular web browsers and HTML pages
2. AI agents use ARW-P endpoints and discovery files  
3. Both paths connect to the same web server and data

---

## 👥 Core Actors & Trust Model

| Actor | Role & Responsibilities |
|-------|------------------------|
| **🏢 Site Host** | • Publishes discovery files at `/.well-known/`<br>• Issues time-limited JWT tokens<br>• Defines available endpoints and scopes |
| **🤖 Agent Provider** | • Supplies cryptographic public keys<br>• Respects documented rate limits<br>• Follows endpoint specifications |
| **🌐 Edge Gateway** *(optional)* | • Provides additional authentication layers<br>• Implements advanced rate limiting<br>• Shapes and caches responses |
| **👤 Human Visitor** | • Continues using normal web interface<br>• Unaffected by agent interactions<br>• May benefit from agent-enhanced features |

---

## 📋 Required Components (v1.0)

### Core Discovery Files

| Endpoint | HTTP Method | Purpose | Required Fields |
|----------|-------------|---------|-----------------|
| `/.well-known/ai-token` | `GET` + `POST` | Agent identity token exchange | `nonce`, `tokenEndpoint` |
| `/.well-known/user-delegate` | `POST` | User delegation request | `user_id`, `scopes`, `callback_url` |
| `/.well-known/user-token` | `POST` | User token exchange | `delegation_request_id`, `authorization_code` |
| `/.well-known/agents.json` | `GET` | Capability discovery | `specVersion`, `endpoints`, `scopes` |

### Content Endpoints

| Pattern | Purpose | Content Type |
|---------|---------|--------------|
| `/ai/<pageId>.json` | Page-specific structured data | `application/json` |
| `/ai/search` | Natural language search interface | `application/json` |
| `/ai/search/semantic` | Vector-based semantic search | `application/json` |
| `/ai/memory/store` | Agent conversation context storage | `application/json` |
| `/ai/memory/retrieve` | Agent conversation context retrieval | `application/json` |
| `/ai/stream/*` *(optional)* | Real-time updates via Server-Sent Events | `text/event-stream` |

---

## ⚡ Dynamic Content & Real-time Features

ARW-P supports advanced features for dynamic, time-sensitive content that changes frequently.

### 📡 Server-Sent Events (SSE) for Live Updates

For real-time content like flash sales, inventory changes, or dynamic pricing:

```javascript
// Agent subscribes to real-time updates
const eventSource = new EventSource('https://example.com/ai/stream/offers', {
    headers: {
        'Authorization': 'Bearer ' + agentToken
    }
});

eventSource.onmessage = function(event) {
    const update = JSON.parse(event.data);
    console.log('New offer:', update);
};
```

**Server-side SSE implementation:**
```javascript
app.get('/ai/stream/offers', authenticateToken, (req, res) => {
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*'
    });

    // Send initial data
    res.write(`data: ${JSON.stringify({
        type: 'connected',
        timestamp: Date.now()
    })}\n\n`);

    // Listen for flash sales or inventory updates
    const offerListener = (offer) => {
        res.write(`data: ${JSON.stringify({
            type: 'flash_sale',
            offer: {
                product_id: offer.product_id,
                discount: offer.discount,
                expires_at: offer.expires_at,
                inventory_remaining: offer.stock
            },
            timestamp: Date.now()
        })}\n\n`);
    };

    // Subscribe to real-time offer events
    eventEmitter.on('flash_offer', offerListener);

    // Cleanup on disconnect
    req.on('close', () => {
        eventEmitter.off('flash_offer', offerListener);
    });
});
```

### 🔍 Vector Indexing for Semantic Search

Advanced implementations can include vector search capabilities:

```json
{
  "endpoints": [
    {
      "path": "/ai/search/semantic",
      "method": "POST",
      "scope": "semantic_search",
      "description": "Vector-based semantic search using embeddings",
      "parameters": {
        "query": {
          "type": "string",
          "description": "Natural language search query"
        },
        "embedding": {
          "type": "array",
          "description": "Pre-computed query embedding vector (optional)"
        },
        "filters": {
          "type": "object",
          "description": "Metadata filters (category, price, etc.)"
        },
        "similarity_threshold": {
          "type": "number",
          "default": 0.7,
          "description": "Minimum similarity score (0-1)"
        }
      }
    }
  ]
}
```

**Semantic search response:**
```json
{
  "query": "comfortable hiking boots for winter",
  "embedding_model": "text-embedding-ada-002",
  "results": [
    {
      "id": "prod_456",
      "title": "Insulated Mountain Boots",
      "similarity_score": 0.94,
      "vector_distance": 0.06,
      "metadata": {
        "category": "footwear",
        "season": "winter",
        "features": ["insulated", "waterproof", "hiking"]
      }
    }
  ],
  "search_metadata": {
    "total_vectors_searched": 50000,
    "search_time_ms": 12,
    "index_version": "v2.1"
  }
}
```

### 🧠 Persistent Memory Agents

Support for agents that maintain conversation context across sessions:

```json
{
  "endpoints": [
    {
      "path": "/ai/memory/store",
      "method": "POST",
      "scope": "memory",
      "description": "Store conversation context and preferences",
      "requires_user": true,
      "user_scopes": ["memory_storage"]
    },
    {
      "path": "/ai/memory/retrieve",
      "method": "GET",
      "scope": "memory", 
      "description": "Retrieve stored conversation context",
      "requires_user": true,
      "user_scopes": ["memory_access"]
    }
  ]
}
```

**Memory storage example:**
```bash
curl -X POST https://example.com/ai/memory/store \
  -H "Authorization: Bearer <AGENT_TOKEN>" \
  -H "X-User-Token: Bearer <USER_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": "conv_789",
    "context": {
      "user_preferences": {
        "price_range": "100-200",
        "preferred_brands": ["Nike", "Adidas"],
        "size": "10",
        "activity": "running"
      },
      "search_history": [
        "running shoes under $150",
        "Nike Air Max reviews"
      ],
      "cart_items": ["prod_123"],
      "session_start": "2024-01-15T10:00:00Z"
    },
    "expires_at": "2024-01-22T10:00:00Z"
  }'
```

### 🔔 Push Notifications for Agents

Webhook-style notifications for important events:

```json
{
  "webhooks": {
    "inventory_alerts": {
      "endpoint": "https://agent-provider.com/webhooks/inventory",
      "events": ["out_of_stock", "back_in_stock", "low_inventory"],
      "filters": {
        "product_categories": ["electronics", "apparel"],
        "price_threshold": 100
      }
    },
    "price_changes": {
      "endpoint": "https://agent-provider.com/webhooks/pricing",
      "events": ["price_drop", "sale_started", "sale_ending"],
      "user_specific": true
    }
  }
}
```

---

## 🎨 Implementation Examples

### Basic Discovery Configuration

Create your `/.well-known/agents.json`:

```json
{
  "$schema": "https://arw.dev/schemas/agents-1.0.json",
  "specVersion": "1.0",
  "meta": {
    "name": "My Website API",
    "description": "AI-friendly access to our content and services",
    "version": "1.0.0",
    "contact": {
      "email": "api@mywebsite.com",
      "url": "https://mywebsite.com/api-docs"
    }
  },
  "authentication": {
    "required": true,
    "schemes": ["bearer"],
    "tokenTtl": 3600,
    "userDelegation": {
      "supported": true,
      "maxSessionDuration": 7200,
      "supportedScopes": ["booking", "payments", "profile", "preferences"]
    }
  },
  "rateLimits": {
    "default": {
      "requests": 100,
      "windowMs": 60000
    },
    "search": {
      "requests": 20,
      "windowMs": 60000
    },
    "user_actions": {
      "requests": 10,
      "windowMs": 60000
    }
  },
  "endpoints": [
    {
      "path": "/ai/search",
      "method": "POST",
      "scope": "search",
      "description": "Semantic search across site content",
      "parameters": {
        "q": {
          "type": "string",
          "required": true,
          "description": "Search query in natural language"
        },
        "limit": {
          "type": "integer",
          "default": 10,
          "max": 50
        }
      }
    },
    {
      "path": "/ai/search/semantic",
      "method": "POST", 
      "scope": "semantic_search",
      "description": "Vector-based semantic search using embeddings",
      "parameters": {
        "query": {
          "type": "string",
          "required": true
        },
        "similarity_threshold": {
          "type": "number",
          "default": 0.7
        }
      }
    },
    {
      "path": "/ai/articles/{id}.json",
      "method": "GET",
      "scope": "content",
      "description": "Structured article content",
      "parameters": {
        "id": {
          "type": "string",
          "required": true,
          "description": "Article identifier"
        }
      }
    },
    {
      "path": "/ai/bookings/create",
      "method": "POST",
      "scope": "booking",
      "description": "Create a new booking (requires user delegation)",
      "requires_user": true,
      "user_scopes": ["booking", "payments"],
      "parameters": {
        "service_type": {
          "type": "string",
          "enum": ["flight", "hotel", "car"],
          "required": true
        }
      }
    },
    {
      "path": "/ai/memory/store",
      "method": "POST",
      "scope": "memory",
      "description": "Store conversation context and preferences",
      "requires_user": true,
      "user_scopes": ["memory_storage"]
    },
    {
      "path": "/ai/stream/offers",
      "method": "GET",
      "scope": "streaming",
      "description": "Real-time offers via Server-Sent Events",
      "content_type": "text/event-stream"
    }
  ],
  "scopes": {
    "search": "Search site content and metadata",
    "semantic_search": "Advanced vector-based search capabilities",
    "content": "Access structured content data",
    "booking": "Create and manage bookings (user delegation required)",
    "memory": "Store and retrieve agent conversation context",
    "streaming": "Subscribe to real-time content updates",
    "analytics": "Read aggregated usage statistics"
  },
  "features": {
    "realtime_updates": true,
    "persistent_memory": true,
    "user_delegation": true,
    "semantic_search": true
  }
}
```

### Search Endpoint Implementation

Example `/ai/search` response:

```json
{
  "query": "machine learning tutorials",
  "took": 23,
  "total": 127,
  "results": [
    {
      "id": "ml-intro-2024",
      "title": "Introduction to Machine Learning",
      "url": "/articles/machine-learning-intro",
      "snippet": "A comprehensive guide to getting started with ML concepts, algorithms, and practical applications.",
      "relevance": 0.95,
      "metadata": {
        "author": "Dr. Jane Smith",
        "publishDate": "2024-01-15",
        "tags": ["machine-learning", "tutorial", "beginner"],
        "readTime": "15 min"
      }
    }
  ],
  "facets": {
    "categories": [
      {"name": "Tutorials", "count": 45},
      {"name": "Research", "count": 32},
      {"name": "Tools", "count": 28}
    ]
  }
}
```

---

## 🛠️ Quick Start Guide

### 1. Setup Discovery Files

```bash
# Create the well-known directory
mkdir -p .well-known

# Add to your web server configuration
# Nginx example:
location /.well-known/ {
    add_header Access-Control-Allow-Origin *;
    add_header Content-Type application/json;
}
```

### 2. Implement Token Exchange

```javascript
// Example Node.js implementation
app.get('/.well-known/ai-token', (req, res) => {
    const nonce = generateSecureNonce();
    const challenge = {
        nonce,
        tokenEndpoint: 'https://yoursite.com/.well-known/ai-token',
        expiresAt: Date.now() + 300000 // 5 minutes
    };
    
    // Store nonce temporarily
    redis.setex(`nonce:${nonce}`, 300, JSON.stringify(challenge));
    
    res.json(challenge);
});

app.post('/.well-known/ai-token', async (req, res) => {
    const { nonce, proof } = req.body;
    
    // Verify the signature
    const isValid = await verifyAgentSignature(nonce, proof);
    
    if (isValid) {
        const token = jwt.sign(
            { scope: 'search,content', iat: Date.now() },
            JWT_SECRET,
            { expiresIn: '1h' }
        );
        
        res.json({ token, expiresIn: 3600 });
    } else {
        res.status(401).json({ error: 'Invalid signature' });
    }
});
```

### 3. Create Content Endpoints

```javascript
app.post('/ai/search', authenticateToken, (req, res) => {
    const { q, limit = 10 } = req.body;
    
    // Implement your search logic
    const results = searchContent(q, limit);
    
    res.json({
        query: q,
        took: 42,
        total: results.total,
        results: results.items.map(item => ({
            title: item.title,
            url: item.url,
            snippet: item.summary,
            relevance: item.score,
            metadata: {
                author: item.author,
                publishDate: item.date,
                tags: item.tags
            }
        }))
    });
});
```

---

## 📊 Use Cases & Examples

### E-commerce Integration

```json
{
  "endpoints": [
    {
      "path": "/ai/products/search",
      "method": "POST",
      "scope": "catalog",
      "description": "Search product catalog with natural language"
    },
    {
      "path": "/ai/products/{id}",
      "method": "GET", 
      "scope": "catalog",
      "description": "Get structured product information"
    },
    {
      "path": "/ai/inventory/check",
      "method": "POST",
      "scope": "inventory",
      "description": "Check real-time availability"
    }
  ]
}
```

### Content Management System

```json
{
  "endpoints": [
    {
      "path": "/ai/articles/search",
      "method": "POST",
      "scope": "content",
      "description": "Semantic article search"
    },
    {
      "path": "/ai/articles/{slug}",
      "method": "GET",
      "scope": "content", 
      "description": "Structured article content"
    },
    {
      "path": "/ai/categories",
      "method": "GET",
      "scope": "taxonomy",
      "description": "Content categorization data"
    }
  ]
}
```

---

## 🤝 Community & Support

### Getting Help

- 📖 **Documentation**: [Full API Reference](flows.md)
- 💬 **Community Forum**: [ARW-P Discussions](https://github.com/arwproject/arw-p/discussions)
- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/arwproject/arw-p/issues)
- 📧 **Email Support**: [contact@arw.dev](mailto:contact@arw.dev)

### Contributing

We welcome contributions! Areas we need help with:

- 🔧 Code contributions and implementations
- 📝 Documentation improvements  
- 🧪 Testing and validation
- 💡 Feature proposals and feedback

### Roadmap

- **v1.1** - Enhanced streaming capabilities
- **v1.2** - Advanced authentication methods
- **v2.0** - Production stability guarantee

---

**Ready to enable AI-native interactions on your website?**

[Get Started →](flows.md) • [View Examples →](https://github.com/arwproject/arw-p-examples) • [Join Community →](https://github.com/arwproject/arw-p/discussions)

---

*ARW-P is an open standard maintained by the community*
