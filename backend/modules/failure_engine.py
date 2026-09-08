"""
failure_engine.py
Logic-based failure simulation — no LLM.
Simulates realistic failure scenarios based on architecture and scale.
Each scenario uses threshold rules to compute impact and mitigation.
Enhanced: Each failure now includes N ranked recovery solutions.
"""





# ── Load thresholds ──────────────────────────────────────────────────────────
DB_SATURATION_THRESHOLD   = 0.80   # 80% connection pool usage → risk
CACHE_HIT_TARGET          = 0.85   # <85% cache hit rate → DB overload risk
SPIKE_MULTIPLIER_CRITICAL = 5.0    # 5x traffic → critical
SPIKE_MULTIPLIER_HIGH     = 2.5    # 2.5x traffic → high


def simulate_failures(features: dict, architecture: dict, cost: dict) -> list:
    scale     = features.get("scale", 10_000)
    arch_type = architecture.get("architecture", "")
    real_time = features.get("real_time", False)
    ai_req    = features.get("ai_required", False)
    iot       = features.get("iot", False)
    payments  = features.get("payments", False)

    failures = []

    if features.get("multi_context"):
        failures.append(_multi_context_bridge_failure())
        failures.append(_multi_context_cloud_outage())
        failures.append(_multi_context_edge_isolation())
        if ai_req:
            failures.append(_multi_context_ai_drift())

        order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        failures.sort(key=lambda x: order.get(x["impact"], 9))
        return failures

    if "Edge-First" in arch_type:
        failures.append(_edge_communication_blackout())
        failures.append(_edge_node_failure())
        failures.append(_edge_power_loss())
        failures.append(_edge_sensor_malfunction())
        failures.append(_edge_sync_conflict())
        if ai_req:
            failures.append(_ml_model_degradation())

        order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        failures.sort(key=lambda x: order.get(x["impact"], 9))
        return failures

    failures.append(_traffic_spike(scale, arch_type))

    if "Serverless" in arch_type:
        failures.append(_serverless_cold_start())
        failures.append(_api_gateway_throttling())
        failures.append(_dynamodb_throttling())
    else:
        failures.append(_database_overload(scale, arch_type))
        failures.append(_service_crash(arch_type))
        failures.append(_cache_failure(scale))

    if real_time and "Serverless" not in arch_type:
        failures.append(_messaging_lag(scale, arch_type))

    if payments:
        failures.append(_payment_gateway_timeout())

    if ai_req:
        failures.append(_ml_model_degradation())

    if iot:
        failures.append(_iot_device_flood(scale))

    if "Microservices" in arch_type:
        failures.append(_cascading_service_failure())

    # Sort by impact severity
    order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
    failures.sort(key=lambda x: order.get(x["impact"], 9))

    return failures


# ── Solution builder helper ──────────────────────────────────────────────────

def _solution(name, description, implementation, advantages, disadvantages,
              complexity="Medium", cost_impact="Medium", effectiveness="High",
              recommended=True):
    return {
        "name": name,
        "description": description,
        "implementation_approach": implementation,
        "advantages": advantages,
        "disadvantages": disadvantages,
        "complexity": complexity,
        "cost_impact": cost_impact,
        "recovery_effectiveness": effectiveness,
        "recommendation_status": "Recommended" if recommended else "Optional",
    }


def _rank_solutions(solutions):
    """Rank solutions by effectiveness then complexity."""
    eff_order = {"Very High": 0, "High": 1, "Medium": 2, "Low": 3}
    cmp_order = {"Low": 0, "Medium": 1, "High": 2, "Very High": 3}
    ranked = sorted(solutions, key=lambda s: (eff_order.get(s["recovery_effectiveness"], 9),
                                               cmp_order.get(s["complexity"], 9)))
    for i, s in enumerate(ranked):
        s["rank"] = i + 1
    return ranked


def _best_strategy(solutions):
    """Determine the best combined strategy from top solutions."""
    recommended = [s for s in solutions if s["recommendation_status"] == "Recommended"]
    if not recommended:
        recommended = solutions[:2]
    top = recommended[:2]
    names = " + ".join(s["name"] for s in top)
    return {
        "strategy": names,
        "explanation": f"Combining {names} provides the best balance of recovery effectiveness, "
                       f"implementation complexity, and cost efficiency for this architecture.",
    }


# ── Failure scenarios with N solutions ───────────────────────────────────────

def _database_overload(scale, arch_type) -> dict:
    conn_pressure = scale / 10_000
    impact = "Critical" if conn_pressure > 3 else "High" if conn_pressure > 1.5 else "Medium"

    if "Microservices" in arch_type:
        mitigation = ("PgBouncer connection pooler limits per-service connections. "
                      "Each service uses its own DB schema (database-per-service pattern). "
                      "Read replicas absorb SELECT queries (target: 70% offload).")
    else:
        mitigation = ("Add Redis cache layer — target 85%+ cache hit rate to reduce DB load. "
                      "Implement read replicas for SELECT-heavy operations. "
                      "Query optimization and connection pooling via PgBouncer.")

    solutions = _rank_solutions([
        _solution("Automatic Failover to Replica",
                  "Configure automatic failover to a hot standby replica when primary becomes unavailable.",
                  "Set up RDS Multi-AZ with automatic failover. Failover completes in 60-120 seconds.",
                  ["Near-zero data loss", "Automatic — no manual intervention", "AWS-managed"],
                  ["60-120 second failover window", "Doubles database cost"],
                  complexity="Medium", cost_impact="Medium", effectiveness="High", recommended=True),
        _solution("Database Clustering",
                  "Deploy a multi-node database cluster for high availability and load distribution.",
                  "Set up PostgreSQL Citus cluster or Aurora PostgreSQL with multiple read replicas.",
                  ["Distributes load across nodes", "Handles massive concurrent connections", "Linear read scaling"],
                  ["Complex setup and management", "Higher infrastructure cost"],
                  complexity="High", cost_impact="High", effectiveness="Very High", recommended=True),
        _solution("Connection Pooling (PgBouncer)",
                  "Add a connection pooler between application and database to efficiently manage connections.",
                  "Deploy PgBouncer in transaction pooling mode. Set pool_size per service.",
                  ["Reduces connection overhead by 90%", "Easy to implement", "Low cost"],
                  ["Adds a network hop", "Transaction-level pooling has limitations with prepared statements"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Read Replica Routing",
                  "Route read-only queries to dedicated read replicas to offload the primary.",
                  "Create 2-3 read replicas. Configure application to route SELECT queries to replicas.",
                  ["Offloads 60-70% of queries from primary", "Linear read scaling"],
                  ["Replication lag (milliseconds)", "Application must handle read/write splitting"],
                  complexity="Medium", cost_impact="Medium", effectiveness="High", recommended=True),
        _solution("Multi-Region Database Deployment",
                  "Deploy database replicas across multiple geographic regions for disaster recovery.",
                  "Set up Aurora Global Database or cross-region read replicas with automatic failover.",
                  ["Survives entire region outages", "Low-latency reads globally", "RPO < 1 second"],
                  ["Significantly higher cost", "Cross-region write latency", "Complex consistency model"],
                  complexity="High", cost_impact="High", effectiveness="Very High", recommended=False),
        _solution("Exponential Backoff Retry",
                  "Implement retry logic with exponential backoff for transient database connection failures.",
                  "Add retry decorator with 1s → 2s → 4s → 8s backoff, max 4 retries, with jitter.",
                  ["Simple to implement", "Handles transient failures gracefully", "No infrastructure cost"],
                  ["Increases response latency during retries", "Doesn't solve persistent overload"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
        _solution("Circuit Breaker Pattern",
                  "Implement circuit breaker to prevent cascading failures when database is overloaded.",
                  "Use Resilience4j or custom circuit breaker. Open after 50% failure rate over 30s window.",
                  ["Prevents cascading failures", "Allows system to degrade gracefully", "Fast failure"],
                  ["Requests fail immediately when circuit is open", "Requires fallback logic"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Cache Fallback (Stale Data)",
                  "Serve stale cached data when database is unavailable for non-critical read operations.",
                  "Set Redis cache with TTL grace period. Serve stale cache when DB connection fails.",
                  ["Maintains user experience during outage", "Zero additional infrastructure"],
                  ["Stale data may cause inconsistencies", "Only works for read operations"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=False),
        _solution("Backup Restoration",
                  "Restore database from the most recent automated backup in case of data corruption.",
                  "Enable automated daily backups with point-in-time recovery. RTO: 30-60 minutes.",
                  ["Recovers from data corruption", "Point-in-time recovery available"],
                  ["Longer recovery time (30-60 min)", "Data loss between last backup and failure"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=False),
    ])

    return {
        "scenario":   "Database connection pool exhaustion",
        "trigger":    f"Load > {DB_SATURATION_THRESHOLD*100:.0f}% pool capacity at {scale:,} concurrent users",
        "impact":     impact,
        "probability":"High" if scale > 50_000 else "Medium",
        "mitigation": mitigation,
        "detection":  "CloudWatch RDS metric: DatabaseConnections > 160 → alert",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _traffic_spike(scale, arch_type) -> dict:
    spike_scale = scale * SPIKE_MULTIPLIER_CRITICAL
    impact = "Critical"

    if "Serverless" in arch_type:
        mitigation = ("Serverless auto-scales to spike automatically. "
                      "Set concurrency limit to prevent runaway Lambda costs. "
                      "API Gateway throttle: 10,000 req/s hard limit.")
        impact = "Medium"
    elif "Microservices" in arch_type or "Event-Driven" in arch_type:
        mitigation = ("Kubernetes HPA (Horizontal Pod Autoscaler) triggers at 70% CPU. "
                      "Scale from 3 → 15 replicas within 2 minutes. "
                      "API Gateway rate limiting: 5,000 req/s per IP. "
                      "Circuit breaker (Hystrix) prevents cascade on downstream services.")
    else:
        mitigation = ("Horizontal scaling via load balancer — add instances within 2 min. "
                      "CDN caching absorbs static requests at edge. "
                      "Rate limiting at Nginx/load balancer level. "
                      "Auto-scaling group triggers at 70% CPU threshold.")

    solutions = _rank_solutions([
        _solution("Auto-Scaling (HPA / ASG)",
                  "Automatically scale compute resources based on CPU/memory thresholds.",
                  "Configure K8s HPA at 70% CPU or AWS ASG with scaling policies.",
                  ["Automatic response", "Handles sustained load", "Cost-efficient scaling"],
                  ["2-5 minute scaling lag", "May over-provision during oscillation"],
                  complexity="Medium", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("CDN Edge Caching",
                  "Cache static assets and API responses at CDN edge locations worldwide.",
                  "Configure CloudFront/Cloudflare with aggressive caching policies.",
                  ["Absorbs 60-80% of read traffic", "Global performance improvement", "DDoS protection"],
                  ["Cache invalidation complexity", "Not suitable for dynamic content"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Rate Limiting",
                  "Limit requests per client/IP to prevent any single source from overwhelming the system.",
                  "Implement rate limiting at API Gateway level: 1000 req/min per IP.",
                  ["Prevents abuse", "Protects backend services", "Simple implementation"],
                  ["May reject legitimate traffic during spikes", "Requires tuning thresholds"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Load Balancer Health Routing",
                  "Configure load balancer to route traffic only to healthy instances.",
                  "Set up ALB/NLB with health check probes every 10s, unhealthy threshold: 3.",
                  ["Prevents routing to crashed instances", "Automatic failover"],
                  ["Doesn't add capacity", "Only redistributes existing capacity"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
        _solution("Queue-Based Load Leveling",
                  "Buffer incoming requests in a queue to smooth out traffic spikes.",
                  "Put SQS/RabbitMQ between API gateway and backend. Process at sustainable rate.",
                  ["Absorbs burst traffic", "No request loss", "Backend processes at steady rate"],
                  ["Increased latency", "Queue can grow during sustained spikes"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=False),
        _solution("Geographic Load Balancing",
                  "Distribute traffic across multiple regions to spread the load.",
                  "Configure Route 53 geo-routing or Cloudflare load balancing across regions.",
                  ["Distributes load globally", "Reduces latency for users", "Region-level redundancy"],
                  ["Complex multi-region setup", "Data replication challenges", "Higher cost"],
                  complexity="High", cost_impact="High", effectiveness="Very High", recommended=False),
    ])

    return {
        "scenario":   f"Traffic spike (5x normal: {int(spike_scale):,} concurrent users)",
        "trigger":    f"Sudden traffic surge to {int(spike_scale):,} req/s",
        "impact":     impact,
        "probability":"Medium (product launch, viral event)",
        "mitigation": mitigation,
        "detection":  "CloudWatch ALB metric: RequestCount > 5x 5-min average → auto-scale trigger",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _service_crash(arch_type) -> dict:
    if "Microservices" in arch_type or "Event-Driven" in arch_type:
        impact = "Medium"
        mitigation = ("Kubernetes restarts crashed pod within 30s (liveness probe). "
                      "Service mesh (Istio) retries failed requests up to 3x. "
                      "Circuit breaker opens after 50% failure rate — prevents cascade. "
                      "Multi-AZ deployment: pod replicas across 2 availability zones.")
    else:
        impact = "High"
        mitigation = ("Run minimum 2 instances behind load balancer (active-active). "
                      "Health check every 30s — ALB removes unhealthy instance within 1 min. "
                      "Horizontal scaling allows failed nodes to be replaced automatically. "
                      "Blue-green deployment prevents crash during deploys.")

    solutions = _rank_solutions([
        _solution("Container Auto-Restart (Liveness Probe)",
                  "Kubernetes automatically restarts containers that fail health checks.",
                  "Configure liveness probe with httpGet on /health, failureThreshold: 3.",
                  ["Automatic recovery", "< 30 second restart", "No manual intervention"],
                  ["Brief service interruption during restart", "Doesn't fix root cause"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Multi-AZ Deployment",
                  "Deploy application replicas across multiple availability zones.",
                  "Spread pods/instances across 2-3 AZs with anti-affinity rules.",
                  ["Survives AZ-level failures", "No single point of failure"],
                  ["Increased data transfer costs between AZs", "Slightly more complex networking"],
                  complexity="Medium", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Circuit Breaker Pattern",
                  "Prevent cascading failures by failing fast when a dependency is down.",
                  "Implement Resilience4j circuit breaker with 50% failure threshold.",
                  ["Prevents cascade", "Fast failure response", "Graceful degradation"],
                  ["Requires fallback logic", "Open circuit means partial feature loss"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Blue-Green Deployment",
                  "Maintain two identical environments and switch traffic between them.",
                  "Deploy new version to green environment, test, then switch load balancer.",
                  ["Zero-downtime deployments", "Instant rollback by switching back"],
                  ["Doubles infrastructure during deployment", "Database schema changes need care"],
                  complexity="Medium", cost_impact="Medium", effectiveness="High", recommended=True),
        _solution("Service Mesh Retry",
                  "Use Istio/Linkerd service mesh to automatically retry failed requests.",
                  "Configure Istio VirtualService with retries: attempts: 3, retryOn: 5xx.",
                  ["Transparent to application code", "Handles transient failures"],
                  ["Adds latency on retries", "May mask underlying issues"],
                  complexity="Medium", cost_impact="Low", effectiveness="Medium", recommended=False),
    ])

    return {
        "scenario":   "Application service crash / OOM kill",
        "trigger":    "Memory leak, unhandled exception, or OOM kill from kernel",
        "impact":     impact,
        "probability":"Medium",
        "mitigation": mitigation,
        "detection":  "CloudWatch EC2/Pod metric: health check failures > 2 consecutive → replace",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _cache_failure(scale) -> dict:
    db_load_increase = round((1 - CACHE_HIT_TARGET) * 100 / (1 - 0.5), 1)

    solutions = _rank_solutions([
        _solution("ElastiCache Multi-AZ Failover",
                  "Configure Redis with Multi-AZ automatic failover for high availability.",
                  "Enable Multi-AZ on ElastiCache Redis. Failover completes in < 60 seconds.",
                  ["Automatic failover", "< 60 second recovery", "AWS-managed"],
                  ["Doubles cache cost", "Brief connection interruption during failover"],
                  complexity="Low", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Cache-Aside with TTL Grace",
                  "Serve stale cache data with extended TTL when cache source fails.",
                  "Set cache entries with soft TTL (5min) and hard TTL (30min). Serve stale on miss.",
                  ["Maintains user experience", "Simple implementation", "No additional infrastructure"],
                  ["Stale data risk", "Only works for non-critical reads"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
        _solution("Circuit Breaker on Cache Layer",
                  "Bypass cache and query database directly when cache is unreachable.",
                  "Implement circuit breaker that opens when cache errors > 50% over 30s.",
                  ["Prevents timeout waiting for dead cache", "Allows system to continue"],
                  ["Database load increases dramatically", "Performance degradation"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Redis Cluster Mode",
                  "Deploy Redis in cluster mode with data sharding across multiple nodes.",
                  "Enable Redis Cluster with 3 shards + 1 replica each for HA.",
                  ["Data partitioned for scalability", "Individual shard failover", "Higher throughput"],
                  ["More complex configuration", "Cross-slot operations limited"],
                  complexity="High", cost_impact="High", effectiveness="Very High", recommended=False),
        _solution("Local In-Memory Cache Fallback",
                  "Use application-level in-memory cache (Caffeine/Guava) as L1 cache.",
                  "Implement two-tier caching: L1 (in-memory) + L2 (Redis). L1 serves on L2 failure.",
                  ["Instant fallback", "No network dependency", "Reduces Redis load"],
                  ["Limited by instance memory", "Cache inconsistency across instances"],
                  complexity="Medium", cost_impact="Low", effectiveness="Medium", recommended=False),
    ])

    return {
        "scenario":   "Redis cache cluster failure",
        "trigger":    "Redis node failure → all traffic hits database directly",
        "impact":     "High" if scale > 20_000 else "Medium",
        "probability":"Low (99.9% uptime for ElastiCache Multi-AZ)",
        "mitigation": ("ElastiCache Multi-AZ with automatic failover (< 60s). "
                       f"Without cache, DB load increases ~{db_load_increase:.0f}%. "
                       "Fallback: serve stale cache data for non-critical reads (TTL grace period). "
                       "Circuit breaker on cache layer — bypass to DB if Redis unreachable."),
        "detection":  "CloudWatch ElastiCache: CacheHits / (CacheHits + CacheMisses) < 0.7 → alert",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _messaging_lag(scale, arch_type) -> dict:
    throughput = int(scale * 0.1)

    solutions = _rank_solutions([
        _solution("Consumer Group Scaling",
                  "Add more consumers to the consumer group to increase throughput.",
                  "Increase Kafka partitions and add consumer instances. Max consumers = partitions.",
                  ["Linear throughput scaling", "No data loss", "Simple horizontal scaling"],
                  ["Requires partition count increase", "Rebalancing causes brief pause"],
                  complexity="Medium", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Dead Letter Queue (DLQ)",
                  "Route failed messages to a DLQ after max retries to prevent blocking.",
                  "Configure DLQ topic with max 3 retries. Alert on DLQ message count.",
                  ["Prevents poison messages from blocking", "Failed messages preserved for analysis"],
                  ["Messages require manual reprocessing", "Potential data loss if DLQ not monitored"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Backpressure Mechanism",
                  "Slow producer rate when consumer lag exceeds threshold.",
                  "Monitor consumer_lag metric. If > 100K messages, producer applies rate limiting.",
                  ["Prevents runaway lag", "Maintains system stability"],
                  ["Reduces incoming throughput", "Requires producer-side changes"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Event Prioritization",
                  "Process critical events first by using priority queues or separate topics.",
                  "Create high/medium/low priority topics. Route critical events to high-priority topic.",
                  ["Critical events always processed first", "Better user experience"],
                  ["Increases topic complexity", "Routing logic needed"],
                  complexity="Medium", cost_impact="Low", effectiveness="Medium", recommended=False),
    ])

    return {
        "scenario":   f"Kafka consumer lag (>{throughput:,} events/sec backlog)",
        "trigger":    "Consumer group falls behind producer rate — event processing delay",
        "impact":     "High",
        "probability":"Medium under sustained load",
        "mitigation": ("Scale consumer group — add partitions and consumers horizontally. "
                       "Dead-letter queue (DLQ) for failed messages (max 3 retries). "
                       "Backpressure: producer slows if consumer lag > 100K messages. "
                       "Kafka retention: 7 days — no data loss even during extended lag."),
        "detection":  "Kafka metric: consumer_lag > 10,000 messages → PagerDuty alert",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _payment_gateway_timeout() -> dict:
    solutions = _rank_solutions([
        _solution("Retry with Exponential Backoff",
                  "Retry failed payment requests with increasing delays.",
                  "Implement 1s → 2s → 4s backoff with max 3 attempts and idempotency keys.",
                  ["Handles transient failures", "Idempotency prevents double charges"],
                  ["Increases user wait time", "3 retries = ~7s total delay"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Async Payment Processing via Queue",
                  "Process payments asynchronously through a message queue.",
                  "Enqueue payment intent in SQS. Worker processes asynchronously. User sees 'Pending'.",
                  ["No blocking user experience", "Retry logic built into queue", "Better throughput"],
                  ["User doesn't get instant confirmation", "Complex status tracking"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Fallback Payment Provider",
                  "Switch to a secondary payment gateway if primary is unavailable.",
                  "Integrate both Stripe and Razorpay. If primary fails > 3 min, route to secondary.",
                  ["Eliminates single point of failure", "Near-zero payment downtime"],
                  ["Two integrations to maintain", "Reconciliation complexity"],
                  complexity="High", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Circuit Breaker on Payment Service",
                  "Fast-fail payment requests when gateway is known to be down.",
                  "Open circuit after 5 consecutive failures. Show 'Payment temporarily unavailable'.",
                  ["Prevents user frustration from repeated failures", "Reduces load on failing gateway"],
                  ["Users cannot complete purchase", "Revenue impact during downtime"],
                  complexity="Medium", cost_impact="Low", effectiveness="Medium", recommended=False),
        _solution("Payment Intent Caching",
                  "Cache payment intents locally and process when gateway recovers.",
                  "Store payment intents in encrypted local queue. Process batch when gateway returns.",
                  ["No lost transactions", "Users can continue shopping"],
                  ["Security risk of storing payment data", "Complex PCI compliance"],
                  complexity="High", cost_impact="Low", effectiveness="Medium", recommended=False),
    ])

    return {
        "scenario":   "Payment gateway timeout / unavailability",
        "trigger":    "Stripe/Razorpay API returns 5xx or exceeds 30s timeout",
        "impact":     "High",
        "probability":"Low (99.99% SLA from providers)",
        "mitigation": ("Retry with exponential backoff (1s → 2s → 4s, max 3 attempts). "
                       "Idempotency keys on every payment request — prevents duplicate charges. "
                       "Async payment processing via queue — user sees 'pending' state. "
                       "Fallback: secondary payment provider if primary fails > 3 min."),
        "detection":  "Alert on payment API error rate > 1% over 5-min window",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _ml_model_degradation() -> dict:
    solutions = _rank_solutions([
        _solution("Automated Retraining Pipeline",
                  "Automatically retrain models when data drift exceeds threshold.",
                  "Set up MLflow/SageMaker pipeline triggered when PSI > 0.2.",
                  ["Keeps model current", "Automated — no manual work", "Measurable quality"],
                  ["Requires labeled data pipeline", "Compute cost for retraining"],
                  complexity="High", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Shadow Deployment / A-B Testing",
                  "Deploy new model alongside old model to validate before full cutover.",
                  "Route 10% traffic to new model. Compare metrics. Auto-promote if better.",
                  ["Safe validation", "Data-driven promotion", "No risky full cutover"],
                  ["Doubles inference cost during test", "Complex routing logic"],
                  complexity="High", cost_impact="Medium", effectiveness="High", recommended=True),
        _solution("Rule-Based Fallback",
                  "Fall back to simple rule-based system when model confidence is low.",
                  "If model confidence < 0.6, use hand-crafted business rules instead.",
                  ["Instant fallback", "Predictable behavior", "No additional compute"],
                  ["Rules may be less accurate than ML", "Requires maintaining rule set"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
        _solution("Model Monitoring with Alerts",
                  "Continuously monitor model performance metrics and alert on degradation.",
                  "Track accuracy, precision, recall, and drift score. Alert on threshold breach.",
                  ["Early detection of issues", "Data-driven decisions"],
                  ["Doesn't fix the problem — only detects it", "Requires monitoring infrastructure"],
                  complexity="Medium", cost_impact="Low", effectiveness="Medium", recommended=True),
        _solution("Model Ensemble",
                  "Use multiple models and aggregate predictions for robustness.",
                  "Deploy 3 models (different algorithms). Use majority vote or weighted average.",
                  ["More robust predictions", "Reduces individual model risk"],
                  ["3x inference cost", "Complex model management"],
                  complexity="High", cost_impact="High", effectiveness="High", recommended=False),
    ])

    return {
        "scenario":   "ML model accuracy degradation (data drift)",
        "trigger":    "Production data distribution shifts from training data",
        "impact":     "Medium",
        "probability":"High over time without monitoring",
        "mitigation": ("Model monitoring: track prediction distribution weekly vs baseline. "
                       "Automated retraining pipeline triggers when drift score > threshold. "
                       "Shadow deployment: new model serves in parallel before cutover. "
                       "Fallback: rule-based system if model confidence < 0.6."),
        "detection":  "Evidently AI or Arize — alert on PSI (Population Stability Index) > 0.2",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _iot_device_flood(scale) -> dict:
    solutions = _rank_solutions([
        _solution("MQTT Connection Rate Limiting",
                  "Limit device connection rate to prevent thundering herd.",
                  "Set MQTT broker max_connects_per_second: 1000. Devices use jittered retry.",
                  ["Prevents broker overload", "Simple server-side config"],
                  ["Delays device reconnection", "Devices must implement backoff"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Exponential Backoff with Jitter on Devices",
                  "Devices use randomized exponential backoff to spread reconnection over time.",
                  "Device firmware: reconnect_delay = random(0, min(2^attempt, 300)) seconds.",
                  ["Eliminates thundering herd", "No server-side changes needed"],
                  ["Requires firmware update", "Some devices may reconnect slowly"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Edge Message Buffering",
                  "Buffer messages locally on edge devices during cloud disconnect.",
                  "Store messages in local flash/SQLite. Replay to cloud when connected.",
                  ["No data loss during outage", "Devices continue operating"],
                  ["Limited local storage", "Message ordering may be affected"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("AWS IoT Core Horizontal Scaling",
                  "Leverage AWS IoT Core managed service for automatic scaling.",
                  "Use AWS IoT Core which handles millions of connections automatically.",
                  ["Handles massive scale", "Fully managed", "Built-in security"],
                  ["AWS vendor lock-in", "Cost scales with message volume"],
                  complexity="Low", cost_impact="Medium", effectiveness="Very High", recommended=True),
    ])

    return {
        "scenario":   f"IoT device message flood ({scale:,} devices connecting simultaneously)",
        "trigger":    "Mass device reconnect after network outage (thundering herd)",
        "impact":     "High",
        "probability":"Medium (power outage, ISP issue)",
        "mitigation": ("MQTT broker: connection rate limiting — 1,000 connects/sec max. "
                       "Exponential backoff jitter on device reconnect (prevents stampede). "
                       "AWS IoT Core scales horizontally — handles millions of connections. "
                       "Edge layer buffers messages locally during cloud disconnect."),
        "detection":  "AWS IoT Core metric: Connect.Success spike > 5x baseline → alert",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _cascading_service_failure() -> dict:
    solutions = _rank_solutions([
        _solution("Circuit Breaker Pattern",
                  "Stop calling a failing downstream service and return a fallback response.",
                  "Implement Resilience4j circuit breaker. Open after 50% failure rate over 10s.",
                  ["Prevents cascade", "Fast failure", "Protects upstream services"],
                  ["Requires fallback for every dependency", "Circuit must be tuned per service"],
                  complexity="Medium", cost_impact="Low", effectiveness="Very High", recommended=True),
        _solution("Bulkhead Isolation",
                  "Isolate thread pools per downstream dependency to prevent resource exhaustion.",
                  "Allocate separate thread pool (10 threads) per downstream service call.",
                  ["One slow service can't exhaust all threads", "Fault isolation"],
                  ["Reduces total available threads", "Complex thread pool management"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Timeout Budget",
                  "Set strict timeout budgets for all downstream calls.",
                  "Max 500ms per downstream call, 2s total request budget. Kill slow calls.",
                  ["Prevents request pile-up", "Consistent response times"],
                  ["Legitimate slow operations may be killed", "Requires careful tuning"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Service Mesh (Istio/Linkerd)",
                  "Use a service mesh for automatic retry, timeout, and circuit breaking.",
                  "Deploy Istio sidecar proxies. Configure VirtualService policies.",
                  ["Transparent to application", "Centralized policy management"],
                  ["Adds latency (sidecar proxy)", "Complex infrastructure"],
                  complexity="High", cost_impact="Medium", effectiveness="High", recommended=False),
        _solution("Async Communication via Events",
                  "Replace synchronous calls with asynchronous event-driven communication.",
                  "Publish events to Kafka/SQS instead of direct HTTP calls between services.",
                  ["Fully decoupled", "No cascading failures possible", "Better throughput"],
                  ["Eventually consistent", "More complex debugging", "Event schema management"],
                  complexity="High", cost_impact="Medium", effectiveness="Very High", recommended=False),
    ])

    return {
        "scenario":   "Cascading microservice failure (dependency chain)",
        "trigger":    "Service A timeout causes Service B to queue requests → OOM → crash",
        "impact":     "Critical",
        "probability":"Medium in tightly coupled microservices",
        "mitigation": ("Circuit breaker pattern (Resilience4j / Istio) — open after 50% failure rate. "
                       "Bulkhead pattern — isolate thread pools per downstream dependency. "
                       "Timeout budget: max 500ms per downstream call, 2s total request budget. "
                       "Service mesh (Istio) provides automatic retry + timeout enforcement."),
        "detection":  "Distributed tracing (Jaeger / X-Ray): p99 latency spike > 2x baseline",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _serverless_cold_start() -> dict:
    solutions = _rank_solutions([
        _solution("Provisioned Concurrency",
                  "Keep a minimum number of Lambda instances warm to avoid cold starts.",
                  "Set provisioned concurrency = 5-10 for critical API endpoints.",
                  ["Eliminates cold starts for provisioned instances", "Consistent latency"],
                  ["Increases cost significantly", "Loses serverless cost benefits"],
                  complexity="Low", cost_impact="High", effectiveness="Very High", recommended=True),
        _solution("Optimize Package Size",
                  "Reduce deployment package size to speed up cold start initialization.",
                  "Use Lambda Layers. Remove unused dependencies. Use tree-shaking.",
                  ["Faster cold starts (100-300ms improvement)", "No additional cost"],
                  ["Requires dependency audit", "May break if wrong dependencies removed"],
                  complexity="Medium", cost_impact="Low", effectiveness="Medium", recommended=True),
        _solution("Lightweight Runtime",
                  "Use a faster runtime (Node.js or Rust) instead of Python/Java for cold-start-sensitive functions.",
                  "Rewrite critical path functions in Node.js (fastest cold start) or Rust.",
                  ["10-50x faster cold starts", "Lower memory usage"],
                  ["May require rewriting code", "Team must learn new language"],
                  complexity="High", cost_impact="Low", effectiveness="High", recommended=False),
        _solution("Warm-up Scheduler",
                  "Periodically invoke Lambda functions to keep them warm.",
                  "CloudWatch Events rule invokes function every 5 minutes with warm-up event.",
                  ["Simple workaround", "Low cost"],
                  ["Not reliable under scaling", "Doesn't help with new concurrent instances"],
                  complexity="Low", cost_impact="Low", effectiveness="Low", recommended=False),
    ])

    return {
        "scenario":   "Lambda Cold Start Latency",
        "trigger":    "Sudden traffic spike or deployment of new function version",
        "impact":     "Medium",
        "probability":"High on low-traffic endpoints",
        "mitigation": ("Provisioned Concurrency for critical APIs to keep instances warm. "
                       "Optimize deployment package size (reduce dependencies). "
                       "Use lighter runtimes (e.g., Node.js or Rust instead of Java/Python)."),
        "detection":  "X-Ray / CloudWatch: InitDuration metric > 1s",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _api_gateway_throttling() -> dict:
    solutions = _rank_solutions([
        _solution("Request AWS Quota Increase",
                  "Request a service limit increase for API Gateway throughput.",
                  "Submit AWS Support ticket for increased API Gateway limits.",
                  ["More capacity without architecture changes", "Simple solution"],
                  ["Takes 1-3 business days", "May have hard upper limits"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Client-Side Exponential Backoff",
                  "Implement retry with backoff and jitter on the client side.",
                  "Client retries on 429: delay = random(0, min(2^attempt, 60)) seconds.",
                  ["Smooths out request bursts", "Standard HTTP pattern"],
                  ["User experiences delay", "Doesn't increase capacity"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
        _solution("API Gateway Response Caching",
                  "Cache API responses at the gateway level for read-heavy endpoints.",
                  "Enable API Gateway caching with 5-minute TTL for GET endpoints.",
                  ["Reduces backend load by 60-80%", "Faster response times"],
                  ["Stale data for cached endpoints", "Additional cost for cache"],
                  complexity="Low", cost_impact="Medium", effectiveness="High", recommended=True),
    ])

    return {
        "scenario":   "API Gateway Throttling (429 Too Many Requests)",
        "trigger":    "Traffic exceeds account-level or route-level limits (e.g., 10,000 req/s)",
        "impact":     "High",
        "probability":"Medium during viral events",
        "mitigation": ("Implement exponential backoff and jitter on the client side. "
                       "Request AWS quota increase for API Gateway concurrent executions. "
                       "Enable API Gateway caching to absorb read-heavy spikes."),
        "detection":  "CloudWatch API Gateway metric: 4XXError > threshold",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _dynamodb_throttling() -> dict:
    solutions = _rank_solutions([
        _solution("Switch to On-Demand Capacity",
                  "Use DynamoDB on-demand mode for automatic capacity management.",
                  "Change table billing mode to PAY_PER_REQUEST.",
                  ["No capacity planning needed", "Handles any traffic pattern"],
                  ["More expensive per-request than provisioned", "No cost predictability"],
                  complexity="Low", cost_impact="Medium", effectiveness="High", recommended=True),
        _solution("DynamoDB Accelerator (DAX)",
                  "Add DAX in-memory cache for microsecond read latency.",
                  "Deploy DAX cluster with 3 nodes. SDK automatically routes reads through DAX.",
                  ["Microsecond read latency", "Offloads 90%+ reads from DynamoDB"],
                  ["Additional infrastructure cost", "Eventually consistent reads only"],
                  complexity="Medium", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Partition Key Optimization",
                  "Redesign partition keys to distribute load evenly.",
                  "Add suffix/prefix to partition keys (e.g., userId#shard0-9) for uniform distribution.",
                  ["Eliminates hot partitions", "No additional cost"],
                  ["Requires data model changes", "More complex queries"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
    ])

    return {
        "scenario":   "DynamoDB ProvisionedThroughputExceeded",
        "trigger":    "Write/Read operations exceed provisioned capacity or hot partition",
        "impact":     "High",
        "probability":"Medium for spiky workloads",
        "mitigation": ("Use DynamoDB On-Demand capacity for unpredictable workloads. "
                       "Implement DynamoDB Accelerator (DAX) for read-heavy hot keys. "
                       "Ensure partition keys are evenly distributed to avoid hot partitions."),
        "detection":  "CloudWatch DynamoDB metric: ThrottledRequests > 0",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


# ── Edge / Multi-context failures (with solutions) ──────────────────────────

def _edge_communication_blackout() -> dict:
    solutions = _rank_solutions([
        _solution("Store-and-Forward Queue",
                  "Buffer all outbound data locally and transmit when connectivity returns.",
                  "Implement local SQLite-backed queue. Replay on heartbeat recovery.",
                  ["No data loss", "Autonomous operation", "Simple implementation"],
                  ["Local storage limits", "Large sync backlog on recovery"],
                  complexity="Medium", cost_impact="Low", effectiveness="Very High", recommended=True),
        _solution("Autonomous Local Processing",
                  "Continue all processing locally using cached rules and models.",
                  "Edge nodes operate independently with last-known-good configuration.",
                  ["Zero dependency on cloud", "Continuous operation"],
                  ["Decisions based on potentially stale data", "No remote monitoring"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Priority-Based Sync on Recovery",
                  "When connectivity restores, sync critical data first before bulk data.",
                  "Tag data by priority. Sync: critical state → commands → telemetry → logs.",
                  ["Critical data synced first", "Efficient use of limited bandwidth"],
                  ["Complex priority tagging", "Low-priority data delayed"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
    ])

    return {
        "scenario":   "Prolonged Communication Blackout",
        "trigger":    "Satellite or radio link lost for extended duration (> 24 hours)",
        "impact":     "High",
        "probability":"High in remote environments",
        "mitigation": ("Store-and-forward queue accumulates data locally on edge SQLite DB. "
                       "Local processing continues autonomously based on cached rules. "
                       "Prioritize critical state telemetry upon reconnection before bulk sync."),
        "detection":  "Heartbeat timeout > 5 minutes → Trigger autonomous mode",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _edge_node_failure() -> dict:
    solutions = _rank_solutions([
        _solution("N+1 Hardware Redundancy",
                  "Maintain spare edge nodes that can take over immediately.",
                  "Deploy N+1 edge nodes per location. Watchdog transfers workload to spare.",
                  ["Instant failover", "No single point of failure"],
                  ["Higher hardware cost", "Spare node consumes power"],
                  complexity="Medium", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Watchdog Timer Auto-Reboot",
                  "Hardware watchdog automatically reboots locked/crashed nodes.",
                  "Configure hardware watchdog timer with 60s timeout. Hard reboot on expiry.",
                  ["Recovers from software crashes", "No manual intervention needed"],
                  ["Brief service interruption during reboot", "Doesn't fix hardware failures"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Neighbor Node Failover",
                  "Adjacent edge nodes detect failure and absorb workload.",
                  "Implement peer-to-peer heartbeat. On failure, neighbor takes over processing.",
                  ["Automatic load redistribution", "No central coordinator needed"],
                  ["Neighbor node capacity may be insufficient", "Complex coordination"],
                  complexity="High", cost_impact="Low", effectiveness="High", recommended=True),
    ])

    return {
        "scenario":   "Hardware Failure in Isolation",
        "trigger":    "Raspberry Pi / Edge Device crashes due to environment or hardware fault",
        "impact":     "Critical",
        "probability":"Medium",
        "mitigation": ("Redundancy at edge (N+1 physical nodes acting as local cluster). "
                       "Watchdog timer automatically hard-reboots locked nodes. "
                       "Neighbor node takes over processing duties (local failover)."),
        "detection":  "Local network neighbor discovery fails to ping node",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _edge_power_loss() -> dict:
    solutions = _rank_solutions([
        _solution("Battery Backup (UPS)",
                  "Uninterruptible power supply provides bridge power during outages.",
                  "Deploy UPS with 2-4 hour capacity per edge node.",
                  ["Immediate power continuity", "Prevents data loss"],
                  ["Battery degradation over time", "Additional weight and cost"],
                  complexity="Low", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Graceful Degradation",
                  "Disable non-essential sensors and reduce processing to conserve power.",
                  "Power manager disables non-critical subsystems. Priority: life-support > comms > analytics.",
                  ["Extends remaining power", "Critical functions continue"],
                  ["Reduced functionality", "Some data collection paused"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Non-Volatile State Flush",
                  "Flush critical state to flash storage before deep sleep.",
                  "On low-power interrupt, write current state to NVMe/flash. Resume on power restore.",
                  ["No state loss", "Fast recovery on power restore"],
                  ["Flash write cycles limited", "Must complete flush before power dies"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
    ])

    return {
        "scenario":   "Primary Power Loss",
        "trigger":    "Grid failure, solar panel disruption, or battery drain",
        "impact":     "Critical",
        "probability":"High",
        "mitigation": ("Battery backup (UPS) kicks in immediately. "
                       "Graceful degradation: system disables non-essential sensors to preserve power. "
                       "Critical state flushed to non-volatile flash storage before deep sleep."),
        "detection":  "Voltage drop detected on power pin → Trigger power-save interrupt",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _edge_sensor_malfunction() -> dict:
    solutions = _rank_solutions([
        _solution("Outlier Detection Filter",
                  "ML model or statistical filter removes impossible sensor readings.",
                  "Rolling average anomaly detection with 3 std deviation threshold.",
                  ["Catches garbage data", "Prevents bad decisions", "Low compute cost"],
                  ["May filter legitimate extreme readings", "Requires calibration"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Redundant Sensor Cross-Validation",
                  "Cross-validate readings against redundant sensors of the same type.",
                  "Deploy 2-3 sensors per measurement. Accept median value. Alert on > 20% variance.",
                  ["High accuracy", "Detects individual sensor failures"],
                  ["More hardware cost", "More wiring complexity"],
                  complexity="Medium", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Failsafe Action Lock",
                  "Prevent autonomous actions when sensor data quality is uncertain.",
                  "If sensor variance > 20%, lock autonomous actions. Require manual override.",
                  ["Prevents dangerous automated decisions", "Safety-first approach"],
                  ["System becomes manual-only", "Operator must be available"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
    ])

    return {
        "scenario":   "Sensor Malfunction / Data Corruption",
        "trigger":    "Physical damage to sensor array sending garbage data",
        "impact":     "Medium",
        "probability":"High in harsh environments",
        "mitigation": ("Local outlier detection ML model filters impossible readings. "
                       "Cross-validation with redundant sensors. "
                       "Failsafe logic prevents autonomous action if sensor variance > 20%."),
        "detection":  "Rolling average anomaly > 3 std deviations",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _edge_sync_conflict() -> dict:
    solutions = _rank_solutions([
        _solution("CRDTs (Conflict-free Replicated Data Types)",
                  "Use data structures that merge automatically without conflicts.",
                  "Implement CRDTs for shared state. Merge is deterministic and commutative.",
                  ["No conflicts by design", "Works offline", "Deterministic merging"],
                  ["Limited data structure types", "Higher memory usage"],
                  complexity="High", cost_impact="Low", effectiveness="Very High", recommended=True),
        _solution("Vector Clocks for Causality",
                  "Track causal ordering of events to detect and resolve conflicts.",
                  "Attach vector clock to every state update. Compare on sync to detect divergence.",
                  ["Accurate causality tracking", "Detects all conflicts"],
                  ["Vector clock size grows with nodes", "Complex implementation"],
                  complexity="High", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Edge-as-Source-of-Truth",
                  "Edge node always wins for physical state data.",
                  "Conflict resolution policy: edge state = ground truth for sensor/physical data.",
                  ["Simple resolution rule", "Correct for physical systems"],
                  ["Cloud changes overridden", "Only works for physical state"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
    ])

    return {
        "scenario":   "Data Sync Conflict Post-Blackout",
        "trigger":    "Conflicting state changes between cloud and edge during disconnected period",
        "impact":     "Medium",
        "probability":"High",
        "mitigation": ("CRDTs (Conflict-free Replicated Data Types) merge data deterministically. "
                       "Vector clocks trace causality of events. "
                       "Edge node always acts as source-of-truth for physical state."),
        "detection":  "Timestamp overlap during sync payload processing",
        "solutions":  solutions,
        "best_strategy": _best_strategy(solutions),
    }


# ── Multi-context failures ───────────────────────────────────────────────────

def _multi_context_bridge_failure() -> dict:
    solutions = _rank_solutions([
        _solution("Autonomous Mode Activation",
                  "Subsystems gracefully degrade into fully autonomous mode.",
                  "On bridge heartbeat failure, each subsystem activates local-only processing.",
                  ["No dependency on bridge", "Continuous operation", "Pre-programmed fallback"],
                  ["No cross-system data flow", "Subsystems may diverge"],
                  complexity="Medium", cost_impact="Low", effectiveness="Very High", recommended=True),
        _solution("Persistent Queue Dump",
                  "Sync queue dumps to persistent storage and waits for heartbeat recovery.",
                  "Configure sync queue with disk-backed persistence. Resume on reconnection.",
                  ["No data loss", "Automatic recovery"],
                  ["Storage limits on edge", "Large backlog on recovery"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Redundant Bridge Paths",
                  "Maintain multiple communication paths between subsystems.",
                  "Primary: satellite link. Secondary: radio relay. Tertiary: delayed batch transfer.",
                  ["Survives single path failure", "Automatic failover"],
                  ["Higher infrastructure cost", "Complex routing"],
                  complexity="High", cost_impact="High", effectiveness="Very High", recommended=False),
    ])

    return {
        "scenario": "[Cross-System] Integration Bridge Failure",
        "trigger": "DTN link goes down or Sync Queue overflows due to prolonged partition.",
        "impact": "High",
        "probability": "High in interplanetary or deep-edge scenarios",
        "mitigation": "Subsystems gracefully degrade into autonomous mode. Local read/write continues. Sync queue dumps to persistent storage and waits for heartbeat.",
        "detection": "Heartbeat failure between Cloud and Edge gateways.",
        "solutions": solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _multi_context_cloud_outage() -> dict:
    solutions = _rank_solutions([
        _solution("Edge Autonomous Isolation",
                  "Edge systems remain fully operational during cloud outage.",
                  "Edge nodes are designed to operate independently. No cloud dependency for local ops.",
                  ["Zero impact on edge operations", "Pre-built isolation"],
                  ["No cloud features available to edge", "Data accumulates locally"],
                  complexity="Low", cost_impact="Low", effectiveness="Very High", recommended=True),
        _solution("Cloud Multi-AZ Failover",
                  "Cloud system automatically fails over to standby availability zone.",
                  "Configure multi-AZ deployment with automatic failover for all cloud services.",
                  ["Handles AZ-level failures", "Automatic recovery"],
                  ["Does not handle region failures", "Brief interruption during failover"],
                  complexity="Medium", cost_impact="Medium", effectiveness="High", recommended=True),
        _solution("Cloud Auto-Scaling",
                  "Automatically scale cloud resources to handle demand during partial outage.",
                  "Configure aggressive auto-scaling policies with rapid scale-up.",
                  ["Handles capacity issues", "Cost-efficient"],
                  ["Doesn't help with infrastructure failures", "Scaling has delays"],
                  complexity="Low", cost_impact="Medium", effectiveness="Medium", recommended=True),
    ])

    return {
        "scenario": "[Cloud Subsystem] Core Service Outage",
        "trigger": "Microservices dependency failure or database failover.",
        "impact": "High",
        "probability": "Low",
        "mitigation": "Edge systems remain unaffected (autonomous isolation). Cloud system uses auto-scaling and multi-AZ failover.",
        "detection": "CloudWatch / Prometheus synthetic checks.",
        "solutions": solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _multi_context_edge_isolation() -> dict:
    solutions = _rank_solutions([
        _solution("N+1 Edge Redundancy",
                  "Spare edge nodes take over processing when primary fails.",
                  "Maintain N+1 edge hardware. Automatic workload transfer on failure detection.",
                  ["Instant failover", "Continuous critical operations"],
                  ["Higher hardware cost", "Power for spare nodes"],
                  complexity="Medium", cost_impact="Medium", effectiveness="Very High", recommended=True),
        _solution("Safety-Critical Task Prioritization",
                  "Shift safety-critical tasks to highest-priority hardware lane.",
                  "On failure, remaining hardware prioritizes Level 1 (life-critical) tasks only.",
                  ["Life-safety maintained", "Clear priority ordering"],
                  ["Non-critical tasks paused", "Reduced telemetry"],
                  complexity="Medium", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Non-Critical Telemetry Pause",
                  "Pause all non-essential data collection to conserve resources.",
                  "Disable analytics, logging, and bulk telemetry. Resume when capacity restores.",
                  ["Frees compute and storage", "Extends operation time"],
                  ["Data gap in telemetry", "Reduced observability"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
    ])

    return {
        "scenario": "[Edge Subsystem] Node Isolation",
        "trigger": "Local hardware failure or critical power loss.",
        "impact": "Critical",
        "probability": "Medium",
        "mitigation": "N+1 edge redundancy takes over. Safety-critical tasks shifted to highest-priority hardware lane. Non-critical telemetry paused.",
        "detection": "Neighbor node watchdog timeout.",
        "solutions": solutions,
        "best_strategy": _best_strategy(solutions),
    }


def _multi_context_ai_drift() -> dict:
    solutions = _rank_solutions([
        _solution("Last-Known-Good Weights",
                  "Edge AI continues using last successfully synced model weights.",
                  "Store validated model checkpoint locally. Use until new weights can be synced.",
                  ["Continuous inference", "Proven model performance"],
                  ["Model may be outdated", "Accuracy degrades with data shift"],
                  complexity="Low", cost_impact="Low", effectiveness="High", recommended=True),
        _solution("Hardcoded Heuristic Fallback",
                  "Fall back to rule-based heuristics when model confidence drops.",
                  "If inference confidence < 0.5, switch to hand-crafted decision rules.",
                  ["Predictable behavior", "No ML dependency"],
                  ["Less accurate than ML", "Rules may not cover all cases"],
                  complexity="Low", cost_impact="Low", effectiveness="Medium", recommended=True),
        _solution("Compressed Model Update via DTN",
                  "Send compressed model weight deltas over narrow DTN link.",
                  "Compute weight delta (new - old), compress, and transmit. Apply as patch on edge.",
                  ["Smaller transfer size", "Model stays current"],
                  ["Complex delta computation", "May not fit in bandwidth window"],
                  complexity="High", cost_impact="Low", effectiveness="High", recommended=False),
    ])

    return {
        "scenario": "[AI Subsystem] Model Drift & Sync Failure",
        "trigger": "Edge model becomes stale because Cloud cannot push large weight updates over narrow DTN link.",
        "impact": "Medium",
        "probability": "Medium",
        "mitigation": "Edge AI continues using last-known-good weights. Fallback to hardcoded heuristics if confidence score drops below threshold.",
        "detection": "Inference confidence score anomaly.",
        "solutions": solutions,
        "best_strategy": _best_strategy(solutions),
    }
