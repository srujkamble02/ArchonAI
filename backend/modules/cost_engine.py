"""
cost_engine.py
Deterministic cost estimation based on architecture decisions and scale.
All values computed from rule-based formulas — no LLM.

Pricing basis: AWS on-demand (approximate 2025 rates).
"""

import math

from .currency import (
    convert_usd_cost_payload_to_inr,
    format_usd_as_inr,
)

# ── Base AWS pricing (source USD/month approximate) ──────────────────────────
EC2_RATES = {
    "t3.small":   15.18,
    "t3.medium":  30.37,
    "t3.large":   60.74,
    "m5.large":   69.12,
    "m5.xlarge":  138.24,
    "m5.2xlarge": 276.48,
    "c5.xlarge":  124.10,
    "g4dn.xlarge": 394.92,   # GPU for AI
}

RDS_RATE_PER_GB  = 0.115   # RDS PostgreSQL storage per GB/month
RDS_INSTANCE_MAP = {
    "startup":    30.0,
    "mid":        80.0,
    "large":      200.0,
    "enterprise": 600.0,
}

REDIS_RATE = {
    "startup":    15.0,
    "mid":        30.0,
    "large":      80.0,
    "enterprise": 200.0,
}

S3_RATE_PER_GB = 0.023
CLOUDFRONT_RATE = 0.0085   # per GB transfer

KAFKA_RATE = {
    "startup":    0,      # not needed
    "mid":        50.0,
    "large":      150.0,
    "enterprise": 400.0,
}

EKS_CLUSTER_COST = 72.0   # USD 0.10/hr per cluster
NAT_GATEWAY      = 32.40  # per NAT gateway/month
CLOUDWATCH       = 10.0   # base monitoring


def estimate_cost(features: dict, architecture: dict) -> dict:
    scale_label = features.get("scale_label", "mid")
    scale       = features.get("scale", 10_000)
    arch_type   = architecture.get("architecture", "")
    real_time   = features.get("real_time", False)
    ai_req      = features.get("ai_required", False)
    iot         = features.get("iot", False)

    if features.get("multi_context"):
        subsystem_scales = features.get("subsystem_scales", {})
        if not subsystem_scales:
            subsystem_scales = {"Cloud": 1_000_000, "Edge": 10_000}
            
        total_compute = 0
        total_db = 0
        total_edge = 0
        breakdown = []
        assumptions = []
        
        for sub, sc in subsystem_scales.items():
            sub_lower = sub.lower()
            if sub_lower in ["earth", "cloud", "online"]:
                c_compute = _compute_cost(sc, "large", "Microservices", ai_req)
                c_db = _database_cost(sc, "large", "Microservices")
                total_compute += c_compute
                total_db += c_db
                _add_breakdown(breakdown, f"[{sub}] Compute & DB", c_compute + c_db, f"AWS Microservices & Aurora for {sc:,} {sub} users.")
                assumptions.append(f"{sub} Scale: {sc:,} users")
            else:
                e_hw = sc * 50.0
                e_pwr = sc * 2.0
                total_edge += (e_hw + e_pwr)
                _add_breakdown(breakdown, f"[{sub}] Hardware & Power", e_hw + e_pwr, f"Amortized hardware CapEx and power for {sc:,} {sub} nodes.")
                assumptions.append(f"{sub} Scale: {sc:,} devices/nodes")
                
        total = total_compute + total_db + total_edge
        
        _add_breakdown(breakdown, "[Integration] Bridge Infrastructure", 500.0, "Dedicated bridge gateways and store-and-forward storage buffers.")
        total += 500.0
        
        if ai_req:
            _add_breakdown(breakdown, "[AI] Hybrid Model Deployment", 1500.0, "Cloud SageMaker for heavy lifting + Edge TPU amortized cost.")
            total += 1500.0
            
        return convert_usd_cost_payload_to_inr({
            "compute": total_compute + total_edge,
            "database": total_db, "storage": 0, "messaging": 0, "networking": 0, "monitoring": 0, "iot": 0, "ai_serving": 1500 if ai_req else 0,
            "total_monthly": total,
            "scaling_10x_estimate": total * 8,
            "currency": "INR",
            "basis": "Hybrid Pricing (Cloud OpEx + Hardware CapEx)",
            "note": "Costs are split: Cloud systems use standard AWS pricing; Edge systems calculate amortized physical hardware and power costs.",
            "breakdown": breakdown,
            "assumptions": assumptions
        })

    is_edge_offline = "Edge-First" in arch_type

    if is_edge_offline:
        hardware_cost = scale * 50.0
        power_cost = scale * 2.0
        maint_cost = scale * 5.0
        total_edge = hardware_cost + power_cost + maint_cost

        breakdown = []
        _add_breakdown(breakdown, "Hardware (Edge Devices)", hardware_cost, f"Capital expense amortized or leased for {scale:,} edge nodes.")
        _add_breakdown(breakdown, "Power Consumption", power_cost, f"Estimated local power draw across {scale:,} devices.")
        _add_breakdown(breakdown, "Maintenance & Field Ops", maint_cost, "Physical maintenance, replacement pool, and truck rolls.")

        return convert_usd_cost_payload_to_inr({
            "compute": hardware_cost,
            "database": 0, "storage": 0, "messaging": 0, "networking": 0, "monitoring": maint_cost, "iot": power_cost, "ai_serving": 0,
            "total_monthly": total_edge,
            "scaling_10x_estimate": total_edge * 8,
            "currency": "INR",
            "basis": "Hardware and Field Operations Pricing",
            "note": "AWS cloud pricing removed. Costs reflect physical hardware, power, and field maintenance for offline edge deployment.",
            "breakdown": breakdown,
            "assumptions": [
                f"Scale: {scale:,} physical edge nodes",
                f"Hardware: approx. {format_usd_as_inr(50)}/node amortized",
                f"Power: approx. {format_usd_as_inr(2)}/mo per node",
                f"Maintenance: approx. {format_usd_as_inr(5)}/mo per node (spares + truck rolls)"
            ]
        })

    compute  = _compute_cost(scale, scale_label, arch_type, ai_req)
    database = _database_cost(scale, scale_label, arch_type)
    cache    = _cache_cost(scale_label, arch_type)
    storage  = _storage_cost(scale)
    messaging = _messaging_cost(scale_label, real_time, arch_type)
    networking = _networking_cost(scale, arch_type)
    monitoring = _monitoring_cost(arch_type)
    iot_cost   = _iot_cost(scale_label) if iot else 0.0
    ai_cost    = _ai_cost(scale) if ai_req else 0.0

    subtotals = {
        "compute":    round(compute, 2),
        "database":   round(database + cache, 2),
        "storage":    round(storage, 2),
        "messaging":  round(messaging, 2),
        "networking": round(networking, 2),
        "monitoring": round(monitoring, 2),
        "iot":        round(iot_cost, 2),
        "ai_serving": round(ai_cost, 2),
    }

    total = round(sum(subtotals.values()), 2)
    scaling_10x = round(total * _scaling_factor(arch_type), 2)

    is_serverless = "Serverless" in arch_type

    # ── Per-component breakdown for report ──────────────────────────────────
    breakdown = []
    _add_breakdown(breakdown, "Compute (Lambda & API Gateway)" if is_serverless else "Compute",
                   subtotals["compute"],
                   _compute_description(scale, arch_type, ai_req))
    
    if is_serverless:
        _add_breakdown(breakdown, "Database (DynamoDB)",
                       subtotals["database"],
                       f"DynamoDB pay-per-request pricing for {scale:,} active users.")
    else:
        _add_breakdown(breakdown, "Database (RDS + Redis Cache)",
                       subtotals["database"],
                       f"RDS PostgreSQL {format_usd_as_inr(RDS_INSTANCE_MAP.get(scale_label, 80))}/mo instance "
                       f"+ Redis {format_usd_as_inr(REDIS_RATE.get(scale_label, 30))}/mo. "
                       f"Storage: ~{max(20, int(scale/500))} GB @ {format_usd_as_inr(RDS_RATE_PER_GB, decimals=2)}/GB.")

    _add_breakdown(breakdown, "Storage & CDN (S3 + CloudFront)",
                   subtotals["storage"],
                   f"~{max(50, int(scale/200))} GB S3 @ {format_usd_as_inr(S3_RATE_PER_GB, decimals=2)}/GB + "
                   f"CloudFront egress (10% traffic, {format_usd_as_inr(CLOUDFRONT_RATE, decimals=2)}/GB).")
    
    if real_time:
        msg_desc = "AWS SNS/SQS for serverless event routing." if is_serverless else "Apache Kafka MSK for real-time event streaming."
    else:
        msg_desc = "No messaging layer required for this architecture."

    _add_breakdown(breakdown, "Messaging (SNS/SQS)" if is_serverless else "Messaging (Kafka / SQS)",
                   subtotals["messaging"],
                   msg_desc)
    
    net_desc = f"Data-out at {format_usd_as_inr(0.09, decimals=2)}/GB (~10 KB/req × 10 req/user/day for {scale:,} users)."
    if not is_serverless:
        net_desc = f"NAT Gateway @ {format_usd_as_inr(NAT_GATEWAY)}/mo + " + net_desc

    _add_breakdown(breakdown, "Networking (Data Transfer)" if is_serverless else "Networking (NAT Gateway + Data Transfer)",
                   subtotals["networking"],
                   net_desc)
    
    _add_breakdown(breakdown, "Monitoring (CloudWatch + X-Ray)" if is_serverless else "Monitoring (CloudWatch + Prometheus)",
                   subtotals["monitoring"],
                   "CloudWatch base + X-Ray tracing." if is_serverless else "CloudWatch base + Prometheus/Grafana stack. "
                   f"{'Extra log ingestion for microservices.' if 'Microservices' in arch_type else ''}")
    if iot_cost > 0:
        _add_breakdown(breakdown, "IoT (AWS IoT Core + MQTT)",
                       subtotals["iot"],
                       f"AWS IoT Core messaging + Greengrass edge runtime for '{scale_label}' fleet.")
    if ai_cost > 0:
        _add_breakdown(breakdown, "AI Serving (SageMaker Endpoint)",
                       subtotals["ai_serving"],
                       f"SageMaker real-time inference endpoint. GPU cost scales with {scale:,} inference calls.")

    assumptions = [
        f"Scale: {scale:,} concurrent users ({scale_label} tier)",
        "Pricing basis: AWS on-demand rates, approximate 2025 figures",
        "Traffic pattern: 10 requests per user per day, ~10 KB average payload",
        "No reserved instances or Savings Plans applied (can reduce compute ~30-40%)",
        f"Kafka included only when real_time=True (currently: {real_time})",
        f"GPU instance (g4dn.xlarge @ {format_usd_as_inr(EC2_RATES['g4dn.xlarge'])}/mo) included only when AI=True (currently: {ai_req})",
        "Storage estimate: 1 GB per 500 users, 10% CDN egress ratio",
    ]

    return convert_usd_cost_payload_to_inr({
        **subtotals,
        "total_monthly":         total,
        "scaling_10x_estimate":  scaling_10x,
        "currency":              "INR",
        "basis":                 "AWS on-demand pricing (approximate 2025 rates)",
        "note":                  _cost_note(scale_label, arch_type),
        "breakdown":             breakdown,
        "assumptions":           assumptions,
    })


def _add_breakdown(lst: list, label: str, cost: float, description: str):
    lst.append({"label": label, "cost": round(cost, 2), "description": description})


def _compute_description(scale: int, arch_type: str, ai_req: bool) -> str:
    if "Serverless" in arch_type:
        reqs_per_mo = scale * 10 * 30
        desc = f"Lambda invocations (~{reqs_per_mo:,}/mo) + API Gateway requests"
        if ai_req:
            desc += f" + SageMaker Serverless Inference"
        return desc

    if scale < 10_000:
        spec = f"1× t3.medium ({format_usd_as_inr(15.18)}/mo)"
    elif scale < 50_000:
        spec = f"2× t3.large ({format_usd_as_inr(60.74)}/mo each)"
    elif scale < 200_000:
        spec = f"3× m5.large ({format_usd_as_inr(69.12)}/mo each)"
    elif scale < 500_000:
        spec = f"4× m5.xlarge ({format_usd_as_inr(138.24)}/mo each)"
    else:
        spec = f"6× m5.2xlarge ({format_usd_as_inr(276.48)}/mo each)"
    extras = []
    if "Microservices" in arch_type or "Event-Driven" in arch_type:
        extras.append(f"EKS cluster overhead ({format_usd_as_inr(EKS_CLUSTER_COST)}/mo)")
    if ai_req:
        extras.append(f"GPU node: g4dn.xlarge ({format_usd_as_inr(EC2_RATES['g4dn.xlarge'])}/mo)")
    desc = spec
    if extras:
        desc += " + " + " + ".join(extras)
    return desc



def _compute_cost(scale, scale_label, arch_type, ai_req) -> float:
    if "Serverless" in arch_type:
        # Source pricing: roughly USD 0.20 per 1M Lambda reqs, plus API Gateway costs.
        reqs_per_mo = scale * 10 * 30
        return max(5.0, (reqs_per_mo / 1_000_000) * 4.0)

    # Determine instance type and count
    if scale < 10_000:
        instance, count = "t3.medium", 1
    elif scale < 50_000:
        instance, count = "t3.large", 2
    elif scale < 200_000:
        instance, count = "m5.large", 3
    elif scale < 500_000:
        instance, count = "m5.xlarge", 4
    else:
        instance, count = "m5.2xlarge", 6

    cost = EC2_RATES[instance] * count

    # EKS overhead for microservices
    if "Microservices" in arch_type or "Event-Driven" in arch_type:
        cost += EKS_CLUSTER_COST

    # GPU node for AI
    if ai_req:
        cost += EC2_RATES["g4dn.xlarge"]

    return cost


def _database_cost(scale, scale_label, arch_type="Monolithic") -> float:
    if "Serverless" in arch_type:
        reqs_per_mo = scale * 10 * 30
        return max(5.0, (reqs_per_mo / 1_000_000) * 1.25) # DynamoDB source pricing per million W/R
    storage_gb = max(20, int(scale / 500))   # rough: 1 GB per 500 users
    instance_cost = RDS_INSTANCE_MAP.get(scale_label, 80.0)
    storage_cost  = storage_gb * RDS_RATE_PER_GB
    return instance_cost + storage_cost


def _cache_cost(scale_label, arch_type="Monolithic") -> float:
    if "Serverless" in arch_type:
        return 0.0 # DynamoDB handles caching or uses DAX which isn't modeled separately here
    return REDIS_RATE.get(scale_label, 30.0)


def _storage_cost(scale) -> float:
    gb = max(50, int(scale / 200))
    s3 = gb * S3_RATE_PER_GB
    cdn = (gb * 0.1) * CLOUDFRONT_RATE * 30   # assume 10% egress/day
    return s3 + cdn


def _messaging_cost(scale_label, real_time, arch_type="Monolithic") -> float:
    if not real_time:
        return 0.0
    if "Serverless" in arch_type:
        return 10.0 # SQS/SNS pay per request
    return KAFKA_RATE.get(scale_label, 50.0)


def _networking_cost(scale, arch_type) -> float:
    cost = 0.0
    if "Serverless" not in arch_type:
        cost += NAT_GATEWAY
        if "Microservices" in arch_type:
            cost += NAT_GATEWAY   # second AZ
    # Data transfer out (~10 KB per request, 10 req/user/day)
    monthly_gb_out = (scale * 10 * 10_000) / (1024 ** 3)
    cost += monthly_gb_out * 0.09   # Source pricing per GB out
    return cost


def _monitoring_cost(arch_type) -> float:
    base = CLOUDWATCH + 10.0   # Prometheus + Grafana Cloud free tier buffer
    if "Microservices" in arch_type:
        base += 30.0   # additional log ingestion
    return base


def _iot_cost(scale_label) -> float:
    return {"startup": 20, "mid": 60, "large": 150, "enterprise": 400}.get(scale_label, 60)


def _ai_cost(scale) -> float:
    # Model serving: SageMaker endpoint estimate
    return max(50, scale / 1000 * 0.5)


def _scaling_factor(arch_type) -> float:
    if "Serverless" in arch_type:
        return 2.8    # serverless scales near-linearly
    if "Microservices" in arch_type:
        return 3.2    # horizontal scaling, but more infra
    return 5.0        # monolith scales poorly — vertical limits hit


def _cost_note(scale_label, arch_type) -> str:
    notes = {
        "startup":    "Startup estimate. Reserved instances would cut compute ~40%.",
        "mid":        "Mid-scale estimate. Consider Savings Plans for 30-40% reduction.",
        "large":      "Large-scale estimate. Reserved + Spot instances recommended.",
        "enterprise": "Enterprise estimate. Negotiate EDP (Enterprise Discount Program) with AWS.",
    }
    return notes.get(scale_label, "Estimate based on on-demand pricing.")
