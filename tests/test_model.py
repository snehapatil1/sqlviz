"""Tests for graph model."""

from sqlviz.model import SQLGraph, build_graph


def test_build_graph_simple():
    """Test building graph from simple query."""
    parsed = {
        "tables": ["users"],
        "joins": [],
        "selected_columns": {"users": ["id", "name"]},
        "filters": {},
        "group_by": None,
    }
    graph = build_graph(parsed)
    assert "users" in graph.nodes
    assert len(graph.edges) == 0


def test_build_graph_with_join():
    """Test building graph with join."""
    parsed = {
        "tables": ["users", "orders"],
        "joins": [{"type": "INNER", "table": "orders", "condition": "users.id = orders.user_id"}],
        "selected_columns": {"users": ["id"], "orders": ["total"]},
        "filters": {},
        "group_by": None,
    }
    graph = build_graph(parsed)
    assert "users" in graph.nodes
    assert "orders" in graph.nodes
    assert len(graph.edges) == 1


def test_build_graph_with_filters():
    """Test building graph with filters."""
    parsed = {
        "tables": ["users"],
        "joins": [],
        "selected_columns": {"users": ["id"]},
        "filters": {"users": ["users.active = 1"]},
        "group_by": None,
    }
    graph = build_graph(parsed)
    assert len(graph.nodes["users"].filters) > 0
