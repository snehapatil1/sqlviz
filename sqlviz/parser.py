"""SQL parsing layer using sqlparse."""

import re
from typing import Dict, List, Optional, Set

import sqlparse
from sqlparse.sql import Identifier, IdentifierList, Token, TokenList
from sqlparse.tokens import Keyword, Name, Punctuation, Wildcard, DML

from sqlviz.errors import ParseError, UnsupportedSQLError


def parse_sql(sql: str) -> Dict:
    """
    Parse SQL SELECT query into structured dictionary.

    Args:
        sql: Raw SQL string

    Returns:
        Dictionary with keys: tables, joins, selected_columns, filters, group_by

    Raises:
        ParseError: If SQL cannot be parsed
        UnsupportedSQLError: If unsupported syntax is detected
    """
    sql = sql.strip()
    if not sql:
        raise ParseError("Empty SQL query")

    # Check for unsupported features
    _check_unsupported_features(sql)

    # Parse SQL
    parsed = sqlparse.parse(sql)
    if not parsed:
        raise ParseError("Failed to parse SQL query")

    stmt = parsed[0]

    # Extract components
    tables = _extract_tables(stmt)
    joins = _extract_joins(stmt, sql)  # Pass original SQL for regex matching
    selected_columns = _extract_selected_columns(stmt)
    filters = _extract_filters(stmt)
    group_by = _extract_group_by(stmt)
    for join in joins:
        tables.append(join["table"])

    return {
        "tables": tables,
        "joins": joins,
        "selected_columns": selected_columns,
        "filters": filters,
        "group_by": group_by,
    }


def _check_unsupported_features(sql: str) -> None:
    """Check for unsupported SQL features."""
    sql_upper = sql.upper()

    # Check for CTEs
    if re.search(r'\bWITH\s+\w+\s+AS\s*\(', sql_upper):
        raise UnsupportedSQLError("CTEs (WITH clauses) are not supported")

    # Check for UNION
    if re.search(r'\bUNION\s+(ALL\s+)?SELECT\b', sql_upper):
        raise UnsupportedSQLError("UNION / UNION ALL are not supported")

    # Check for window functions
    if re.search(r'\bOVER\s*\(', sql_upper):
        raise UnsupportedSQLError("Window functions (OVER) are not supported")

    # Check for nested SELECT in FROM
    if re.search(r'FROM\s*\([^)]*SELECT', sql_upper, re.IGNORECASE):
        raise UnsupportedSQLError("Subqueries in FROM clause are not supported")

    # Check for subqueries in WHERE
    if re.search(r'WHERE\s+[^=]*\([^)]*SELECT', sql_upper, re.IGNORECASE):
        raise UnsupportedSQLError("Subqueries in WHERE clause are not supported")


def _extract_tables(stmt: TokenList) -> List[str]:
    """Extract table names from FROM clause."""
    tables = []
    from_seen = False
    tokens = list(stmt.flatten())
    i = 0

    while i < len(tokens):
        token = tokens[i]
        if token.ttype is Keyword and token.value.upper() == "FROM":
            from_seen = True
            i += 1
            # Get table name after FROM
            while i < len(tokens):
                if tokens[i].ttype is Keyword and tokens[i].value.upper() in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT", "INNER", "LEFT", "RIGHT", "FULL"):
                    break
                if tokens[i].ttype is Name:
                    table_name = tokens[i].value.strip()
                    if table_name and table_name.upper() not in ("AS",):
                        # Check for alias
                        if i + 1 < len(tokens) and tokens[i + 1].value.upper() == "AS":
                            i += 2
                        elif i + 1 < len(tokens) and tokens[i + 1].ttype is Name:
                            # Might be alias without AS
                            i += 1
                        if table_name not in tables:
                            tables.append(table_name)
                    break
                i += 1
        i += 1

    return tables


def _extract_joins(stmt: TokenList, sql: str = None) -> List[Dict]:
    """Extract JOIN clauses."""
    joins = []
    
    # Try using regex on the original SQL string as a more reliable method
    if sql:
        # Pattern to match: [INNER|LEFT|RIGHT|FULL] JOIN table_name ON condition
        # Match join type (optional), JOIN, table name, ON, and condition up to next keyword
        # Use case-insensitive matching but preserve original case
        join_pattern = r'\b(INNER|LEFT|RIGHT|FULL)?\s+JOIN\s+(\w+)\s+ON\s+((?:(?!\s+(?:WHERE|GROUP|ORDER|HAVING|LIMIT)\b).)+?)(?=\s+(?:WHERE|GROUP|ORDER|HAVING|LIMIT)\b|$)'
        
        matches = re.finditer(join_pattern, sql, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            join_type = (match.group(1) or "INNER").upper()  # Default to INNER if not specified
            table_name = match.group(2)  # Preserve original case
            condition = match.group(3).strip()  # Preserve original case
            
            joins.append({
                "type": join_type,
                "table": table_name,
                "condition": condition,
            })
    
    # If regex didn't work, fall back to token-based approach
    if not joins:
        tokens = list(stmt.flatten())
        i = 0

        while i < len(tokens):
            token = tokens[i]
            
            # Check for join type keyword
            join_type = None
            if token.ttype is Keyword:
                token_val = token.value.upper()
                if token_val in ("INNER", "LEFT", "RIGHT", "FULL"):
                    join_type = token_val
                    # Check if next token is JOIN
                    if i + 1 < len(tokens):
                        next_token = tokens[i + 1]
                        if hasattr(next_token, 'value') and next_token.value.upper() == "JOIN":
                            # Found "INNER JOIN" or "LEFT JOIN" etc.
                            i += 2  # Skip past "INNER JOIN" or "LEFT JOIN"
                            
                            # Extract table name
                            table_name = None
                            while i < len(tokens):
                                if tokens[i].ttype is Name:
                                    table_name = tokens[i].value.strip()
                                    i += 1
                                    break
                                # Skip whitespace and other tokens
                                i += 1
                            
                            # Look for ON clause
                            join_condition = None
                            if table_name:
                                while i < len(tokens):
                                    if tokens[i].ttype is Keyword and tokens[i].value.upper() == "ON":
                                        i += 1
                                        # Extract join condition
                                        condition_parts = []
                                        paren_count = 0
                                        while i < len(tokens):
                                            token_val = tokens[i].value if hasattr(tokens[i], 'value') else str(tokens[i])
                                            if token_val == "(":
                                                paren_count += 1
                                            elif token_val == ")":
                                                paren_count -= 1
                                            token_val_upper = token_val.upper() if isinstance(token_val, str) else ""
                                            if token_val_upper in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT") and paren_count == 0:
                                                break
                                            condition_parts.append(str(token_val))
                                            i += 1
                                        join_condition = " ".join(condition_parts).strip()
                                        break
                                    if tokens[i].ttype is Keyword and tokens[i].value.upper() in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT"):
                                        break
                                    i += 1
                                
                                if table_name:
                                    joins.append({
                                        "type": join_type,
                                        "table": table_name,
                                        "condition": join_condition or "",
                                    })
                                    continue  # Skip the i += 1 at the end
                elif token_val == "JOIN":
                    # Handle plain JOIN (defaults to INNER)
                    join_type = "INNER"
                    i += 1  # Skip JOIN
                    
                    # Extract table name
                    table_name = None
                    while i < len(tokens):
                        if tokens[i].ttype is Name:
                            table_name = tokens[i].value.strip()
                            i += 1
                            break
                        i += 1
                    
                    # Look for ON clause
                    join_condition = None
                    if table_name:
                        while i < len(tokens):
                            if tokens[i].ttype is Keyword and tokens[i].value.upper() == "ON":
                                i += 1
                                condition_parts = []
                                paren_count = 0
                                while i < len(tokens):
                                    token_val = tokens[i].value if hasattr(tokens[i], 'value') else str(tokens[i])
                                    if token_val == "(":
                                        paren_count += 1
                                    elif token_val == ")":
                                        paren_count -= 1
                                    token_val_upper = token_val.upper() if isinstance(token_val, str) else ""
                                    if token_val_upper in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT") and paren_count == 0:
                                        break
                                    condition_parts.append(str(token_val))
                                    i += 1
                                join_condition = " ".join(condition_parts).strip()
                                break
                            if tokens[i].ttype is Keyword and tokens[i].value.upper() in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT"):
                                break
                            i += 1
                        
                        if table_name:
                            joins.append({
                                "type": join_type,
                                "table": table_name,
                                "condition": join_condition or "",
                            })
                            continue  # Skip the i += 1 at the end
            
            i += 1
    
    return joins

    while i < len(tokens):
        token = tokens[i]
        
        # Check for join type keyword
        join_type = None
        if token.ttype is Keyword:
            token_val = token.value.upper()
            if token_val in ("INNER", "LEFT", "RIGHT", "FULL"):
                join_type = token_val
                # Check if next token is JOIN
                if i + 1 < len(tokens):
                    next_token = tokens[i + 1]
                    if hasattr(next_token, 'value') and next_token.value.upper() == "JOIN":
                        # Found "INNER JOIN" or "LEFT JOIN" etc.
                        i += 2  # Skip past "INNER JOIN" or "LEFT JOIN"
                        
                        # Extract table name
                        table_name = None
                        while i < len(tokens):
                            if tokens[i].ttype is Name:
                                table_name = tokens[i].value.strip()
                                i += 1
                                break
                            # Skip whitespace and other tokens
                            i += 1
                        
                        # Look for ON clause
                        join_condition = None
                        if table_name:
                            while i < len(tokens):
                                if tokens[i].ttype is Keyword and tokens[i].value.upper() == "ON":
                                    i += 1
                                    # Extract join condition
                                    condition_parts = []
                                    paren_count = 0
                                    while i < len(tokens):
                                        token_val = tokens[i].value if hasattr(tokens[i], 'value') else str(tokens[i])
                                        if token_val == "(":
                                            paren_count += 1
                                        elif token_val == ")":
                                            paren_count -= 1
                                        token_val_upper = token_val.upper() if isinstance(token_val, str) else ""
                                        if token_val_upper in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT") and paren_count == 0:
                                            break
                                        condition_parts.append(str(token_val))
                                        i += 1
                                    join_condition = " ".join(condition_parts).strip()
                                    break
                                if tokens[i].ttype is Keyword and tokens[i].value.upper() in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT"):
                                    break
                                i += 1
                            
                            if table_name:
                                joins.append({
                                    "type": join_type,
                                    "table": table_name,
                                    "condition": join_condition or "",
                                })
                                continue  # Skip the i += 1 at the end
            elif token_val == "JOIN":
                # Handle plain JOIN (defaults to INNER)
                join_type = "INNER"
                i += 1  # Skip JOIN
                
                # Extract table name
                table_name = None
                while i < len(tokens):
                    if tokens[i].ttype is Name:
                        table_name = tokens[i].value.strip()
                        i += 1
                        break
                    i += 1
                
                # Look for ON clause
                join_condition = None
                if table_name:
                    while i < len(tokens):
                        if tokens[i].ttype is Keyword and tokens[i].value.upper() == "ON":
                            i += 1
                            condition_parts = []
                            paren_count = 0
                            while i < len(tokens):
                                token_val = tokens[i].value if hasattr(tokens[i], 'value') else str(tokens[i])
                                if token_val == "(":
                                    paren_count += 1
                                elif token_val == ")":
                                    paren_count -= 1
                                token_val_upper = token_val.upper() if isinstance(token_val, str) else ""
                                if token_val_upper in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT") and paren_count == 0:
                                    break
                                condition_parts.append(str(token_val))
                                i += 1
                            join_condition = " ".join(condition_parts).strip()
                            break
                        if tokens[i].ttype is Keyword and tokens[i].value.upper() in ("WHERE", "GROUP", "ORDER", "HAVING", "LIMIT"):
                            break
                        i += 1
                    
                    if table_name:
                        joins.append({
                            "type": join_type,
                            "table": table_name,
                            "condition": join_condition or "",
                        })
                        continue  # Skip the i += 1 at the end
        
        i += 1

    return joins


def _skip_to_next_significant(tokens: list, j: int) -> int:
    """Advance j past whitespace and commas."""
    while j < len(tokens) and (tokens[j].value.strip() == "" or tokens[j].value == ","):
        j += 1
    return j


def _skip_past_function_call(tokens: list, j: int) -> int:
    """Advance past function call like COUNT(...), including optional AS alias. j is at '('."""
    paren_count = 0
    while j < len(tokens):
        if tokens[j].value == "(":
            paren_count += 1
        elif tokens[j].value == ")":
            paren_count -= 1
            if paren_count == 0:
                j += 1
                break
        j += 1
    # Skip optional AS alias
    j = _skip_to_next_significant(tokens, j)
    if j < len(tokens) and tokens[j].value.upper() == "AS":
        j = _skip_to_next_significant(tokens, j + 1)
        if j < len(tokens) and tokens[j].ttype is Name:
            j += 1
    return j


def _extract_selected_columns(stmt: TokenList) -> Dict[str, List[str]]:
    """Extract selected columns grouped by table.

    Token stream is flat: each token is one piece (e.g. 'users', '.', 'id').
    Table.column appears as Name, Punctuation('.'), Name.
    """
    columns_by_table: Dict[str, List[str]] = {}
    tokens = list(stmt.flatten())
    i = 0

    # Find SELECT
    while i < len(tokens):
        if (tokens[i].ttype is Keyword or tokens[i].ttype is DML) and tokens[i].value.upper() == "SELECT":
            i += 1
            break
        i += 1

    # Parse column list until FROM
    while i < len(tokens):
        token = tokens[i]

        # Stop at FROM
        if token.ttype is Keyword and token.value.upper() == "FROM":
            break

        # Skip whitespace and commas
        if token.value.strip() == "" or token.value == ",":
            i += 1
            continue

        # Wildcard: SELECT *
        if token.ttype is Wildcard or token.value == "*":
            if "*" not in columns_by_table:
                columns_by_table["*"] = ["*"]
            i += 1
            continue

        # Name: either table in "table.column", a function call (COUNT(...)), or bare column name
        if token.ttype is Name:
            table_or_col = token.value.strip()
            j = _skip_to_next_significant(tokens, i + 1)

            # Function call: COUNT(...), SUM(...), etc. - skip entire expression and "AS alias"
            if j < len(tokens) and tokens[j].value == "(":
                i = _skip_past_function_call(tokens, j)
                continue
            # Pattern table . column
            if j < len(tokens) and tokens[j].value == ".":
                table = table_or_col
                j += 1
                j = _skip_to_next_significant(tokens, j)
                if j < len(tokens) and tokens[j].ttype is Name:
                    col = tokens[j].value.strip()
                    if table not in columns_by_table:
                        columns_by_table[table] = []
                    columns_by_table[table].append(col)
                    i = j  # advance past column name
                else:
                    i = j
            else:
                # Bare column (no table prefix)
                if "_unknown" not in columns_by_table:
                    columns_by_table["_unknown"] = []
                columns_by_table["_unknown"].append(table_or_col)

        i += 1

    return columns_by_table


def _extract_filters(stmt: TokenList) -> Dict[str, List[str]]:
    """Extract WHERE conditions grouped by table. Stops at GROUP BY / ORDER / HAVING / LIMIT."""
    filters: Dict[str, List[str]] = {}
    where_seen = False
    condition_parts: List[str] = []

    for token in stmt.flatten():
        if token.ttype is Keyword and token.value.upper() == "WHERE":
            where_seen = True
            continue

        if where_seen:
            # Stop at GROUP (or "GROUP BY" as one token), ORDER, HAVING, LIMIT
            token_upper = token.value.upper() if hasattr(token, "value") else ""
            if token.ttype is Keyword and (
                token_upper.startswith("GROUP") or token_upper in ("ORDER", "HAVING", "LIMIT")
            ):
                break
            condition_parts.append(token.value)

    if condition_parts:
        where_clause = " ".join(condition_parts).strip()
        # Normalize spaces around dots
        where_normalized = re.sub(r"\s*\.\s*", ".", where_clause)
        table_pattern = r"(\w+)\.\w+"
        table_matches = re.findall(table_pattern, where_normalized)
        if table_matches:
            # Split by AND/OR to get full conditions, then assign each to its table(s)
            for table in set(table_matches):
                if table not in filters:
                    filters[table] = []
            # Find full condition per table: split WHERE on AND/OR
            parts = re.split(r"\s+AND\s+|\s+OR\s+", where_clause, flags=re.IGNORECASE)
            for part in parts:
                part = part.strip()
                part_normalized = re.sub(r"\s*\.\s*", ".", part)
                tables_in_part = set(re.findall(table_pattern, part_normalized))
                for table in tables_in_part:
                    if table in filters and part not in filters[table]:
                        filters[table].append(part)
        else:
            filters["_global"] = [where_clause]

    return filters


def _extract_group_by(stmt: TokenList) -> Optional[List[str]]:
    """Extract GROUP BY columns. Returns list of 'table.column' or bare 'column'."""
    group_by_cols: List[str] = []
    tokens = list(stmt.flatten())
    i = 0

    # Find GROUP BY (GROUP and BY may be one token or two)
    while i < len(tokens):
        t = tokens[i]
        val = (t.value or "").upper()
        if t.ttype is Keyword and (val == "GROUP" or val.startswith("GROUP")):
            i += 1
            # If token was "GROUP" only, skip "BY"
            if i < len(tokens) and tokens[i].value.upper() == "BY":
                i += 1
            break
        i += 1

    # Collect columns (table.column or bare column)
    while i < len(tokens):
        token = tokens[i]
        val = (token.value or "").upper()
        if token.ttype is Keyword and val in ("ORDER", "HAVING", "LIMIT"):
            break
        if (token.value or "").strip() == "" or token.value == ",":
            i += 1
            continue
        if token.ttype is Name:
            table_or_col = token.value.strip()
            j = _skip_to_next_significant(tokens, i + 1)
            if j < len(tokens) and tokens[j].value == ".":
                j += 1
                j = _skip_to_next_significant(tokens, j)
                if j < len(tokens) and tokens[j].ttype is Name:
                    col = tokens[j].value.strip()
                    group_by_cols.append(f"{table_or_col}.{col}")
                    i = j
                else:
                    i = j
            else:
                group_by_cols.append(table_or_col)
        i += 1

    return group_by_cols if group_by_cols else None
