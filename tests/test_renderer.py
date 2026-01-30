"""Tests for graph renderer."""

from sqlviz.model import SQLGraph, TableNode
from sqlviz.renderer import render_graph


def test_render_simple_graph():
    """Test rendering a simple graph."""
    graph = SQLGraph()
    graph.add_table("users")
    svg = render_graph(graph)
    assert "svg" in svg.lower()
    assert "users" in svg


def test_render_graph_with_join():
    """Test rendering graph with join."""
    graph = SQLGraph()
    graph.add_table("users")
    graph.add_table("orders")
    graph.add_join("users", "orders", "INNER", "users.id = orders.user_id")
    svg = render_graph(graph)
    assert "svg" in svg.lower()
    assert "users" in svg
    assert "orders" in svg
