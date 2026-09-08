"""
feature_extractor.py
Rule-based NLP feature extraction from project description text.
No LLM used here — pure keyword detection and heuristics.
"""

import re
from dataclasses import dataclass, asdict
from typing import Optional


REALTIME_KEYWORDS = [
    "real-time", "realtime", "live", "streaming", "websocket", "socket.io",
    "chat", "tracking", "gps", "notifications", "push", "event-driven",
    "instant", "broadcast", "pubsub", "pub-sub", "kafka", "rabbitmq"
]

PAYMENT_KEYWORDS = [
    "payment", "pay", "stripe", "razorpay", "billing", "subscription",
    "checkout", "invoice", "transaction", "wallet", "upi", "credit card",
    "debit card", "paypal", "fintech", "money", "purchase", "order"
]

AI_KEYWORDS = [
    "ai", "ml", "machine learning", "deep learning", "nlp", "recommendation",
    "chatbot", "gpt", "llm", "neural", "prediction", "classification",
    "detection", "recognition", "computer vision", "generative", "bert",
    "sentiment"
]

IOT_KEYWORDS = [
    "iot", "sensor", "device", "embedded", "raspberry", "arduino", "mqtt",
    "edge", "hardware", "smart home", "wearable", "beacon", "firmware",
    "telemetry", "sensors", "devices", "edge nodes", "device monitoring", "environmental data collection"
]

MOBILE_KEYWORDS = [
    "mobile", "android", "ios", "app", "flutter", "react native", "swift",
    "kotlin", "phone", "tablet", "apk"
]

# Scale entity words — users, devices, homes, sensors, etc.
_SCALE_ENTITIES = r"(?:users?|concurrent|active|devices?|homes?|sensors?|clients?|endpoints?|students?|customers?|events/sec|events?)"

SCALE_PATTERNS = [
    # e.g. "5 million users", "5M devices"
    (r"(\d+)\s*(?:million|m)\s*" + _SCALE_ENTITIES,         lambda m: int(m.group(1)) * 1_000_000),
    # e.g. "50K homes", "200k devices"
    (r"(\d+)\s*k\s*" + _SCALE_ENTITIES,                      lambda m: int(m.group(1)) * 1_000),
    # e.g. "50,000 users"
    (r"(\d{1,3}(?:,\d{3})+)\s*" + _SCALE_ENTITIES,          lambda m: int(m.group(1).replace(',', ''))),
    # e.g. "50000 users"
    (r"(\d+)\s*(?:thousand)\s*" + _SCALE_ENTITIES,           lambda m: int(m.group(1)) * 1_000),
    # plain number + entity
    (r"(\d+)\s*" + _SCALE_ENTITIES,                          lambda m: int(m.group(1))),
    # bare words
    (r"million\s*" + _SCALE_ENTITIES,                        lambda m: 1_000_000),
    (r"large\s*scale|enterprise|massive",                    lambda m: 500_000),
    (r"medium\s*scale|growing",                              lambda m: 50_000),
    (r"small\s*scale|startup|mvp",                           lambda m: 5_000),
]

SECURITY_KEYWORDS = [
    "hipaa", "gdpr", "pci", "compliance", "healthcare", "medical", "hospital",
    "bank", "financial", "government", "sensitive", "encrypted", "audit"
]

MICROSERVICES_KEYWORDS = [
    "microservice", "distributed", "multi-tenant", "saas", "enterprise",
    "scalable", "high availability", "fault tolerant", "modular",
    "kafka", "ec2", "fastapi", "spring boot", "docker", "kubernetes", "k8s"
]

VIDEO_KEYWORDS = [
    "video", "streaming", "rtmp", "hls", "dash", "medialive", "ffmpeg",
    "vod", "livestream", "broadcasting"
]

GLOBAL_KEYWORDS = [
    "global", "multi-region", "geo-routing", "worldwide", "international",
    "cross-region"
]

OFFLINE_KEYWORDS = [
    "no internet", "intermittent connectivity", "high latency", "remote environment",
    "space", "mars", "disaster", "rural", "autonomous system", "life-support",
    "critical system", "offline", "disconnected"
]


@dataclass
class ExtractedFeatures:
    real_time: bool
    payments: bool
    ai_required: bool
    iot: bool
    platform: str          # web | mobile | ai | iot | hybrid
    scale: int             # estimated concurrent users
    scale_label: str       # startup | mid | large | enterprise
    security_critical: bool
    microservices_hint: bool
    video_streaming: bool
    global_deployment: bool
    edge_offline: bool
    multi_context: bool
    subsystem_scales: dict
    keywords_found: dict


def extract_features(text: str) -> dict:
    t = text.lower()

    real_time = _any_keyword(t, REALTIME_KEYWORDS)
    payments  = _any_keyword(t, PAYMENT_KEYWORDS)
    ai_req    = _any_keyword(t, AI_KEYWORDS)
    iot       = _any_keyword(t, IOT_KEYWORDS)
    mobile    = _any_keyword(t, MOBILE_KEYWORDS)
    security  = _any_keyword(t, SECURITY_KEYWORDS)
    ms_hint   = _any_keyword(t, MICROSERVICES_KEYWORDS)
    video     = _any_keyword(t, VIDEO_KEYWORDS)
    global_d  = _any_keyword(t, GLOBAL_KEYWORDS)
    offline   = _any_keyword(t, OFFLINE_KEYWORDS)

    scale = _extract_scale(t)
    scale_label = _scale_label(scale)

    if offline or iot:
        platform = "iot"
    elif ai_req and not mobile:
        platform = "ai"
    elif mobile:
        platform = "mobile"
    else:
        platform = "web"

    if mobile and (iot or offline or ai_req):
        platform = "hybrid"

    # Multi-context detection
    raw_envs = []
    for env in ["earth", "mars", "cloud", "edge", "remote", "offline", "intermittent"]:
        if env in t:
            raw_envs.append(env)
            
    unique_subsystems = {}
    for e in raw_envs:
        if e in ["earth", "cloud"]:
            unique_subsystems["Earth/Cloud"] = e
        elif e in ["mars"]:
            unique_subsystems["Mars"] = e
        elif e in ["remote", "edge"]:
            unique_subsystems["Remote/Edge"] = e
            
    if not unique_subsystems:
        if offline or iot:
            unique_subsystems["Edge"] = "edge"
        else:
            unique_subsystems["Cloud"] = "cloud"

    multi_context = len(unique_subsystems) > 1

    subsystem_scales = {}
    for sub_name, kw in unique_subsystems.items():
        idx = t.find(kw)
        chunk = t[max(0, idx-40):idx+120] if idx != -1 else t
        extracted = _extract_scale(chunk)
        if extracted != 10_000:
            subsystem_scales[sub_name] = extracted
        else:
            if "Earth" in sub_name or "Cloud" in sub_name:
                subsystem_scales[sub_name] = 1_000_000
            else:
                subsystem_scales[sub_name] = 10_000

    features = ExtractedFeatures(
        real_time=real_time,
        payments=payments,
        ai_required=ai_req,
        iot=iot,
        platform=platform,
        scale=scale,
        scale_label=scale_label,
        security_critical=security,
        microservices_hint=ms_hint,
        video_streaming=video,
        global_deployment=global_d,
        edge_offline=offline,
        multi_context=multi_context,
        subsystem_scales=subsystem_scales,
        keywords_found={
            "real_time": _matched_keywords(t, REALTIME_KEYWORDS),
            "payments":  _matched_keywords(t, PAYMENT_KEYWORDS),
            "ai":        _matched_keywords(t, AI_KEYWORDS),
            "iot":       _matched_keywords(t, IOT_KEYWORDS),
            "security":  _matched_keywords(t, SECURITY_KEYWORDS),
            "video":     _matched_keywords(t, VIDEO_KEYWORDS),
            "global":    _matched_keywords(t, GLOBAL_KEYWORDS),
            "offline":   _matched_keywords(t, OFFLINE_KEYWORDS),
        }
    )
    return asdict(features)


def _any_keyword(text: str, keywords: list) -> bool:
    return any(kw in text for kw in keywords)


def _matched_keywords(text: str, keywords: list) -> list:
    return [kw for kw in keywords if kw in text]


def _extract_scale(text: str) -> int:
    for pattern, extractor in SCALE_PATTERNS:
        m = re.search(pattern, text)
        if m:
            try:
                return extractor(m)
            except Exception:
                continue
    return 10_000  # default: mid-tier


def _scale_label(scale: int) -> str:
    if scale < 10_000:
        return "startup"
    if scale < 100_000:
        return "mid"
    if scale < 1_000_000:
        return "large"
    return "enterprise"
