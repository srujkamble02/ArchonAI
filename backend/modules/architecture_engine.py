"""
architecture_engine.py
Pure rule-based architecture decision engine.
NO LLM involvement — deterministic logic only.
"""

from typing import Any


# ── Rule thresholds ──────────────────────────────────────────────────────────
MICROSERVICES_SCALE   = 100_000
SERVERLESS_MAX_SCALE  = 50_000
MONOLITHIC_MAX_SCALE  = 20_000


def decide_architecture(features: dict) -> dict:
    scale         = features.get("scale", 10_000)
    real_time     = features.get("real_time", False)
    ai_required   = features.get("ai_required", False)
    iot           = features.get("iot", False)
    platform      = features.get("platform", "web")
    payments      = features.get("payments", False)
    security      = features.get("security_critical", False)
    ms_hint       = features.get("microservices_hint", False)
    edge_offline  = features.get("edge_offline", False)
    multi_context = features.get("multi_context", False)

    arch, confidence, reason, tradeoffs = _apply_rules(
        scale, real_time, ai_required, iot, platform, payments, security, ms_hint, edge_offline, multi_context
    )

    components   = _select_components(arch, features)
    integrations = _select_integrations(features)
    security_recs = _security_recommendations(features)
    reasoning_details = _build_reasoning_details(features, arch)
    alternatives      = _build_alternatives(arch)
    constraint_analysis = _validate_constraints(features, arch)
    ui_ux = _build_ui_ux(features)
    tradeoff_analysis = _build_tradeoffs(features, arch)

    return {
        "architecture":      arch,
        "confidence":        confidence,
        "reason":            reason,
        "tradeoffs":         tradeoffs,
        "components":        components,
        "integrations":      integrations,
        "security":          security_recs,
        "reasoning_details": reasoning_details,
        "alternatives":      alternatives,
        "constraint_analysis": constraint_analysis,
        "ui_ux":             ui_ux,
        "tradeoff_analysis": tradeoff_analysis,
    }

def _build_tradeoffs(features: dict, arch: str) -> list:
    tradeoffs = []
    real_time = features.get("real_time", False)
    edge_off = features.get("edge_offline", False)
    multi_context = features.get("multi_context", False)
    scale = features.get("scale", 0)
    
    if edge_off or multi_context:
        tradeoffs.append({
            "dimension": "Consistency vs Availability (CAP Theorem)",
            "decision": "Prioritizing Availability & Partition Tolerance.",
            "justification": "In offline/edge environments, network partitions are guaranteed. We must allow local reads/writes (Availability) and resolve conflicts later (Eventual Consistency), rather than blocking the UI waiting for the cloud."
        })
        
    if real_time and (edge_off or multi_context):
        tradeoffs.append({
            "dimension": "Real-time vs Offline Constraints",
            "decision": "Local Real-time + Remote Asynchronous.",
            "justification": "Physics dictates we cannot have global real-time across high-latency links. The architecture provides strict real-time guarantees *within* the local subsystem, but uses store-and-forward queues for global state."
        })
        
    if "Serverless" in arch:
        tradeoffs.append({
            "dimension": "Cost vs Performance (Cold Starts)",
            "decision": "Optimizing for Cost at Idle.",
            "justification": "Serverless scales to zero, saving money. The tradeoff is occasional 1-3 second latency spikes (cold starts) when functions wake up. Acceptable for standard APIs, dangerous for strict real-time."
        })
    elif "Microservices" in arch:
        tradeoffs.append({
            "dimension": "Scalability vs Operational Complexity",
            "decision": "Prioritizing independent scaling.",
            "justification": "EKS/ECS microservices handle massive scale and allow teams to deploy independently. The tradeoff is a heavy DevOps burden, requiring service meshes, distributed tracing, and complex CI/CD."
        })
        
    return tradeoffs

def _validate_constraints(features: dict, arch: str) -> list:
    issues = []
    real_time = features.get("real_time", False)
    edge_off = features.get("edge_offline", False)
    scale = features.get("scale", 0)
    
    if "Serverless" in arch and real_time and scale > 50000:
        issues.append({
            "conflict": "Serverless ONLY vs Real-time Collaboration at High Scale",
            "reasoning": "Serverless WebSockets (e.g. API Gateway) have hard connection limits and high costs at scale. Lambda cold starts break real-time latency requirements.",
            "adjustment": "Hybrid approach: Use Serverless for REST APIs, but provision dedicated EC2/ECS instances or managed PaaS for the WebSocket/Real-time layer."
        })
        
    kw = features.get("keywords_found", {})
    offline_kw = kw.get("offline", [])
    is_space = any(k in ["space", "mars", "high latency", "remote environment"] for k in offline_kw) or "Mars" in features.get("subsystem_scales", {})
    if is_space and real_time:
        issues.append({
            "conflict": "Real-time UI vs High-latency Environments (Mars)",
            "reasoning": "Mars-Earth communication has a 4-20 minute light-speed delay. 'Real-time' collaboration across this link is physically impossible.",
            "adjustment": "Relaxed constraint: 'Real-time' is restricted to local intra-node communication. Interplanetary sync uses asynchronous store-and-forward (DTN)."
        })
        
    if edge_off and features.get("payments"):
        issues.append({
            "conflict": "Strict Consistency (Payments) vs Distributed/Offline Systems",
            "reasoning": "Financial ledgers require strict ACID consistency, which is mathematically impossible in a partition-tolerant offline environment (CAP Theorem).",
            "adjustment": "Tradeoff-based decision: Edge systems log intent/authorizations (event sourcing). Ledgers are formally reconciled in the Cloud once connectivity restores."
        })
        
    return issues

def _build_ui_ux(features: dict) -> list:
    ui = []
    multi_context = features.get("multi_context", False)
    
    if multi_context:
        subsystem_scales = features.get("subsystem_scales", {})
        for sub in subsystem_scales.keys():
            if sub in ["Earth/Cloud", "Cloud", "Earth"]:
                ui.append({
                    "environment": sub,
                    "type": "Rich Web/Mobile UI",
                    "offline_ux": "Standard caching (Service Workers). Optimistic UI for mutations.",
                    "degradation": "Graceful degradation on partial failure; skeleton loaders during latency.",
                    "real_time": "WebSocket-driven live updates. True real-time state synchronization."
                })
            else:
                ui.append({
                    "environment": sub,
                    "type": "Lightweight / Critical-only UI",
                    "offline_ux": "Full local state via local-first DB (e.g. SQLite/IndexedDB). Manual conflict resolution UI.",
                    "degradation": "Zero reliance on external network. UI remains 100% functional offline.",
                    "real_time": "Optimistic updates locally. Sync indicators explicitly show 'Last Synced X mins ago'."
                })
    else:
        if features.get("edge_offline"):
            ui.append({
                "environment": "Edge / Remote",
                "type": "Lightweight / Critical-only UI",
                "offline_ux": "Full local state. Explicit conflict resolution screens.",
                "degradation": "100% offline functional. 'Syncing' indicator locked.",
                "real_time": "Local 'real-time' illusion. Remote state clearly marked as 'Delayed'."
            })
        else:
            ui.append({
                "environment": "Cloud / Web",
                "type": "Rich Responsive UI",
                "offline_ux": "Basic PWA caching. Forms save to IndexedDB if offline.",
                "degradation": "Loading skeletons, retry buttons, graceful fallback.",
                "real_time": "WebSockets for live updates."
            })
    return ui


def _apply_rules(scale, real_time, ai_req, iot, platform, payments, security, ms_hint, edge_offline, multi_context):
    if multi_context:
        arch = "Hybrid Multi-Environment Architecture"
        reason = "Multiple distinct environments detected. Problem decomposed into independent subsystems with a dedicated integration bridge."
        tradeoffs = "Increased deployment complexity, distributed tracing challenges, and eventual consistency handling required across environments."
        return arch, 95, reason, tradeoffs

    if edge_offline:
        arch = "Edge-First Distributed Architecture"
        reason = "Offline, high-latency, or extreme environment detected. System requires autonomy without constant cloud connectivity."
        tradeoffs = "High on-device processing requirements. Delayed data synchronization. Eventual consistency is mandatory."
        return arch, 95, reason, tradeoffs

    # Rule 1 — Enterprise / very large scale → Microservices
    if scale >= MICROSERVICES_SCALE or ms_hint:
        confidence = min(95, 75 + int((scale - MICROSERVICES_SCALE) / 50_000))
        confidence = min(confidence, 95)
        if real_time:
            arch = "Event-Driven Microservices"
            reason = (f"Scale of {scale:,} users demands independent service scaling. "
                      "Real-time requirements add event-driven messaging layer (Kafka/WebSockets).")
        else:
            arch = "Microservices"
            reason = (f"Scale of {scale:,} users exceeds monolithic capacity threshold ({MICROSERVICES_SCALE:,}). "
                      "Independent deployment and scaling of each service is essential.")
        tradeoffs = ("Higher operational complexity (K8s, service mesh). "
                     "Network latency between services. Requires strong DevOps maturity.")
        return arch, confidence, reason, tradeoffs

    # Rule 2 — IoT → Edge + Event-Driven
    if iot:
        arch = "Edge-Driven IoT Architecture"
        reason = ("IoT workloads require edge computing for low-latency sensor processing. "
                  "MQTT broker handles device communication; cloud handles aggregation.")
        tradeoffs = "Edge node management complexity. Offline-first design needed for connectivity gaps."
        return arch, 88, reason, tradeoffs

    # Rule 3 — AI-heavy platform → AI-Augmented Microservices
    if ai_req and scale > 20_000:
        arch = "AI-Augmented Microservices"
        reason = ("AI/ML workloads need isolated compute (GPU instances) separate from business logic. "
                  "Microservices isolate model serving from API layer.")
        tradeoffs = "Model serving latency adds p99 overhead. GPU instances significantly increase cost."
        return arch, 85, reason, tradeoffs

    # Rule 4 — Small scale, no real-time, no AI → Monolithic
    if scale < MONOLITHIC_MAX_SCALE and not real_time and not ai_req:
        arch = "Monolithic"
        reason = (f"Scale of {scale:,} users is well within monolithic capacity. "
                  "Simpler to develop, test, and deploy at this stage.")
        tradeoffs = ("Harder to scale individual components later. "
                     "Deploy-all-or-nothing constraint. Plan for eventual decomposition.")
        return arch, 82, reason, tradeoffs

    # Rule 5 — Mid-scale, real-time → Serverless + event-driven
    if scale <= SERVERLESS_MAX_SCALE and real_time and not security:
        arch = "Serverless Event-Driven"
        reason = ("Mid-scale with real-time events suits serverless: auto-scaling, "
                  "no idle compute cost, event triggers handle spikes cleanly.")
        tradeoffs = "Cold-start latency (100–500ms). Not suited for stateful long-running processes."
        return arch, 80, reason, tradeoffs

    # Rule 6 — Mid-scale default → Modular Monolith / Hybrid
    arch = "Hybrid (Modular Monolith → Microservices)"
    reason = (f"Scale of {scale:,} suits a modular monolith now with clear service boundaries "
              "to extract into microservices as traffic grows.")
    tradeoffs = "Requires disciplined module boundaries from day one to avoid big-ball-of-mud."
    return arch, 78, reason, tradeoffs


def _select_components(arch: str, features: dict) -> list:
    base = []
    platform = features.get("platform", "web")
    real_time = features.get("real_time", False)
    payments  = features.get("payments", False)
    ai_req    = features.get("ai_required", False)
    iot       = features.get("iot", False)
    scale     = features.get("scale", 10_000)
    video     = features.get("video_streaming", False)
    global_d  = features.get("global_deployment", False)
    edge_off  = features.get("edge_offline", False)
    multi_context = features.get("multi_context", False)

    if multi_context:
        subsystem_scales = features.get("subsystem_scales", {})
        if not subsystem_scales:
            subsystem_scales = {"Cloud": 1_000_000, "Edge": 10_000}

        for sub, sc in subsystem_scales.items():
            sub_lower = sub.lower()
            if sub_lower in ["earth", "cloud", "online"]:
                base.append({"layer": f"[{sub} System] API Gateway", "tech": "AWS API Gateway", "role": "Global routing, auth, rate limiting"})
                base.append({"layer": f"[{sub} System] Backend", "tech": "Microservices (EKS / ECS)", "role": "Scalable core logic for cloud/earth users"})
                base.append({"layer": f"[{sub} System] Database", "tech": "Aurora PostgreSQL + DynamoDB", "role": "Highly available persistent storage"})
                if video:
                    base.append({"layer": f"[{sub} System] Media Pipeline", "tech": "FFmpeg + CloudFront CDN", "role": "Global video streaming and delivery"})
            else:
                base.append({"layer": f"[{sub} System] Edge Node", "tech": "Hardened Embedded Systems (N+1)", "role": "Local autonomous compute"})
                if features.get("security_critical"):
                    base.append({"layer": f"[{sub} System] Safety-Critical", "tech": "RTOS / Isolated Thread", "role": "Life-critical operations, strict isolation (Level 1 Priority)"})
                    base.append({"layer": f"[{sub} System] Execution Path", "tech": "Priority Scheduler", "role": "Level 1: Life-critical, Level 2: Comm, Level 3: Analytics"})
                base.append({"layer": f"[{sub} System] Local Storage", "tech": "Embedded DB (SQLite/RocksDB)", "role": "Local state, replicated logs"})
        
        # AI Deployment Split
        if ai_req:
            base.append({"layer": "[Cloud AI] Heavy Computing", "tech": "GPU Cluster / SageMaker", "role": "Model training, heavy inference, model update pipeline"})
            base.append({"layer": "[Edge AI] Local Inference", "tech": "Lightweight On-device Models", "role": "Real-time local decision making, inference boundaries, sync fallback behavior"})
        
        # Integration Layer Completeness
        kw = features.get("keywords_found", {})
        offline_kw = kw.get("offline", [])
        is_space = any(k in ["space", "mars", "high latency", "remote environment", "remote"] for k in offline_kw) or "Mars" in subsystem_scales
        
        if is_space:
            base.append({"layer": "[Integration Layer] DTN Bridge", "tech": "Delay-Tolerant Networking (BP)", "role": "Store-and-forward communication method per link, high latency tolerance"})
        else:
            base.append({"layer": "[Integration Layer] Sync Bridge", "tech": "Sync Queue / Eventual Consistency", "role": "Message buffering, store-and-forward when online, eventual consistency sync strategy"})
            
        base.append({"layer": "[Integration Layer] Sync Strategy", "tech": "CRDTs & Vector Clocks", "role": "Conflict-free resolution, versioning, explicit data ownership rules"})
        
        return base

    if edge_off:
        kw = features.get("keywords_found", {})
        offline_kw = kw.get("offline", [])
        is_critical = any(k in ["life-support", "critical system", "autonomous system"] for k in offline_kw)
        is_space = any(k in ["space", "mars", "high latency", "remote environment"] for k in offline_kw)

        if is_critical or not offline_kw: # default to critical if unknown edge context
            base.append({"layer": "Safety-Critical Control System", "tech": "RTOS / Isolated Compute Unit", "role": "Hard real-time execution, emergency overrides (independent of AI)"})

        base.append({"layer": "Edge Layer", "tech": "Edge nodes (Raspberry Pi / embedded systems)", "role": "Local compute units with N+1 redundancy and failover"})
        base.append({"layer": "Local Processing", "tech": "Real-time decision engine", "role": "Rule-based + lightweight ML"})
        
        base.append({"layer": "Energy-Aware Scheduling", "tech": "Dynamic Power Scaling", "role": "Prioritize life-support, sleep idle components, reduce task frequency"})

        base.append({"layer": "Local Storage", "tech": "Embedded DB (SQLite / RocksDB)", "role": "Replicated local logs + state"})
        base.append({"layer": "Messaging", "tech": "MQTT / ZeroMQ", "role": "Local message bus"})
        
        base.append({"layer": "Observability", "tech": "Prometheus + Grafana + Jaeger", "role": "Local metrics, visualization, tracing, and file-based log storage"})
        
        if is_space:
            base.append({"layer": "Interplanetary Communication / DTN Layer", "tech": "Bundle Protocol (BP)", "role": "Store-and-forward transmission, scheduled windows, high-latency tolerance (4–20 min delay)"})
        else:
            base.append({"layer": "Sync Layer", "tech": "Delayed sync queue", "role": "Store-and-forward mechanism"})

        if ai_req:
            base.append({"layer": "AI/ML Layer", "tech": "On-device AI models", "role": "Lightweight offline inference"})
        return base

    is_serverless = "Serverless" in arch

    # Frontend
    if platform in ("mobile", "hybrid"):
        base.append({"layer": "Frontend", "tech": "React Native / Flutter", "role": "Cross-platform mobile UI"})
    else:
        base.append({"layer": "Frontend", "tech": "React + Tailwind CSS", "role": "Responsive web interface"})

    # API layer
    base.append({"layer": "API Gateway", "tech": "AWS API Gateway", "role": "Routing, authentication, rate limiting"})

    # Backend
    if is_serverless:
        base.append({"layer": "Compute", "tech": "AWS Lambda (Node.js/Python)", "role": "Serverless business logic"})
    elif "Microservices" in arch:
        base.append({"layer": "Backend Services", "tech": "FastAPI + Node.js microservices", "role": "Isolated domain services"})
    else:
        base.append({"layer": "Backend", "tech": "FastAPI (Python)", "role": "Core business logic"})

    # Database
    if is_serverless:
        base.append({"layer": "Database", "tech": "Amazon DynamoDB", "role": "Serverless NoSQL storage"})
    elif scale >= MICROSERVICES_SCALE:
        base.append({"layer": "Database", "tech": "PostgreSQL (primary) + MongoDB", "role": "Relational + document storage"})
    else:
        base.append({"layer": "Database", "tech": "PostgreSQL", "role": "Primary relational database"})

    # Cache
    if not is_serverless:
        base.append({"layer": "Cache", "tech": "Redis", "role": "Session store, query cache, rate limiting"})

    # Real-time
    if real_time:
        if is_serverless:
            base.append({"layer": "Messaging", "tech": "AWS SNS / SQS", "role": "Event queues and topics"})
            base.append({"layer": "WebSocket", "tech": "AWS API Gateway WebSockets", "role": "Real-time client connections"})
        else:
            base.append({"layer": "Messaging", "tech": "Apache Kafka", "role": "Event streaming and async processing"})
            base.append({"layer": "WebSocket", "tech": "Socket.io / FastAPI WebSocket", "role": "Real-time client connections"})

    # AI
    if ai_req:
        if is_serverless:
            base.append({"layer": "AI/ML Layer", "tech": "AWS SageMaker Serverless Inference", "role": "Model serving and inference"})
        else:
            base.append({"layer": "AI/ML Layer", "tech": "Python (scikit-learn / PyTorch) + FastAPI", "role": "Model serving and inference"})
    else:
        base.append({"layer": "AI/ML Layer", "tech": "Python (Optional)", "role": "Optional: Anomaly detection, predictive analytics, or automation"})

    # IoT
    if iot:
        base.append({"layer": "IoT Broker", "tech": "MQTT (Mosquitto) + AWS IoT Core", "role": "Device communication"})
        base.append({"layer": "Edge", "tech": "AWS Greengrass / Raspberry Pi", "role": "On-device processing"})

    # Auth
    base.append({"layer": "Auth", "tech": "Auth0 / Amazon Cognito", "role": "Authentication and RBAC"})

    # Video Streaming
    if video:
        base.append({"layer": "Video Ingestion", "tech": "RTMP / WebRTC", "role": "Ingest servers"})
        base.append({"layer": "Media Processing", "tech": "FFmpeg / AWS MediaLive", "role": "Transcoding and packaging"})
        base.append({"layer": "Streaming Protocol", "tech": "HLS / DASH", "role": "Adaptive bitrate delivery"})
        base.append({"layer": "Video Storage", "tech": "AWS S3 / Object Storage", "role": "Video chunk storage"})

    # Global Infrastructure
    if global_d:
        base.append({"layer": "Global Routing", "tech": "AWS Route 53 / Geo DNS", "role": "Geo-routing across regions (US, India, Europe)"})
        base.append({"layer": "Regional Clusters", "tech": "Independent service clusters", "role": "Compute per region"})
        base.append({"layer": "Data Replication", "tech": "Cross-region DB replication", "role": "Data synchronization"})
        base.append({"layer": "Failover", "tech": "Automatic region failover", "role": "High availability"})

    # CDN
    base.append({"layer": "CDN", "tech": "AWS CloudFront", "role": "Static assets and edge caching"})

    return base


def _select_integrations(features: dict) -> list:
    integrations = []
    
    if features.get("edge_offline"):
        integrations.append({"name": "Local Notification System", "purpose": "Alerting and alarms", "category": "messaging"})
        integrations.append({"name": "Onboard AI Models", "purpose": "Local decision making", "category": "ai"})
        integrations.append({"name": "Local Communication Protocols", "purpose": "Inter-device telemetry", "category": "messaging"})
        return integrations

    if features.get("payments"):
        integrations.append({"name": "Stripe / Razorpay", "purpose": "Payment processing and subscription billing", "category": "payment"})
    if features.get("real_time"):
        integrations.append({"name": "Twilio / Firebase FCM", "purpose": "Push notifications and SMS alerts", "category": "messaging"})
    if features.get("platform") in ("mobile", "hybrid", "web"):
        integrations.append({"name": "Google Maps API", "purpose": "Location, routing, and geofencing", "category": "maps"})
    if features.get("ai_required"):
        integrations.append({"name": "OpenAI API / Hugging Face", "purpose": "LLM inference and embeddings", "category": "ai"})
    integrations.append({"name": "SendGrid", "purpose": "Transactional email delivery", "category": "messaging"})
    integrations.append({"name": "AWS S3", "purpose": "Object and media storage", "category": "storage"})
    return integrations


def _security_recommendations(features: dict) -> list:
    recs = [
        "JWT + OAuth 2.0 — stateless auth with refresh token rotation",
        "HTTPS / TLS 1.3 enforced on all endpoints",
        "WAF (AWS WAF) on API Gateway — block SQLi, XSS, DDoS",
        "Secrets management via AWS Secrets Manager (no env-var secrets)",
        "Role-Based Access Control (RBAC) — least-privilege principle",
        "AES-256 encryption at rest for all PII data",
    ]
    if features.get("security_critical"):
        recs += [
            "HIPAA / GDPR compliance layer — audit logs, data residency",
            "Penetration testing scheduled quarterly",
            "Field-level encryption for sensitive medical / financial records",
        ]
    if features.get("payments"):
        recs.append("PCI-DSS Level 1 compliance — never store raw card data, use tokenization")
    return recs


# ── Reasoning Details ─────────────────────────────────────────────────────────

def _build_reasoning_details(features: dict, arch: str) -> list:
    """Return an ordered list of decision-rule bullets that led to 'arch'."""
    scale       = features.get("scale", 10_000)
    real_time   = features.get("real_time", False)
    ai_req      = features.get("ai_required", False)
    iot         = features.get("iot", False)
    payments    = features.get("payments", False)
    security    = features.get("security_critical", False)
    ms_hint     = features.get("microservices_hint", False)
    scale_label = features.get("scale_label", "mid")
    edge_off    = features.get("edge_offline", False)
    multi_context = features.get("multi_context", False)

    if multi_context:
        return [
            "Environment Analysis: Multi-context scenario detected (e.g. Earth + Mars, Cloud + Edge).",
            "Problem Decomposition: Splitting system into independent subsystems to prevent forcing one architecture across all environments.",
            f"Architecture Selection: RULE TRIGGERED → {arch}",
            "Integration Strategy: Dedicated integration bridge added for eventual consistency and state sync."
        ]

    if edge_off:
        return [
            "Environment Analysis: Edge/Offline scenario detected",
            "RULE TRIGGERED: Edge/Offline environment detected → Edge-First Distributed Architecture selected"
        ]

    bullets = [
        f"Scale detected: {scale:,} concurrent users → classified as '{scale_label}'",
        f"Real-time requirement: {'YES — event-driven messaging layer added' if real_time else 'NO — synchronous REST sufficient'}",
        f"AI/ML workload: {'YES — dedicated GPU serving layer required' if ai_req else 'NO'}",
        f"IoT devices: {'YES — edge computing + MQTT broker added' if iot else 'NO'}",
        f"Payment processing: {'YES — PCI-DSS compliance layer required' if payments else 'NO'}",
        f"Security-critical domain: {'YES — elevated compliance recommendations applied' if security else 'NO'}",
        f"Microservices signals in description: {'YES — distributed architecture preferred' if ms_hint else 'NO'}",
    ]

    if scale >= MICROSERVICES_SCALE or ms_hint:
        bullets.append(f"RULE TRIGGERED: Scale ≥ {MICROSERVICES_SCALE:,} OR microservices hint → {arch}")
    elif iot:
        bullets.append("RULE TRIGGERED: IoT keywords detected → Edge-Driven IoT Architecture")
    elif ai_req and scale > 20_000:
        bullets.append("RULE TRIGGERED: AI + mid-to-large scale → AI-Augmented Microservices")
    elif scale < MONOLITHIC_MAX_SCALE and not real_time and not ai_req:
        bullets.append(f"RULE TRIGGERED: Scale < {MONOLITHIC_MAX_SCALE:,} + no real-time + no AI → Monolithic")
    elif scale <= SERVERLESS_MAX_SCALE and real_time and not security:
        bullets.append("RULE TRIGGERED: Mid-scale + real-time + non-sensitive → Serverless Event-Driven")
    else:
        bullets.append("RULE TRIGGERED: Mid-scale with mixed signals → Hybrid (Modular Monolith → Microservices)")

    return bullets


# ── Alternatives Comparison ───────────────────────────────────────────────────

def _build_alternatives(arch: str) -> list:
    """
    Return a list of 3 alternative architectures with why each was NOT chosen
    vs. the selected 'arch'.
    """
    all_options = {
        "Monolith": {
            "summary":  "Single deployable unit, shared database, simplest ops model.",
            "pros":     "Fast initial development, zero network-call overhead, easy local testing.",
            "cons":     "Cannot scale individual bottlenecks; deploy-all-or-nothing; hard to parallelize large teams.",
            "when":     "Scale < 20k users, small team, MVP / prototype stage.",
        },
        "Serverless Event-Driven": {
            "summary":  "Functions-as-a-Service triggered by events (AWS Lambda + SQS/EventBridge).",
            "pros":     "Zero idle cost, auto-scaling to zero, no server management.",
            "cons":     "Cold-start latency (100-500ms), 15-min max execution, complex distributed debugging.",
            "when":     "Variable workloads, event-driven triggers, time-to-market priority.",
        },
        "Microservices": {
            "summary":  "Independently deployable services communicating over APIs/events.",
            "pros":     "Independent scaling, polyglot tech stacks, fault isolation.",
            "cons":     "High operational complexity (K8s, service mesh, distributed tracing), network overhead.",
            "when":     "Scale > 100k users, multiple teams, distinct bounded domains.",
        },
        "Hybrid (Modular Monolith → Microservices)": {
            "summary":  "Start with a well-structured monolith and extract services as needed.",
            "pros":     "Lower initial complexity while keeping future flexibility.",
            "cons":     "Requires strong architectural discipline from day one.",
            "when":     "Mid-scale projects expecting significant growth.",
        },
        "Edge-Driven IoT Architecture": {
            "summary":  "On-device processing with MQTT broker and cloud aggregation.",
            "pros":     "Ultra-low latency, offline resilience, bandwidth efficiency.",
            "cons":     "Complex edge fleet management, firmware OTA updates.",
            "when":     "IoT / hardware products with real-time sensor data.",
        },
        "AI-Augmented Microservices": {
            "summary":  "Standard microservices with isolated GPU-backed model serving.",
            "pros":     "Independent model scaling, clean separation of ML from business logic.",
            "cons":     "GPU instances are expensive; model serving latency adds p99 overhead.",
            "when":     "AI-heavy platforms at mid-to-large scale.",
        },
        "Event-Driven Microservices": {
            "summary":  "Microservices communicating exclusively via Kafka event streams.",
            "pros":     "Loose coupling, high throughput, event sourcing / audit trail built-in.",
            "cons":     "Eventual consistency complexity, Kafka operational overhead.",
            "when":     "High-scale + real-time + complex domain requiring audit logs.",
        },
    }

    # Pick the 3 alternatives most different from selected arch
    candidates = [k for k in all_options if k != arch]
    # Priority: always include Monolith and Serverless if not selected
    priority = ["Monolith", "Serverless Event-Driven", "Hybrid (Modular Monolith → Microservices)",
                "Microservices", "Event-Driven Microservices", "AI-Augmented Microservices",
                "Edge-Driven IoT Architecture"]
    ordered = [p for p in priority if p in candidates]

    result = []
    for name in ordered[:3]:
        opt = all_options[name]
        result.append({
            "name":    name,
            "summary": opt["summary"],
            "pros":    opt["pros"],
            "cons":    opt["cons"],
            "when":    opt["when"],
            "why_not_chosen": (
                f"'{name}' was evaluated but not selected because the current inputs "
                f"better match '{arch}' based on scale, feature flags, and confidence scoring."
            ),
        })
    return result
