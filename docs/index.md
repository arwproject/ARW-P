# 🤖 ARW-P: Agent-Ready Web Protocol

**The future-ready protocol that bridges AI agents and web services**

*Enabling seamless AI-to-web interactions without compromising human experiences*

![Version](https://img.shields.io/badge/version-0.1-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Status](https://img.shields.io/badge/status-Beta-orange.svg)

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

## 📋 Required Components (v0.1)

### Core Discovery Files

| Endpoint | HTTP Method | Purpose | Required Fields |
|----------|-------------|---------|-----------------|
| `/.well-known/ai-token` | `GET` + `POST` | Token exchange & authentication | `nonce`, `tokenEndpoint` |
| `/.well-known/agents.json` | `GET` | Capability discovery | `specVersion`, `endpoints`, `scopes` |

### Content Endpoints

| Pattern | Purpose | Content Type |
|---------|---------|--------------|
| `/ai/<pageId>.json` | Page-specific structured data | `application/json` |
| `/ai/search` | Natural language search interface | `application/json` |
| `/ai/stream/*` *(optional)* | Real-time updates via Server-Sent Events | `text/event-stream` |

---

## 🎨 Implementation Examples

### Basic Discovery Configuration

Create your `/.well-known/agents.json`:

```json
{
  "$schema": "https://arw.dev/schemas/agents-0.1.json",
  "specVersion": "0.1",
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
    "tokenTtl": 3600
  },
  "rateLimits": {
    "default": {
      "requests": 100,
      "windowMs": 60000
    },
    "search": {
      "requests": 20,
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
    }
  ],
  "scopes": {
    "search": "Search site content and metadata",
    "content": "Access structured content data",
    "analytics": "Read aggregated usage statistics"
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

- **v0.2** - Enhanced streaming capabilities
- **v0.3** - Advanced authentication methods
- **v1.0** - Production stability guarantee

---

**Ready to enable AI-native interactions on your website?**

[Get Started →](flows.md) • [View Examples →](https://github.com/arwproject/arw-p-examples) • [Join Community →](https://github.com/arwproject/arw-p/discussions)

---

*ARW-P is an open standard maintained by the community*
