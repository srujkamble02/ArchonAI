"""
recommendation_engine.py
Generates multi-option recommendations for architecture, tech stack, cloud, database, and DevOps.
All logic is rule-based — no LLM involvement.
"""


from .currency import format_usd_as_inr


def generate_recommendations(features: dict, architecture: dict, cloud_provider: str = "AWS") -> dict:
    """Generate multi-option recommendations across all categories."""
    arch_type = architecture.get("architecture", "")

    return {
        "architecture_options": _architecture_options(arch_type, features),
        "tech_stack_options": _tech_stack_options(features, arch_type),
        "database_options": _database_options(features, arch_type),
        "cloud_options": _cloud_options(cloud_provider, features),
        "devops_options": _devops_options(arch_type, features),
        "archon_recommendation": _final_recommendation(arch_type, features, cloud_provider),
    }


def _architecture_options(arch_type: str, features: dict) -> list:
    """Return 2-3 architecture options ranked by suitability."""

    all_options = {
        "Microservices": {
            "description": "Independently deployable services communicating over APIs and event streams.",
            "advantages": [
                "Independent scaling per service",
                "Polyglot technology stacks",
                "Fault isolation — one service failure doesn't crash the system",
                "Independent deployment cycles per team",
            ],
            "disadvantages": [
                "High operational complexity (K8s, service mesh, distributed tracing)",
                "Network latency between services",
                "Data consistency challenges across service boundaries",
                "Requires mature DevOps practices",
            ],
            "estimated_cost": f"High ({format_usd_as_inr(800)}-{format_usd_as_inr(5000)}+/month infrastructure)",
            "scalability": "Very High — horizontal scaling per service",
            "complexity": "High",
        },
        "Modular Monolith": {
            "description": "Single deployable unit with clear internal module boundaries, ready for future decomposition.",
            "advantages": [
                "Simple deployment and operations",
                "Easy local development and debugging",
                "No network overhead between modules",
                "Can be decomposed into microservices later",
            ],
            "disadvantages": [
                "All modules must deploy together",
                "Harder to scale individual bottlenecks",
                "Requires discipline to maintain module boundaries",
                "Risk of becoming a 'big ball of mud' without discipline",
            ],
            "estimated_cost": f"Low-Medium ({format_usd_as_inr(100)}-{format_usd_as_inr(500)}/month infrastructure)",
            "scalability": "Medium — vertical + horizontal scaling of entire application",
            "complexity": "Low-Medium",
        },
        "Serverless": {
            "description": "Functions-as-a-Service (FaaS) triggered by events, with zero idle cost.",
            "advantages": [
                "Zero idle cost — pay only when code runs",
                "Automatic scaling to zero and to millions",
                "No server management",
                "Built-in high availability",
            ],
            "disadvantages": [
                "Cold start latency (100-500ms)",
                "15-minute maximum execution time",
                "Difficult to debug distributed serverless functions",
                "Vendor lock-in to cloud provider",
            ],
            "estimated_cost": f"Low ({format_usd_as_inr(20)}-{format_usd_as_inr(200)}/month for moderate traffic)",
            "scalability": "Very High — automatic, near-infinite scaling",
            "complexity": "Medium",
        },
        "Event-Driven Microservices": {
            "description": "Microservices communicating via event streams (Kafka/RabbitMQ) for loose coupling.",
            "advantages": [
                "Extremely loose coupling between services",
                "Built-in audit trail via event log",
                "High throughput for real-time data processing",
                "Natural support for CQRS and event sourcing",
            ],
            "disadvantages": [
                "Eventual consistency complexity",
                "Kafka/event broker operational overhead",
                "Debugging event chains is difficult",
                "Requires careful event schema management",
            ],
            "estimated_cost": f"High ({format_usd_as_inr(1000)}-{format_usd_as_inr(5000)}+/month infrastructure)",
            "scalability": "Very High — built for massive throughput",
            "complexity": "Very High",
        },
    }

    # Select relevant options based on features
    selected = []

    # Always include the chosen architecture as Option 1 (Recommended)
    if arch_type in all_options:
        opt = all_options[arch_type]
        selected.append({
            "option_number": 1,
            "label": "Recommended",
            "name": arch_type,
            **opt,
            "reason": f"Best match for the detected requirements: {features.get('scale_label', 'mid')} scale, "
                      f"{'real-time, ' if features.get('real_time') else ''}"
                      f"{'AI/ML, ' if features.get('ai_required') else ''}"
                      f"{'payments, ' if features.get('payments') else ''}"
                      f"platform: {features.get('platform', 'web')}.",
        })
    else:
        # For special architectures (Edge-First, Hybrid Multi-Environment), create custom entry
        selected.append({
            "option_number": 1,
            "label": "Recommended",
            "name": arch_type,
            "description": architecture_descriptions.get(arch_type, arch_type),
            "advantages": ["Best match for detected environment constraints"],
            "disadvantages": ["Increased deployment complexity"],
            "estimated_cost": "Varies by deployment environment",
            "scalability": "Environment-dependent",
            "complexity": "High",
            "reason": f"Selected based on unique environment requirements detected in the project description.",
        })

    # Add alternatives
    alt_priority = ["Modular Monolith", "Serverless", "Microservices", "Event-Driven Microservices"]
    opt_num = 2
    for alt_name in alt_priority:
        if alt_name != arch_type and alt_name in all_options and opt_num <= 3:
            opt = all_options[alt_name]
            selected.append({
                "option_number": opt_num,
                "label": "Alternative",
                "name": alt_name,
                **opt,
                "reason": _why_alternative(alt_name, arch_type, features),
            })
            opt_num += 1

    return selected


architecture_descriptions = {
    "Edge-First Distributed Architecture": "Autonomous edge nodes with local processing and delayed cloud sync.",
    "Hybrid Multi-Environment Architecture": "Multiple independent subsystems with an integration bridge.",
    "Edge-Driven IoT Architecture": "Edge computing with MQTT broker and cloud aggregation.",
    "AI-Augmented Microservices": "Microservices with isolated GPU-backed model serving.",
    "Hybrid (Modular Monolith → Microservices)": "Start monolithic, extract services as needed.",
    "Monolithic": "Single deployable unit with shared database.",
}


def _why_alternative(alt_name, arch_type, features):
    reasons = {
        "Modular Monolith": "Simpler to implement and operate. Good choice if team size is small or project is in early stages.",
        "Serverless": "Lower infrastructure cost with automatic scaling. Good if traffic is variable and latency requirements are relaxed.",
        "Microservices": "Better isolation and independent scaling. Good if multiple teams work on different domains.",
        "Event-Driven Microservices": "Better for real-time event processing and audit trails. Good if strict event ordering matters.",
    }
    return reasons.get(alt_name, "Evaluated as a viable alternative based on project characteristics.")


def _tech_stack_options(features: dict, arch_type: str) -> list:
    """Generate 2-3 technology stack options."""
    scale = features.get("scale", 10_000)
    ai_req = features.get("ai_required", False)
    platform = features.get("platform", "web")

    options = []

    # Option 1: Python-based (recommended for AI/data-heavy)
    if ai_req or "AI" in arch_type:
        options.append({
            "option_number": 1,
            "label": "Recommended",
            "name": "Python FastAPI Stack",
            "frontend": "React + TypeScript" if platform == "web" else "React Native",
            "backend": "FastAPI (Python)",
            "database": "PostgreSQL + Redis",
            "ai_ml": "PyTorch / scikit-learn + FastAPI serving",
            "reason": "Python is the industry standard for AI/ML workloads with the richest ecosystem of ML libraries.",
            "advantages": ["Best AI/ML library support", "Fast development", "Strong async support with FastAPI"],
            "disadvantages": ["Slower than compiled languages for compute-heavy tasks", "GIL limitations"],
        })
        options.append({
            "option_number": 2,
            "label": "Alternative",
            "name": "Node.js + Python Hybrid",
            "frontend": "Next.js (React)" if platform == "web" else "React Native",
            "backend": "Node.js (Express/NestJS) + Python AI microservice",
            "database": "PostgreSQL + MongoDB",
            "ai_ml": "Python microservice for ML, Node.js for API",
            "reason": "Splits API performance (Node.js) from ML workloads (Python) for best of both worlds.",
            "advantages": ["High-performance API layer", "Separate scaling for ML", "JavaScript full-stack"],
            "disadvantages": ["Two runtimes to maintain", "Inter-service communication overhead"],
        })
        options.append({
            "option_number": 3,
            "label": "Alternative",
            "name": "Java Spring Boot Stack",
            "frontend": "React + TypeScript" if platform == "web" else "Flutter",
            "backend": "Spring Boot (Java 17+)",
            "database": "PostgreSQL + Redis",
            "ai_ml": "DL4J / ONNX Runtime for inference",
            "reason": "Enterprise-grade reliability and performance. Best for large teams with Java expertise.",
            "advantages": ["Enterprise ecosystem", "Strong typing", "Excellent performance"],
            "disadvantages": ["Slower development speed", "Heavier resource usage", "Less ML library support"],
        })
    else:
        # Non-AI projects
        options.append({
            "option_number": 1,
            "label": "Recommended",
            "name": "React + Node.js Stack",
            "frontend": "React + TypeScript" if platform == "web" else "React Native",
            "backend": "Node.js (Express/NestJS)",
            "database": "PostgreSQL" if scale > 50_000 else "PostgreSQL",
            "reason": "Most widely adopted web stack with the largest developer talent pool and ecosystem.",
            "advantages": ["JavaScript full-stack", "Huge ecosystem", "Fast development", "Easy hiring"],
            "disadvantages": ["Single-threaded (use worker threads for CPU tasks)", "Callback complexity"],
        })
        options.append({
            "option_number": 2,
            "label": "Alternative",
            "name": "React + Python FastAPI Stack",
            "frontend": "React + TypeScript" if platform == "web" else "React Native",
            "backend": "FastAPI (Python)",
            "database": "PostgreSQL + Redis",
            "reason": "FastAPI provides excellent async performance with automatic API documentation.",
            "advantages": ["Auto-generated API docs", "Strong typing with Pydantic", "Async native"],
            "disadvantages": ["Python is slower than Node.js/Go for pure I/O", "Smaller web ecosystem than Node.js"],
        })
        if scale > 100_000:
            options.append({
                "option_number": 3,
                "label": "Alternative",
                "name": "Next.js + Go Microservices",
                "frontend": "Next.js (React SSR)",
                "backend": "Go (Gin/Fiber) microservices",
                "database": "PostgreSQL + Redis + MongoDB",
                "reason": "Go provides extreme performance and low memory usage ideal for high-scale microservices.",
                "advantages": ["Excellent performance", "Low memory footprint", "Built-in concurrency"],
                "disadvantages": ["Smaller ecosystem", "Verbose error handling", "Fewer developers available"],
            })
        else:
            options.append({
                "option_number": 3,
                "label": "Alternative",
                "name": "Next.js Full-Stack",
                "frontend": "Next.js (React SSR + API routes)",
                "backend": "Next.js API Routes + Prisma ORM",
                "database": "PostgreSQL" if payments else "MongoDB",
                "reason": "Full-stack framework with SSR, API routes, and built-in optimizations — minimal setup.",
                "advantages": ["Single framework", "SSR for SEO", "Built-in routing", "Vercel deployment"],
                "disadvantages": ["Vendor coupling to Vercel", "Not ideal for complex backends", "JavaScript-only"],
            })

    return options


def _database_options(features: dict, arch_type: str) -> list:
    """Generate database recommendations."""
    scale = features.get("scale", 10_000)
    payments = features.get("payments", False)
    real_time = features.get("real_time", False)

    options = []

    # PostgreSQL is almost always a good choice
    options.append({
        "option_number": 1,
        "label": "Recommended",
        "name": "PostgreSQL",
        "type": "Relational (SQL)",
        "advantages": ["ACID compliance", "JSON support", "Full-text search", "Excellent scaling with read replicas"],
        "disadvantages": ["Vertical scaling limits", "Complex sharding"],
        "best_for": "Transactional data, complex queries, structured data with relationships",
        "scalability": "High with read replicas and connection pooling",
    })

    if not payments and not features.get("security_critical"):
        options.append({
            "option_number": 2,
            "label": "Alternative",
            "name": "MongoDB",
            "type": "Document (NoSQL)",
            "advantages": ["Flexible schema", "Horizontal scaling (sharding)", "Fast development", "Good for unstructured data"],
            "disadvantages": ["No ACID across documents (until v4.0 multi-doc)", "Less suitable for complex joins"],
            "best_for": "Unstructured data, rapid prototyping, content-heavy applications",
            "scalability": "Very High with native sharding",
        })
    else:
        options.append({
            "option_number": 2,
            "label": "Alternative",
            "name": "MySQL",
            "type": "Relational (SQL)",
            "advantages": ["Wide adoption", "Excellent read performance", "Good tooling", "Easy replication"],
            "disadvantages": ["Less feature-rich than PostgreSQL", "Limited JSON support"],
            "best_for": "Read-heavy workloads, simpler relational models",
            "scalability": "High with read replicas",
        })

    if "Serverless" in arch_type:
        options.append({
            "option_number": 3,
            "label": "Alternative",
            "name": "DynamoDB",
            "type": "Key-Value / Document (NoSQL)",
            "advantages": ["Serverless native", "Single-digit millisecond latency", "Automatic scaling", "Zero maintenance"],
            "disadvantages": ["Complex query patterns", "Expensive for scan-heavy workloads", "Vendor lock-in"],
            "best_for": "Serverless architectures, simple access patterns, high throughput",
            "scalability": "Very High — automatic",
        })
    elif real_time and scale > 100_000:
        options.append({
            "option_number": 3,
            "label": "Alternative",
            "name": "CockroachDB",
            "type": "Distributed SQL",
            "advantages": ["Global distribution", "Strong consistency", "PostgreSQL compatible", "Automatic sharding"],
            "disadvantages": ["Higher latency than single-node PostgreSQL", "Complex pricing", "Newer ecosystem"],
            "best_for": "Globally distributed applications requiring strong consistency",
            "scalability": "Very High — built for global distribution",
        })

    return options


def _cloud_options(selected_cloud: str, features: dict) -> list:
    """Generate cloud provider comparisons."""

    options = [
        {
            "option_number": 1 if selected_cloud == "AWS" else 2,
            "label": "Recommended" if selected_cloud == "AWS" else "Alternative",
            "name": "AWS (Amazon Web Services)",
            "advantages": [
                "Largest service portfolio (200+ services)",
                "Most mature ecosystem and documentation",
                "Widest global infrastructure (30+ regions)",
                "Strongest enterprise support and compliance certifications",
            ],
            "disadvantages": [
                "Complex pricing model",
                "Can be expensive without optimization",
                "Steeper learning curve due to service breadth",
            ],
            "key_services": "EC2, EKS, Lambda, RDS, DynamoDB, S3, CloudFront, SageMaker",
            "best_for": "Enterprise workloads, broadest service needs, global deployment",
        },
        {
            "option_number": 1 if selected_cloud == "GCP" else (2 if selected_cloud != "AWS" else 3),
            "label": "Recommended" if selected_cloud == "GCP" else "Alternative",
            "name": "Google Cloud Platform (GCP)",
            "advantages": [
                "Best-in-class AI/ML services (Vertex AI, TPUs)",
                "Superior data analytics (BigQuery)",
                "Strong Kubernetes support (GKE — Google invented K8s)",
                "Competitive pricing with sustained-use discounts",
            ],
            "disadvantages": [
                "Smaller service portfolio than AWS",
                "Fewer global regions",
                "Enterprise support less mature than AWS",
            ],
            "key_services": "GKE, Cloud Run, Cloud Functions, Cloud SQL, BigQuery, Vertex AI",
            "best_for": "AI/ML workloads, data analytics, Kubernetes-native architectures",
        },
        {
            "option_number": 1 if selected_cloud == "Azure" else 3,
            "label": "Recommended" if selected_cloud == "Azure" else "Alternative",
            "name": "Microsoft Azure",
            "advantages": [
                "Best integration with Microsoft ecosystem (AD, Office 365, Teams)",
                "Strong hybrid cloud support (Azure Arc)",
                "Enterprise-friendly licensing and support",
                "Good AI services (Azure OpenAI, Cognitive Services)",
            ],
            "disadvantages": [
                "UI/UX can be complex",
                "Some services are less mature than AWS equivalents",
                "Pricing can be confusing",
            ],
            "key_services": "AKS, App Service, Azure Functions, Azure SQL, Cosmos DB, Azure AI",
            "best_for": "Microsoft-centric organizations, hybrid cloud, enterprise compliance",
        },
    ]

    # Sort so recommended is first
    options.sort(key=lambda x: x["option_number"])
    return options


def _devops_options(arch_type: str, features: dict) -> list:
    """Generate DevOps tool recommendations with Jenkins as primary."""
    return [
        {
            "option_number": 1,
            "label": "Recommended",
            "name": "Jenkins",
            "category": "Self-hosted CI/CD",
            "advantages": [
                "Full pipeline control and customization",
                "Self-hosted — no external dependencies",
                "1,800+ plugins for any integration",
                "Declarative and scripted pipeline support",
                "Free and open-source",
            ],
            "disadvantages": [
                "Requires server management and maintenance",
                "Plugin compatibility issues across versions",
                "Steeper initial setup compared to cloud-hosted options",
            ],
            "estimated_cost": f"Free (self-hosted) + server costs ({format_usd_as_inr(20)}-{format_usd_as_inr(100)}/month)",
            "scalability": "High — master-agent distributed builds",
            "complexity": "Medium",
            "reason": "Jenkins provides maximum control and customization for complex CI/CD pipelines without vendor lock-in.",
        },
        {
            "option_number": 2,
            "label": "Alternative",
            "name": "GitHub Actions",
            "category": "Cloud-hosted CI/CD",
            "advantages": [
                "Native GitHub integration",
                "Large marketplace of reusable actions",
                "Free for public repositories",
                "Easy YAML-based configuration",
            ],
            "disadvantages": [
                "Vendor lock-in to GitHub",
                "Limited customization compared to Jenkins",
                "Can be expensive for private repos with heavy CI",
            ],
            "estimated_cost": f"Free (public) / {format_usd_as_inr(4)}/user/month (Teams)",
            "scalability": "Medium — limited concurrent jobs on free tier",
            "complexity": "Low",
            "reason": "Best choice for teams already on GitHub who want minimal CI/CD setup overhead.",
        },
        {
            "option_number": 3,
            "label": "Alternative",
            "name": "GitLab CI/CD",
            "category": "Integrated DevOps platform",
            "advantages": [
                "All-in-one DevOps platform",
                "Built-in security scanning (SAST, DAST)",
                "Container registry included",
                "Auto DevOps with minimal configuration",
            ],
            "disadvantages": [
                "Heavy platform — CI/CD is part of a larger suite",
                "Self-hosted requires significant resources",
                "Smaller community than Jenkins/GitHub Actions",
            ],
            "estimated_cost": f"Free tier / Premium {format_usd_as_inr(29)}/user/month",
            "scalability": "High — shared runners scale well",
            "complexity": "Medium",
            "reason": "Best for teams wanting source code, CI/CD, security scanning, and container registry in one platform.",
        },
    ]


def _final_recommendation(arch_type: str, features: dict, cloud_provider: str) -> dict:
    """Generate the final ARCHON AI RECOMMENDATION summary."""

    summary_parts = [
        f"Based on analysis of the project requirements, Archon AI recommends a **{arch_type}** architecture",
        f"deployed on **{cloud_provider}**.",
    ]

    if features.get("ai_required"):
        summary_parts.append("The **Python FastAPI** stack is recommended for optimal AI/ML library support.")
    else:
        summary_parts.append("The **React + Node.js** stack provides the fastest development velocity with the largest talent pool.")

    summary_parts.append(f"**PostgreSQL** is recommended as the primary database for data integrity and ACID compliance.")
    summary_parts.append(f"**Jenkins** is recommended as the CI/CD orchestration server for maximum pipeline control and self-hosted security.")

    return {
        "summary": " ".join(summary_parts),
        "architecture": arch_type,
        "cloud": cloud_provider,
        "ci_cd": "Jenkins",
        "primary_database": "PostgreSQL",
        "confidence": features.get("scale_label", "mid"),
    }
