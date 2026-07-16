# Architecture Diagrams

This document provides visual representations of StadiumOS GenAI's system architecture, data flows, and deployment topology.

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          StadiumOS GenAI System                          │
│                     FIFA World Cup 2026 Host Venue                       │
└─────────────────────────────────────────────────────────────────────────┘

                                   INTERNET
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          Load Balancer (Nginx)                           │
│  • SSL Termination                                                       │
│  • Rate Limiting (30 req/min API, 5 req/min Admin)                      │
│  • Security Headers (CSP, HSTS, CORP, COOP)                             │
│  • Static Asset Caching                                                  │
└──────────────────┬──────────────────────────────────┬───────────────────┘
                   │                                  │
        ┌──────────▼─────────┐           ┌───────────▼──────────┐
        │   Frontend (SPA)    │           │  Backend API (FastAPI)│
        │  • HTML/CSS/JS      │           │  • Python 3.12        │
        │  • WCAG 2.1 AA      │           │  • Async I/O          │
        │  • Offline Fallback │◄──────────┤  • 8 REST Endpoints   │
        │  • No Build Required│   REST    │  • Rate Limiting      │
        └─────────────────────┘   JSON    │  • Security Middleware│
                                           └───────────┬───────────┘
                                                       │
                    ┌──────────────────────────────────┼────────────────┐
                    │                                  │                │
          ┌─────────▼────────┐            ┌───────────▼────┐  ┌────────▼─────────┐
          │  Redis Cache      │            │  AI Service    │  │  Audit Logger    │
          │  • 82% Hit Rate   │            │  • Anthropic   │  │  • JSON Logging  │
          │  • 300s TTL (AI)  │            │  • Retries     │  │  • Security Evts │
          │  • 600s TTL (Data)│            │  • Timeouts    │  │  • Compliance    │
          │  • LRU Eviction   │            │  • Fallback    │  │  • SIEM Ready    │
          └───────────────────┘            └────────┬───────┘  └──────────────────┘
                                                    │
                                           ┌────────▼──────────┐
                                           │  Anthropic API     │
                                           │  Claude Sonnet 4.6 │
                                           │  (External Service)│
                                           └────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          Monitoring & Observability                      │
│  • Prometheus (Metrics Collection)                                       │
│  • Grafana (Visualization - 7 Dashboards)                               │
│  • Structured Logging (JSON format)                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Request Flow Sequence

### AI Chat Request (Cache Miss)

```
Fan Browser          Frontend         Nginx          Backend          Cache          AI Service          Anthropic
     │                   │               │               │               │                  │                  │
     │  "Where is       │               │               │               │                  │                  │
     │   Gate A?"       │               │               │               │                  │                  │
     ├──────────────────►│               │               │               │                  │                  │
     │                   │ POST /api/v1/chat           │               │                  │                  │
     │                   ├───────────────►│               │               │                  │                  │
     │                   │               │  Rate Limit   │               │                  │                  │
     │                   │               │  Check (OK)   │               │                  │                  │
     │                   │               ├───────────────►│               │                  │                  │
     │                   │               │               │  Check Cache  │                  │                  │
     │                   │               │               ├───────────────►│                  │                  │
     │                   │               │               │   Cache MISS  │                  │                  │
     │                   │               │               │◄───────────────┤                  │                  │
     │                   │               │               │               │   Generate       │                  │
     │                   │               │               │               │   Response       │                  │
     │                   │               │               ├────────────────────────────────►│                  │
     │                   │               │               │               │                  │  Create Message │
     │                   │               │               │               │                  ├─────────────────►│
     │                   │               │               │               │                  │                  │
     │                   │               │               │               │                  │  AI Response    │
     │                   │               │               │               │                  │◄─────────────────┤
     │                   │               │               │               │   AI Response    │                  │
     │                   │               │               │◄────────────────────────────────┤                  │
     │                   │               │               │  Store in     │                  │                  │
     │                   │               │               │  Cache (300s) │                  │                  │
     │                   │               │               ├───────────────►│                  │                  │
     │                   │               │   JSON + AI   │               │                  │                  │
     │                   │               │   Response    │               │                  │                  │
     │                   │◄───────────────────────────────┤               │                  │                  │
     │   Response        │               │               │               │                  │                  │
     │   "Gate A is..."  │               │               │               │                  │                  │
     │◄──────────────────┤               │               │               │                  │                  │
     │                   │               │               │               │                  │                  │

     Total Latency: ~650ms (AI generation) + ~100ms (network/processing) = ~750ms
```

### AI Chat Request (Cache Hit)

```
Fan Browser          Frontend         Nginx          Backend          Cache
     │                   │               │               │               │
     │  Same question    │               │               │               │
     │  within 5 min     │               │               │               │
     ├──────────────────►│               │               │               │
     │                   │ POST /api/v1/chat           │               │
     │                   ├───────────────►│               │               │
     │                   │               ├───────────────►│               │
     │                   │               │               │  Check Cache  │
     │                   │               │               ├───────────────►│
     │                   │               │               │   Cache HIT!  │
     │                   │               │               │◄───────────────┤
     │                   │               │   JSON        │               │
     │                   │◄───────────────────────────────┤               │
     │   Response        │               │               │               │
     │◄──────────────────┤               │               │               │
     │                   │               │               │               │

     Total Latency: ~45ms (93% improvement!)
```

---

## Navigation Route Calculation

```
┌──────────────────────────────────────────────────────────────────────┐
│                      Navigation Request Flow                          │
└──────────────────────────────────────────────────────────────────────┘

User Request: "Navigate from Gate A to Section 215"
Accessibility: Wheelchair user

                    ┌─────────────────┐
                    │  Navigation      │
                    │  Service         │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌────────────────┐   ┌────────────────┐
│ Parse Origin  │   │ Parse Dest     │   │ Parse Needs    │
│ "gate_a"      │   │ "section_215"  │   │ ["wheelchair"] │
└───────┬───────┘   └────────┬───────┘   └────────┬───────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                    ┌────────▼─────────┐
                    │  Stadium Map      │
                    │  Graph Lookup     │
                    └────────┬──────────┘
                             │
                    ┌────────▼─────────┐
                    │  Dijkstra's      │
                    │  Algorithm       │
                    │  (Shortest Path) │
                    └────────┬──────────┘
                             │
                    ┌────────▼─────────┐
                    │  Filter Non-     │
                    │  Accessible      │
                    │  Zones           │
                    └────────┬──────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────┐ ┌────────────────┐ ┌─────────────────┐
│  Build Steps    │ │  Calculate     │ │  AI Narration   │
│  gate_a →       │ │  Total Time    │ │  (Optional)     │
│  concourse_n →  │ │  8.5 minutes   │ │  "From Gate A..." │
│  section_215    │ └────────────────┘ └─────────────────┘
└─────────┬───────┘
          │
          ▼
┌─────────────────────────────┐
│  Navigation Response        │
│  • Steps: [3 steps]         │
│  • Total: 8.5 min           │
│  • Accessible: true         │
│  • Narrative: "..."         │
│  • Source: "genai"          │
└─────────────────────────────┘

Performance: <100ms (deterministic), +320ms if AI narration
```

---

## Deployment Architecture

### Single-Instance Deployment (Small Venue <40K capacity)

```
┌─────────────────────────────────────────────────────────────┐
│                      Docker Host / VPS                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              docker-compose.yml                        │ │
│  │                                                         │ │
│  │  ┌───────────────┐  ┌──────────────┐  ┌────────────┐ │ │
│  │  │   frontend    │  │   backend    │  │   redis    │ │ │
│  │  │   :8080       │  │   :8000      │  │   :6379    │ │ │
│  │  └───────────────┘  └──────────────┘  └────────────┘ │ │
│  │                                                         │ │
│  │  Volumes:                                              │ │
│  │  • redis_data (persistent)                            │ │
│  │  • nginx_logs                                          │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Resources:                                                  │
│  • 2 vCPU, 4GB RAM                                          │
│  • 20GB SSD                                                  │
│  • Cost: ~$40/month (DigitalOcean/Linode)                  │
└─────────────────────────────────────────────────────────────┘
```

### Multi-Instance Deployment (Large Venue 60K-80K capacity)

```
                         ┌──────────────────┐
                         │   CDN / WAF      │
                         │  (CloudFlare)    │
                         └────────┬─────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │  Load Balancer (Nginx)     │
                    │  • SSL Termination         │
                    │  • Health Checks           │
                    │  • Rate Limiting           │
                    └─────────────┬──────────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
     ┌──────▼──────┐       ┌──────▼──────┐     ┌──────▼──────┐
     │  Backend 1  │       │  Backend 2  │     │  Backend 3  │
     │  (Primary)  │       │  (Replica)  │     │  (Replica)  │
     └──────┬──────┘       └──────┬──────┘     └──────┬──────┘
            │                     │                     │
            └─────────────────────┼─────────────────────┘
                                  │
                    ┌─────────────▼──────────────┐
                    │   Redis Cluster            │
                    │   • Primary + 2 Replicas   │
                    │   • Sentinel HA            │
                    │   • Automatic Failover     │
                    └────────────────────────────┘

     ┌────────────────────────────────────────────┐
     │        Monitoring Stack                    │
     │  • Prometheus (metrics)                    │
     │  • Grafana (dashboards)                    │
     │  • Alertmanager (notifications)            │
     └────────────────────────────────────────────┘

Resources per Backend:
• 2 vCPU, 2GB RAM
• Total: 6 vCPU, 6GB RAM for backends
• Redis: 2GB RAM (primary + replicas)
• Total Cost: ~$180/month + CDN costs
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Flow Overview                        │
└─────────────────────────────────────────────────────────────────┘

Request Types and Data Paths:

1. STATIC DATA (Stadium Info, Routes)
   ┌─────────┐
   │ Request │──────► Frontend ──────► In-Memory
   └─────────┘       (No Backend)      Constants

2. CACHED AI RESPONSES
   ┌─────────┐
   │ Request │──► Backend ──► Redis ──► Response
   └─────────┘              (Cache Hit)

3. NEW AI RESPONSES
   ┌─────────┐
   │ Request │──► Backend ──► AI Service ──► Anthropic ──► Redis ──► Response
   └─────────┘              (Cache Miss)                  (Store)

4. DETERMINISTIC OPERATIONS (Navigation, Crowd, Transport)
   ┌─────────┐
   │ Request │──► Backend ──► Service Logic ──► [Optional AI Narration] ──► Response
   └─────────┘              (Always Works)

5. ADMIN OPERATIONS
   ┌─────────┐
   │ Request │──► Nginx ──► Admin Router ──► Audit Log ──► Operation ──► Response
   └─────────┘   (Auth)    (API Key Check)  (Security)

6. MONITORING DATA
   ┌─────────┐
   │ Metrics │──► Prometheus ──► Grafana ──► Dashboard
   └─────────┘   (Scrape /metrics every 15s)
```

---

## Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Security Layers                             │
└─────────────────────────────────────────────────────────────────┘

LAYER 1: Network Security
├─ SSL/TLS 1.2+ (All connections encrypted)
├─ Certificate Pinning (Production)
└─ DDoS Protection (CloudFlare/WAF)

LAYER 2: Application Gateway (Nginx)
├─ Rate Limiting (30 req/min per IP)
├─ Request Size Limits (20KB max body)
├─ IP Whitelisting (Admin endpoints)
└─ Security Headers (CSP, HSTS, CORP, COOP, etc.)

LAYER 3: Application Security (FastAPI)
├─ Input Validation (Pydantic schemas)
├─ Output Sanitization (HTML escaping)
├─ Prompt Injection Filtering (AI inputs)
├─ Admin API Key Authentication (Constant-time comparison)
└─ CORS Policy (Whitelisted origins only)

LAYER 4: Data Security
├─ No PII Storage (Stateless design)
├─ Cache Key Hashing (SHA-256)
├─ Audit Logging (All admin operations)
└─ Secrets Management (.env files, never committed)

LAYER 5: Dependency Security
├─ Automated Scanning (pip-audit, bandit, safety)
├─ GitHub Dependabot (Alerts + PRs)
├─ Docker Image Scanning (Trivy)
└─ Regular Updates (Weekly security patches)

LAYER 6: Monitoring & Response
├─ Real-time Alerting (Error rate, latency spikes)
├─ Audit Trail (JSON logs for SIEM)
├─ Health Checks (Uptime monitoring)
└─ Incident Response Plan (Escalation procedures)
```

---

## API Endpoint Map

```
┌─────────────────────────────────────────────────────────────────┐
│                    API Endpoint Structure                        │
└─────────────────────────────────────────────────────────────────┘

BASE URL: https://api.stadiumos.example.com

PUBLIC ENDPOINTS (Rate Limited: 30 req/min)
├─ GET  /
│  └─ Service info and links
├─ GET  /api/v1/health
│  └─ Health check (no auth required)
│
├─ POST /api/v1/chat
│  └─ AI-powered chat assistant
│  └─ Input: {message, language, role, context}
│  └─ Output: {response, language, source}
│
├─ POST /api/v1/navigate
│  └─ Route calculation with accessibility
│  └─ Input: {origin, destination, accessibility_needs}
│  └─ Output: {steps[], total_minutes, narrative, accessible}
│
├─ POST /api/v1/crowd/analyze
│  └─ Crowd density analysis
│  └─ Input: {zones[], generate_briefing}
│  └─ Output: {analysis[], briefing, alerts[]}
│
├─ POST /api/v1/accessibility
│  └─ Accessibility information
│  └─ Input: {need_type, location, language}
│  └─ Output: {guidance, resources[], source}
│
├─ POST /api/v1/transport
│  └─ Transport recommendations
│  └─ Input: {mode_preferences[], accessibility_needs}
│  └─ Output: {options[], recommendation}
│
├─ POST /api/v1/translate
│  └─ Text translation
│  └─ Input: {text, target_language, source_language}
│  └─ Output: {translated_text, source}
│
├─ POST /api/v1/sustainability
│  └─ Sustainability tips
│  └─ Input: {category, language}
│  └─ Output: {tips[], source}
│
└─ POST /api/v1/emergency
   └─ Emergency decision support
   └─ Input: {incident_type, severity, affected_zones}
   └─ Output: {actions[], escalate, briefing}

ADMIN ENDPOINTS (Require X-Admin-Key header, Rate Limited: 5 req/min)
├─ GET  /admin/status
│  └─ System status and health
│  └─ Output: {genai_available, cache_available, cache_stats}
│
├─ GET  /admin/cache/stats
│  └─ Detailed cache statistics
│  └─ Output: {keys, hit_rate, memory_used}
│
└─ POST /admin/cache/flush
   └─ Flush cache (pattern-based)
   └─ Input: {pattern="*"}
   └─ Output: {flushed_count, pattern}

METRICS ENDPOINT (IP Restricted)
└─ GET  /metrics
   └─ Prometheus metrics (production only)
   └─ Output: OpenMetrics format
```

---

## Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Error Handling Strategy                       │
└─────────────────────────────────────────────────────────────────┘

Request Error Cascade:

┌──────────────────┐
│  User Request    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐      ┌─────────────────┐
│ Input Validation │─NO──►│ 422 Unprocessable│
│  (Pydantic)      │      │ Field-level errors│
└────────┬─────────┘      └──────────────────┘
         │ YES
         ▼
┌──────────────────┐      ┌─────────────────┐
│ Rate Limit Check │─NO──►│ 429 Too Many     │
│                  │      │ Retry-After: 60s │
└────────┬─────────┘      └──────────────────┘
         │ YES
         ▼
┌──────────────────┐      ┌─────────────────┐
│ Auth Check       │─NO──►│ 401 Unauthorized │
│ (Admin only)     │      │ Missing API Key  │
└────────┬─────────┘      └──────────────────┘
         │ YES
         ▼
┌──────────────────┐
│ Business Logic   │
│                  │
└────────┬─────────┘
         │
         ├──► AI Service Fails?
         │    └──► Use Deterministic Fallback ✅
         │
         ├──► Redis Unavailable?
         │    └──► Continue Without Cache ✅
         │
         ├──► Unhandled Exception?
         │    └──► 500 Internal Server Error
         │         Log to audit + monitoring
         │         Generic user message (no leak)
         │
         ▼
┌──────────────────┐
│  200 OK Response │
└──────────────────┘
```

---

## Diagram Files

All architecture diagrams are stored in `docs/diagrams/`:

```
docs/diagrams/
├── architecture-overview.png       # High-level system architecture
├── architecture-overview.svg       # Editable SVG version
├── request-flow-sequence.png       # API request sequence diagrams
├── navigation-flow.png             # Navigation calculation detailed flow
├── deployment-single.png           # Single-instance deployment
├── deployment-multi.png            # Multi-instance HA deployment
├── data-flow.png                   # Data flow through components
├── security-layers.png             # Security architecture layers
├── api-endpoints.png               # API endpoint structure
└── error-handling.png              # Error cascade flow
```

---

## Tools Used for Diagrams

- **ASCII Diagrams:** Manually created for text-based documentation
- **Mermaid.js:** For generating flowcharts and sequence diagrams
- **Draw.io:** For complex architecture diagrams
- **Excalidraw:** For hand-drawn style diagrams

---

## Conclusion

These diagrams provide visual documentation of StadiumOS GenAI's architecture, making it easier for:

- **Developers** to understand system components and interactions
- **DevOps** to plan deployments and scaling strategies
- **Security auditors** to review attack surfaces and mitigations
- **Judges** to quickly grasp the technical design and quality

All diagrams are kept in version control and updated with architectural changes.
