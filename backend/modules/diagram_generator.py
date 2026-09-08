"""
diagram_generator.py
Generates professional, layered SVG architecture diagrams and Mermaid code from graph data.
All diagrams are dynamically generated from graph nodes/edges — nothing hardcoded.
"""

import math


# ── Color scheme per node group ──────────────────────────────────────────────
GROUP_COLORS = {
    "presentation":  {"fill": "#EEEDFE", "stroke": "#7F77DD", "text": "#3C3489", "bg": "rgba(127,119,221,0.06)"},
    "application":   {"fill": "#E1F5EE", "stroke": "#1D9E75", "text": "#085041", "bg": "rgba(29,158,117,0.06)"},
    "data":          {"fill": "#FAEEDA", "stroke": "#BA7517", "text": "#633806", "bg": "rgba(186,117,23,0.06)"},
    "messaging":     {"fill": "#E6F1FB", "stroke": "#378ADD", "text": "#0C447C", "bg": "rgba(55,138,221,0.06)"},
    "edge":          {"fill": "#EAF3DE", "stroke": "#639922", "text": "#27500A", "bg": "rgba(99,153,34,0.06)"},
    "ai":            {"fill": "#FBEAF0", "stroke": "#D4537E", "text": "#72243E", "bg": "rgba(212,83,126,0.06)"},
    "external":      {"fill": "#F1EFE8", "stroke": "#888780", "text": "#444441", "bg": "rgba(136,135,128,0.06)"},
    "infrastructure":{"fill": "#F1EFE8", "stroke": "#5F5E5A", "text": "#2C2C2A", "bg": "rgba(95,94,90,0.06)"},
    "security":      {"fill": "#FEF3C7", "stroke": "#D97706", "text": "#92400E", "bg": "rgba(217,119,6,0.06)"},
    "devops":        {"fill": "#DBEAFE", "stroke": "#2563EB", "text": "#1E3A5F", "bg": "rgba(37,99,235,0.06)"},
    "monitoring":    {"fill": "#F0FDF4", "stroke": "#16A34A", "text": "#14532D", "bg": "rgba(22,163,74,0.06)"},
}

MERMAID_STYLES = {
    "presentation":  "fill:#EEEDFE,stroke:#7F77DD,color:#3C3489",
    "application":   "fill:#E1F5EE,stroke:#1D9E75,color:#085041",
    "data":          "fill:#FAEEDA,stroke:#BA7517,color:#633806",
    "messaging":     "fill:#E6F1FB,stroke:#378ADD,color:#0C447C",
    "edge":          "fill:#EAF3DE,stroke:#639922,color:#27500A",
    "ai":            "fill:#FBEAF0,stroke:#D4537E,color:#72243E",
    "external":      "fill:#F1EFE8,stroke:#888780,color:#444441",
    "infrastructure":"fill:#F1EFE8,stroke:#5F5E5A,color:#2C2C2A",
    "security":      "fill:#FEF3C7,stroke:#D97706,color:#92400E",
    "devops":        "fill:#DBEAFE,stroke:#2563EB,color:#1E3A5F",
    "monitoring":    "fill:#F0FDF4,stroke:#16A34A,color:#14532D",
}

# Icons for component types
LAYER_ICONS = {
    "frontend":   "🌐",
    "mobile":     "📱",
    "cdn":        "⚡",
    "api":        "🔗",
    "gateway":    "🚪",
    "auth":       "🔐",
    "backend":    "⚙️",
    "service":    "⚙️",
    "compute":    "💻",
    "database":   "💾",
    "cache":      "⚡",
    "storage":    "📦",
    "messaging":  "📨",
    "kafka":      "📨",
    "websocket":  "🔌",
    "queue":      "📬",
    "ai":         "🤖",
    "ml":         "🧠",
    "iot":        "📡",
    "edge":       "🖥️",
    "broker":     "📡",
    "video":      "🎬",
    "streaming":  "📺",
    "monitor":    "📊",
    "observ":     "📊",
    "security":   "🛡️",
    "safety":     "🛡️",
    "failover":   "♻️",
    "routing":    "🌍",
    "region":     "🌍",
    "replica":    "🔄",
    "integration":"🔗",
    "sync":       "🔄",
    "power":      "🔋",
    "sensor":     "📡",
}

# Layer grouping display names and order
LAYER_DISPLAY = {
    "presentation":  "PRESENTATION LAYER",
    "application":   "APPLICATION LAYER",
    "security":      "SECURITY LAYER",
    "messaging":     "MESSAGING & EVENTS",
    "ai":            "AI / ML SERVICES",
    "data":          "DATA LAYER",
    "edge":          "EDGE / IoT LAYER",
    "external":      "EXTERNAL SERVICES",
    "infrastructure":"INFRASTRUCTURE",
    "devops":        "CI/CD & DEVOPS",
    "monitoring":    "MONITORING & OBSERVABILITY",
}


def generate_diagrams(graph: dict, architecture: dict, features: dict) -> dict:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    svg     = _generate_svg(nodes, edges, architecture, features)
    mermaid = _generate_mermaid(nodes, edges, architecture)

    return {
        "svg":     svg,
        "mermaid": mermaid,
    }


def _get_icon(label: str) -> str:
    """Get a relevant icon for a component label."""
    lower = label.lower()
    for key, icon in LAYER_ICONS.items():
        if key in lower:
            return icon
    return "◆"


# ─────────────────────────────────────────────────────────────────────────────
# SVG GENERATION — Professional Layered Architecture Diagram
# ─────────────────────────────────────────────────────────────────────────────

def _generate_svg(nodes: list, edges: list, architecture: dict, features: dict) -> str:
    if not nodes:
        return "<svg viewBox='0 0 400 200'><text x='200' y='100' text-anchor='middle'>No nodes</text></svg>"

    # Group nodes by layer group
    groups = {}
    for n in nodes:
        g = n.get("group", "infrastructure")
        groups.setdefault(g, []).append(n)

    group_order = ["presentation", "application", "security", "messaging", "ai",
                   "data", "edge", "external", "infrastructure", "devops", "monitoring"]
    ordered_groups = [g for g in group_order if g in groups]
    for g in groups:
        if g not in ordered_groups:
            ordered_groups.append(g)

    # Layout constants
    SVG_W        = 1000
    BOX_W        = 160
    BOX_H        = 56
    ROW_GAP      = 28       # vertical gap between group rows
    COL_GAP      = 20       # horizontal gap between nodes in same row
    MARGIN_Y     = 60
    MARGIN_X     = 30
    GROUP_PAD_X  = 16
    GROUP_PAD_Y  = 32
    GROUP_HEADER = 24
    TITLE_HEIGHT = 50

    # Compute positions
    positions = {}
    y = MARGIN_Y + TITLE_HEIGHT
    group_bounds = {}   # group_name → (x, y, w, h)

    for group_name in ordered_groups:
        group_nodes = groups[group_name]
        n = len(group_nodes)

        # Calculate row width
        row_w = n * BOX_W + (n - 1) * COL_GAP
        max_row_w = SVG_W - 2 * MARGIN_X - 2 * GROUP_PAD_X

        # If nodes overflow, wrap to multiple rows
        if row_w > max_row_w:
            cols = max(1, int((max_row_w + COL_GAP) / (BOX_W + COL_GAP)))
        else:
            cols = n

        rows_count = math.ceil(n / cols)
        actual_row_w = min(n, cols) * BOX_W + (min(n, cols) - 1) * COL_GAP

        group_x = (SVG_W - actual_row_w) / 2 - GROUP_PAD_X
        group_y = y
        group_w = actual_row_w + 2 * GROUP_PAD_X
        group_h = rows_count * (BOX_H + ROW_GAP) - ROW_GAP + GROUP_HEADER + 2 * GROUP_PAD_Y

        group_bounds[group_name] = (group_x, group_y, group_w, group_h)

        node_y = y + GROUP_HEADER + GROUP_PAD_Y

        for i, node in enumerate(group_nodes):
            row = i // cols
            col = i % cols
            items_in_row = min(cols, n - row * cols)
            row_start_x = (SVG_W - (items_in_row * BOX_W + (items_in_row - 1) * COL_GAP)) / 2
            x = row_start_x + col * (BOX_W + COL_GAP)
            ny = node_y + row * (BOX_H + ROW_GAP)
            positions[node["id"]] = (x + BOX_W / 2, ny + BOX_H / 2)

        y += group_h + ROW_GAP

    SVG_H = y + MARGIN_Y

    # Build SVG
    arch_type = architecture.get("architecture", "Architecture")

    svg_parts = [
        f'<svg viewBox="0 0 {SVG_W} {SVG_H}" xmlns="http://www.w3.org/2000/svg" '
        f'style="width:100%;background:#fafafa;border-radius:12px;font-family:Inter,system-ui,sans-serif">',
    ]

    # Defs: arrowhead markers, filters
    svg_parts.append('''<defs>
  <marker id="arr" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
    <path d="M0,0 L0,8 L10,4 z" fill="#94A3B8"/>
  </marker>
  <filter id="shadow" x="-4%" y="-4%" width="108%" height="112%">
    <feDropShadow dx="0" dy="2" stdDeviation="3" flood-opacity="0.08"/>
  </filter>
  <linearGradient id="titleGrad" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="#6366F1"/>
    <stop offset="100%" stop-color="#06B6D4"/>
  </linearGradient>
</defs>''')

    # Title bar
    svg_parts.append(
        f'<rect x="0" y="0" width="{SVG_W}" height="{TITLE_HEIGHT}" fill="#1E293B" rx="12" />'
        f'<rect x="0" y="12" width="{SVG_W}" height="{TITLE_HEIGHT - 12}" fill="#1E293B" />'
    )
    svg_parts.append(
        f'<text x="{MARGIN_X}" y="{TITLE_HEIGHT/2 + 5}" '
        f'font-size="15" font-weight="700" fill="white" letter-spacing="0.5">'
        f'⚡ {arch_type}</text>'
    )
    svg_parts.append(
        f'<text x="{SVG_W - MARGIN_X}" y="{TITLE_HEIGHT/2 + 5}" text-anchor="end" '
        f'font-size="11" fill="#94A3B8">ARCHON AI — System Architecture</text>'
    )

    # Draw group backgrounds
    for group_name in ordered_groups:
        if group_name not in group_bounds:
            continue
        gx, gy, gw, gh = group_bounds[group_name]
        colors = GROUP_COLORS.get(group_name, GROUP_COLORS["infrastructure"])
        display_name = LAYER_DISPLAY.get(group_name, group_name.upper())

        # Group background rect
        svg_parts.append(
            f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{gw:.1f}" height="{gh:.1f}" '
            f'rx="8" fill="{colors["bg"]}" stroke="{colors["stroke"]}" '
            f'stroke-width="0.5" stroke-dasharray="4,4" opacity="0.8"/>'
        )
        # Group label
        svg_parts.append(
            f'<text x="{gx + 12:.1f}" y="{gy + 18:.1f}" '
            f'font-size="9" fill="{colors["stroke"]}" font-weight="700" '
            f'letter-spacing="1.5" text-transform="uppercase">'
            f'{display_name}</text>'
        )

    # Draw edges (behind nodes)
    for edge in edges:
        src_id = edge.get("from")
        dst_id = edge.get("to")
        if src_id not in positions or dst_id not in positions:
            continue
        x1, y1 = positions[src_id]
        x2, y2 = positions[dst_id]
        label  = edge.get("label", "")

        # Calculate direction and offset to box borders
        dx, dy = x2 - x1, y2 - y1

        # Determine if edge is primarily vertical or horizontal
        if abs(dy) > abs(dx):
            # Vertical: offset from top/bottom
            oy_start = BOX_H / 2 + 2
            oy_end = BOX_H / 2 + 2
            ox_start = 0
            ox_end = 0
            if dy < 0:
                oy_start = -oy_start
                oy_end = -oy_end
        else:
            # Horizontal: offset from left/right
            ox_start = BOX_W / 2 + 2
            ox_end = BOX_W / 2 + 2
            oy_start = 0
            oy_end = 0
            if dx < 0:
                ox_start = -ox_start
                ox_end = -ox_end

        ex1 = x1 + (ox_start if dx >= 0 else -ox_start)
        ey1 = y1 + (oy_start if dy >= 0 else -oy_start)
        ex2 = x2 - (ox_end if dx >= 0 else -ox_end)
        ey2 = y2 - (oy_end if dy >= 0 else -oy_end)

        # Use curved paths for better visual
        mid_y = (ey1 + ey2) / 2
        svg_parts.append(
            f'<path d="M{ex1:.1f},{ey1:.1f} C{ex1:.1f},{mid_y:.1f} {ex2:.1f},{mid_y:.1f} {ex2:.1f},{ey2:.1f}" '
            f'stroke="#CBD5E1" stroke-width="1.2" fill="none" '
            f'marker-end="url(#arr)"/>'
        )

        # Edge label at midpoint
        if label:
            mx = (ex1 + ex2) / 2
            my = (ey1 + ey2) / 2
            svg_parts.append(
                f'<rect x="{mx-35:.1f}" y="{my-8:.1f}" width="70" height="14" rx="3" '
                f'fill="white" stroke="#E2E8F0" stroke-width="0.5"/>'
                f'<text x="{mx:.1f}" y="{my+3:.1f}" text-anchor="middle" '
                f'font-size="7" fill="#64748B" font-weight="500">{label[:20]}</text>'
            )

    # Draw nodes
    for group_name in ordered_groups:
        group_nodes = groups[group_name]
        colors = GROUP_COLORS.get(group_name, GROUP_COLORS["infrastructure"])

        for node in group_nodes:
            nid = node["id"]
            if nid not in positions:
                continue
            cx, cy = positions[nid]
            x = cx - BOX_W / 2
            y_pos = cy - BOX_H / 2

            label_text = node.get("label", node["id"])
            tech_text  = node.get("tech", "")
            icon = _get_icon(label_text)

            # Node card with shadow
            svg_parts.append(
                f'<rect x="{x:.1f}" y="{y_pos:.1f}" width="{BOX_W}" height="{BOX_H}" '
                f'rx="8" fill="white" stroke="{colors["stroke"]}" stroke-width="1.2" '
                f'filter="url(#shadow)"/>'
            )
            # Color accent bar on left
            svg_parts.append(
                f'<rect x="{x:.1f}" y="{y_pos:.1f}" width="4" height="{BOX_H}" '
                f'rx="2" fill="{colors["stroke"]}"/>'
            )
            # Icon + Label
            svg_parts.append(
                f'<text x="{x + 14:.1f}" y="{y_pos + 22:.1f}" '
                f'font-size="11" font-weight="600" fill="{colors["text"]}">'
                f'{icon} {_truncate(label_text, 18)}</text>'
            )
            # Tech text
            if tech_text:
                svg_parts.append(
                    f'<text x="{x + 14:.1f}" y="{y_pos + 38:.1f}" '
                    f'font-size="8.5" fill="#64748B" font-weight="400">'
                    f'{_truncate(tech_text, 24)}</text>'
                )

    # Footer
    svg_parts.append(
        f'<rect x="0" y="{SVG_H - 30}" width="{SVG_W}" height="30" fill="#F8FAFC" rx="0"/>'
    )
    svg_parts.append(
        f'<text x="{SVG_W/2:.1f}" y="{SVG_H - 10:.1f}" text-anchor="middle" '
        f'font-size="9" fill="#94A3B8" font-weight="500">'
        f'Generated by Archon AI — {arch_type}</text>'
    )

    svg_parts.append('</svg>')
    return "\n".join(svg_parts)


def _truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis for SVG labels."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 1] + "…"


# ─────────────────────────────────────────────────────────────────────────────
# MERMAID GENERATION
# ─────────────────────────────────────────────────────────────────────────────

def _generate_mermaid(nodes: list, edges: list, architecture: dict) -> str:
    lines = ["graph TD"]

    # Sanitize node id for mermaid (alphanumeric + underscore only)
    def mid(node_id):
        return node_id.replace("-", "_").replace(".", "_").replace(" ", "_").replace("/", "_")

    # Group nodes into subgraphs
    groups = {}
    for node in nodes:
        g = node.get("group", "infrastructure")
        groups.setdefault(g, []).append(node)

    group_order = ["presentation", "application", "security", "messaging", "ai",
                   "data", "edge", "external", "infrastructure", "devops", "monitoring"]

    for group_name in group_order:
        if group_name not in groups:
            continue
        display_name = LAYER_DISPLAY.get(group_name, group_name.upper())
        lines.append(f"  subgraph {mid(group_name)}[\"{display_name}\"]")
        for node in groups[group_name]:
            nid   = mid(node["id"])
            label = node.get("label", node["id"])
            tech  = node.get("tech", "")
            icon  = _get_icon(label)
            lines.append(f'    {nid}["{icon} {label}<br/><small>{tech[:25]}</small>"]')
        lines.append("  end")
        lines.append("")

    # Handle any remaining groups not in the order
    for group_name, gnodes in groups.items():
        if group_name in group_order:
            continue
        display_name = LAYER_DISPLAY.get(group_name, group_name.upper())
        lines.append(f"  subgraph {mid(group_name)}[\"{display_name}\"]")
        for node in gnodes:
            nid   = mid(node["id"])
            label = node.get("label", node["id"])
            tech  = node.get("tech", "")
            icon  = _get_icon(label)
            lines.append(f'    {nid}["{icon} {label}<br/><small>{tech[:25]}</small>"]')
        lines.append("  end")
        lines.append("")

    # Edge declarations
    for edge in edges:
        src = mid(edge.get("from", ""))
        dst = mid(edge.get("to", ""))
        lbl = edge.get("label", "")
        if src and dst:
            if lbl:
                lines.append(f'  {src} -->|"{lbl}"| {dst}')
            else:
                lines.append(f'  {src} --> {dst}')

    lines.append("")

    # Style declarations per group
    styled = set()
    for node in nodes:
        nid   = mid(node["id"])
        group = node.get("group", "infrastructure")
        style = MERMAID_STYLES.get(group, MERMAID_STYLES["infrastructure"])
        if nid not in styled:
            lines.append(f'  style {nid} {style}')
            styled.add(nid)

    return "\n".join(lines)
