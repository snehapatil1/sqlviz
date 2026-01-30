"""Graph model layer for SQL visualization."""

import re
from typing import Dict, List, Optional, Set


class TableNode:
    """Represents a table node in the graph."""

    def __init__(self, name: str):
        self.name = name
        self.columns: List[str] = []
        self.filters: List[str] = []
        self.has_aggregation: bool = False

    def add_column(self, column: str) -> None:
        """Add a selected column."""
        if column not in self.columns:
            self.columns.append(column)

    def add_filter(self, filter_condition: str) -> None:
        """Add a WHERE filter condition."""
        if filter_condition not in self.filters:
            self.filters.append(filter_condition)

    def set_aggregation(self, has_agg: bool) -> None:
        """Mark if this table has aggregation."""
        self.has_aggregation = has_agg


class JoinEdge:
    """Represents a join edge in the graph."""

    def __init__(self, from_table: str, to_table: str, join_type: str, condition: str):
        self.from_table = from_table
        self.to_table = to_table
        self.join_type = join_type
        self.condition = condition


class SQLGraph:
    """Graph representation of SQL query."""

    def __init__(self):
        self.nodes: Dict[str, TableNode] = {}
        self.edges: List[JoinEdge] = []

    def add_table(self, table_name: str) -> TableNode:
        """Add a table node."""
        if table_name not in self.nodes:
            self.nodes[table_name] = TableNode(table_name)
        return self.nodes[table_name]

    def add_join(self, from_table: str, to_table: str, join_type: str, condition: str) -> None:
        """Add a join edge."""
        self.add_table(from_table)
        self.add_table(to_table)
        self.edges.append(JoinEdge(from_table, to_table, join_type, condition))

    def get_all_tables(self) -> Set[str]:
        """Get all table names in the graph."""
        return set(self.nodes.keys())


def build_graph(parsed: Dict) -> SQLGraph:
    """
    Convert parsed SQL into graph model.

    Args:
        parsed: Parsed SQL dictionary from parser

    Returns:
        SQLGraph instance
    """
    graph = SQLGraph()

    # Add all tables
    for table in parsed["tables"]:
        graph.add_table(table)

    # Add joins
    # Track tables in order (for sequential joins)
    added_tables_set = set(parsed["tables"])
    added_tables_list = list(parsed["tables"])  # Preserve order
    
    for join in parsed["joins"]:
        to_table = join.get("table", "").strip()
        if not to_table:
            continue  # Skip invalid joins
            
        join_condition = join.get("condition", "") or ""
        
        # Determine from_table by parsing the join condition
        # Join conditions typically have format: "table1.column = table2.column"
        # The from_table is the one that's already in the graph
        from_table = None
        
        if join_condition:
            # Extract table names from join condition (format: table.column)
            table_pattern = r'(\w+)\.\w+'
            condition_tables = set(re.findall(table_pattern, join_condition))
            
            # Find which table in the condition is already in the graph (and not the to_table)
            for table in condition_tables:
                if table in added_tables_set and table != to_table:
                    from_table = table
                    break
        
        # Fallback: if we can't determine from condition, use sequential join logic
        # For sequential joins: first join from FROM table, subsequent from last joined table
        if not from_table:
            # Use the last table in the list (which is the most recently added)
            from_table = added_tables_list[-1] if added_tables_list else (parsed["tables"][0] if parsed["tables"] else "")
        
        if from_table and to_table:
            # add_join will add both tables, but let's be explicit
            graph.add_join(from_table, to_table, join.get("type", "INNER"), join_condition)
            added_tables_set.add(to_table)
            if to_table not in added_tables_list:
                added_tables_list.append(to_table)

    # Add columns to nodes
    # Create case-insensitive lookup for graph nodes
    node_lookup = {name.lower(): name for name in graph.nodes.keys()}
    
    for table_name, columns in parsed["selected_columns"].items():
        if table_name == "*":
            # All columns from all tables
            for node in graph.nodes.values():
                node.columns.append("*")
        elif table_name == "_unknown":
            # Columns without table prefix - assign to first table
            if graph.nodes:
                first_table = list(graph.nodes.keys())[0]
                for col in columns:
                    graph.nodes[first_table].add_column(col)
        else:
            # Table-specific columns - use case-insensitive matching
            table_lower = table_name.lower()
            if table_lower in node_lookup:
                actual_table_name = node_lookup[table_lower]
                for col in columns:
                    graph.nodes[actual_table_name].add_column(col)

    # Add filters to nodes (case-insensitive table match)
    for table_name, filter_list in parsed["filters"].items():
        if table_name == "_global":
            # Global filters - assign to first table
            if graph.nodes:
                first_table = list(graph.nodes.keys())[0]
                for filter_cond in filter_list:
                    graph.nodes[first_table].add_filter(filter_cond)
        else:
            # Table-specific filters
            table_lower = table_name.lower()
            if table_lower in node_lookup:
                actual_table_name = node_lookup[table_lower]
                for filter_cond in filter_list:
                    graph.nodes[actual_table_name].add_filter(filter_cond)

    # Mark aggregation only for tables that appear in GROUP BY
    group_by = parsed.get("group_by")
    if group_by:
        for item in group_by:
            if "." in item:
                table = item.split(".", 1)[0].strip()
                table_lower = table.lower()
                if table_lower in node_lookup:
                    graph.nodes[node_lookup[table_lower]].set_aggregation(True)
            else:
                # Bare column - assign to first table
                if graph.nodes:
                    graph.nodes[list(graph.nodes.keys())[0]].set_aggregation(True)
                break

    return graph
