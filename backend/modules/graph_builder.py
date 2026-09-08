"""
graph_builder.py
Builds a directed architecture graph using NetworkX.
Nodes = services, Edges = communication paths with protocol labels.
"""

import networkx as nx


def build_graph(architecture: dict, features: dict) -> dict:
    components = architecture.get("components", [])
    arch_type  = architecture.get("architecture", "")

    G = nx.DiGraph()

    # Build node list from components
    layer_to_id = {}
    for i, comp in enumerate(components):
        node_id = comp["layer"].lower().replace(" ", "_").replace("/", "_")
        layer_to_id[comp["layer"]] = node_id
        G.add_node(node_id, label=comp["layer"], tech=comp["tech"],
                   role=comp["role"], group=_group(comp["layer"]))

    # Add external service nodes
    for intg in architecture.get("integrations", []):
        node_id = intg["name"].lower().replace(" ", "_").replace("/", "_")
        G.add_node(node_id, label=intg["name"], tech=intg["name"],
                   role=intg["purpose"], group="external")

    # Wire edges based on architecture logic
    _add_edges(G, arch_type, features, layer_to_id, architecture)

    # Serialize for JSON output
    nodes = [{"id": n, **G.nodes[n]} for n in G.nodes]
    edges = [{"from": u, "to": v, "label": G.edges[u, v].get("label", "")}
             for u, v in G.edges]

    # Compute basic graph metrics
    metrics = {
        "node_count": G.number_of_nodes(),
        "edge_count": G.number_of_edges(),
        "is_dag": nx.is_directed_acyclic_graph(G),
        "critical_path": _critical_path(G),
    }

    return {"nodes": nodes, "edges": edges, "metrics": metrics}


def _group(layer: str) -> str:
    layer = layer.lower()
    if any(x in layer for x in ["frontend", "ui", "cdn", "mobile", "client"]):
        return "presentation"
    if any(x in layer for x in ["gateway", "load balancer", "routing"]):
        return "presentation"
    if any(x in layer for x in ["auth", "security", "firewall", "waf", "encryption"]):
        return "security"
    if any(x in layer for x in ["api", "backend", "service", "compute", "lambda", "function"]):
        return "application"
    if any(x in layer for x in ["database", "cache", "storage", "redis", "dynamo", "rds", "replica"]):
        return "data"
    if any(x in layer for x in ["kafka", "messaging", "websocket", "queue", "event", "pub/sub", "sns", "sqs"]):
        return "messaging"
    if any(x in layer for x in ["iot", "edge", "broker", "sensor", "mqtt", "device"]):
        return "edge"
    if any(x in layer for x in ["ai", "ml", "model", "inference", "gpu", "sagemaker"]):
        return "ai"
    if any(x in layer for x in ["jenkins", "ci/cd", "cicd", "pipeline", "github actions", "gitlab"]):
        return "devops"
    if any(x in layer for x in ["monitor", "observ", "prometheus", "grafana", "logging", "tracing", "alert"]):
        return "monitoring"
    if any(x in layer for x in ["video", "streaming", "media", "transcode"]):
        return "application"
    return "infrastructure"


def _add_edges(G, arch_type, features, layer_to_id, architecture):

    def lnode(name):
        for layer, node_id in layer_to_id.items():
            if name.lower() in layer.lower():
                return node_id
        return None

    def safe_edge(src_key, dst_key, label="HTTP/REST"):
        s = lnode(src_key)
        d = lnode(dst_key)
        if s and d and s != d and G.has_node(s) and G.has_node(d):
            G.add_edge(s, d, label=label)

    # Core data flow
    safe_edge("frontend", "api",      "HTTPS")
    safe_edge("frontend", "backend",  "HTTPS")
    safe_edge("api",      "backend",  "HTTP/REST")
    safe_edge("backend",  "database", "SQL/TCP")
    safe_edge("backend",  "cache",    "Redis protocol")
    safe_edge("cache",    "database", "Cache miss → DB")

    # Auth
    safe_edge("backend",  "auth",     "OAuth 2.0 / JWT")
    safe_edge("api",      "auth",     "Token validation")

    # CDN
    safe_edge("cdn",      "frontend", "Static assets")

    # Real-time edges
    if features.get("real_time"):
        safe_edge("backend",   "messaging", "Produce events")
        safe_edge("messaging", "backend",   "Consume events")
        safe_edge("backend",   "websocket", "Push updates")
        safe_edge("websocket", "frontend",  "WS frames")

    # AI edges
    if features.get("ai_required"):
        safe_edge("backend", "ai_ml",  "Inference request")
        safe_edge("ai_ml",   "database", "Store predictions")

    # IoT edges
    if features.get("iot"):
        safe_edge("iot",  "edge",    "MQTT")
        safe_edge("edge", "backend", "HTTPS / gRPC")

    # External integrations
    for intg in architecture.get("integrations", []):
        ext_id = intg["name"].lower().replace(" ", "_").replace("/", "_")
        if G.has_node(ext_id):
            cat = intg.get("category", "")
            if cat == "payment":
                safe_edge("backend", intg["name"], "HTTPS / Webhook")
            elif cat == "messaging":
                safe_edge("backend", intg["name"], "API call")
            elif cat == "storage":
                safe_edge("backend", intg["name"], "S3 SDK")


def _critical_path(G: nx.DiGraph) -> list:
    """Return longest path (by hop count) as proxy for critical path."""
    try:
        path = nx.dag_longest_path(G)
        return path
    except Exception:
        return []
