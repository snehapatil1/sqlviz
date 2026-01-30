"""Integration tests for full pipeline."""

from sqlviz.model import build_graph
from sqlviz.parser import parse_sql
from sqlviz.renderer import render_graph


def test_full_pipeline():
    """Test complete pipeline from SQL to SVG."""
    sql = "SELECT users.id, users.name FROM users WHERE users.active = 1"
    
    # Parse
    parsed = parse_sql(sql)
    assert "users" in parsed["tables"]
    
    # Build graph
    graph = build_graph(parsed)
    assert "users" in graph.nodes
    
    # Render
    svg = render_graph(graph)
    assert "svg" in svg.lower()
    assert "users" in svg


def test_full_pipeline_with_join():
    """Test complete pipeline with join."""
    sql = "SELECT users.id, orders.total FROM users INNER JOIN orders ON users.id = orders.user_id"
    
    # Parse
    parsed = parse_sql(sql)
    assert "users" in parsed["tables"]
    assert len(parsed["joins"]) > 0
    
    # Build graph
    graph = build_graph(parsed)
    assert len(graph.edges) > 0
    
    # Render
    svg = render_graph(graph)
    assert "svg" in svg.lower()
