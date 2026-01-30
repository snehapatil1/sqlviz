"""Generate a sample SVG diagram to show expected output format."""

from sqlviz.model import SQLGraph, TableNode
from sqlviz.renderer import render_graph

# Create a sample graph
graph = SQLGraph()

# Add users table
users_node = graph.add_table("users")
users_node.add_column("id")
users_node.add_column("name")
users_node.add_column("email")
users_node.add_filter("users.active = 1")

# Add orders table
orders_node = graph.add_table("orders")
orders_node.add_column("id")
orders_node.add_column("total")
orders_node.add_column("status")

# Add join
graph.add_join("users", "orders", "INNER", "users.id = orders.user_id")

# Render to SVG
svg = render_graph(graph)

# Save to file
with open("sample_output.svg", "w") as f:
    f.write(svg)

print("Sample SVG saved to sample_output.svg")
print("Open this file in a web browser to see the diagram!")
