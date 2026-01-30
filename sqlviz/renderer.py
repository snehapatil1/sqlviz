"""Graphviz rendering layer for SQL visualization."""

from typing import Dict

import graphviz

from sqlviz.model import SQLGraph


def render_graph(graph: SQLGraph) -> str:
    """
    Render SQL graph as SVG using Graphviz.

    Args:
        graph: SQLGraph instance

    Returns:
        SVG string

    Raises:
        ValueError: If graph is empty or SVG generation fails
    """
    # Validate graph has nodes
    if not graph.nodes:
        raise ValueError("Graph has no nodes to render")

    dot = graphviz.Digraph(format="svg", engine="dot")
    dot.attr(rankdir="LR")
    dot.attr(bgcolor="transparent")
    # Native rounded boxes: shape=box, style="rounded,filled" (like digraph example)
    dot.attr("node", shape="box", style="rounded,filled", fontname="Helvetica", fontsize="11")
    dot.attr("edge", fontsize="10", fontcolor="#94a3b8", color="#64748b", penwidth="1.5")

    # Soft, colorful palette for table nodes
    node_colors = [
        "#7dd3fc",  # sky
        "#a5f3fc",  # cyan
        "#bbf7d0",  # green
        "#fde047",  # yellow
        "#fdba74",  # orange
        "#f9a8d4",  # pink
        "#c4b5fd",  # violet
        "#e0e7ff",  # indigo
    ]

    # Render nodes with rounded box + plain text label (multi-line via \n)
    for idx, (table_name, node) in enumerate(graph.nodes.items()):
        color = node_colors[idx % len(node_colors)]
        label = _build_node_label_plain(node)
        label = _escape_dot_label(label)
        dot.node(table_name, label=label, fillcolor=color)

    # Render edges (joins) with soft colors
    for edge in graph.edges:
        label = _build_edge_label(edge)
        dot.edge(edge.from_table, edge.to_table, label=label, color="#94a3b8", fontcolor="#64748b")

    # Generate SVG with error handling
    try:
        # Get DOT source for debugging
        dot_source = dot.source
        
        # Validate DOT source looks reasonable
        if not dot_source or len(dot_source.strip()) == 0:
            raise ValueError("Generated empty DOT source")
        
        svg_bytes = dot.pipe(format="svg")
        svg_str = svg_bytes.decode("utf-8")
    except graphviz.ExecutableNotFound:
        raise ValueError("Graphviz executable not found. Please install Graphviz system package.")
    except graphviz.RequiredArgumentError as e:
        raise ValueError(f"Graphviz argument error: {str(e)}")
    except Exception as e:
        # If pipe fails, include the DOT source in the error
        dot_source = dot.source if hasattr(dot, 'source') else "N/A"
        raise ValueError(f"Failed to generate SVG: {str(e)}\nDOT source:\n{dot_source}")
    
    # Validate we got SVG content
    if not svg_str or len(svg_str.strip()) == 0:
        raise ValueError("Graphviz returned empty SVG")
    
    # Check for error messages in output
    if "Error:" in svg_str or "error" in svg_str.lower():
        raise ValueError(f"Graphviz error in output: {svg_str[:500]}")
    
    # Check if we accidentally got SQL query text instead of SVG
    sql_keywords = ["SELECT", "FROM", "WHERE", "JOIN", "ON"]
    if any(keyword in svg_str.upper() for keyword in sql_keywords) and "<svg" not in svg_str:
        raise ValueError(f"Graphviz returned unexpected content (possibly SQL query): {svg_str[:200]}")
    
    # Extract SVG element from XML document
    # Graphviz returns full XML, but we only need the <svg> element
    if "<svg" in svg_str:
        start = svg_str.find("<svg")
        end = svg_str.rfind("</svg>") + len("</svg>")
        if start >= 0 and end > start:
            svg_str = svg_str[start:end]
            # Ensure xmlns attribute is present for proper rendering
            if 'xmlns=' not in svg_str:
                svg_str = svg_str.replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"', 1)
        else:
            raise ValueError("Could not extract SVG element from Graphviz output")
    else:
        raise ValueError(f"No SVG element found in Graphviz output. Got: {svg_str[:200]}")
    
    # Final validation - ensure we have a valid SVG
    if not svg_str.startswith("<svg"):
        raise ValueError(f"Invalid SVG format. Does not start with <svg. Got: {svg_str[:100]}")
    
    return svg_str


# Separator line between sections inside a node (plain text, no HTML)
_LABEL_SEP = "────────────────"

def _build_node_label_plain(node) -> str:
    """
    Build plain text label for a table node (multi-line with \\n).
    Uses separator lines to distinguish table name, columns, WHERE, GROUP BY.
    """
    lines = [node.name, _LABEL_SEP]

    if node.columns:
        if "*" in node.columns:
            lines.append("(all columns)")
        else:
            for col in node.columns[:5]:
                lines.append(f"  • {col}")
            if len(node.columns) > 5:
                lines.append(f"  ... and {len(node.columns) - 5} more")

    if node.filters:
        lines.append(_LABEL_SEP)
        lines.append("WHERE:")
        for filter_cond in node.filters[:3]:
            filter_text = filter_cond[:40] + "..." if len(filter_cond) > 40 else filter_cond
            lines.append(f"  {filter_text}")
        if len(node.filters) > 3:
            lines.append(f"  ... and {len(node.filters) - 3} more")

    if node.has_aggregation:
        lines.append(_LABEL_SEP)
        lines.append("[GROUP BY]")

    return "\n".join(lines)


def _escape_dot_label(label: str) -> str:
    """Escape backslash and quote for Graphviz DOT label string."""
    label = label.replace("\\", "\\\\")
    label = label.replace('"', '\\"')
    return label


def _build_edge_label(edge) -> str:
    """Build label text for a join edge."""
    join_type_map = {
        "INNER": "INNER JOIN",
        "LEFT": "LEFT JOIN",
        "RIGHT": "RIGHT JOIN",
        "FULL": "FULL JOIN",
    }
    label = join_type_map.get(edge.join_type, edge.join_type)

    if edge.condition:
        # Truncate long conditions
        condition_text = edge.condition[:30] + "..." if len(edge.condition) > 30 else edge.condition
        # Use \n for edge labels (edges handle this better than nodes)
        label += "\\n" + condition_text

    return label
