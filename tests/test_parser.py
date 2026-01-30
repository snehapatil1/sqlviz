"""Tests for SQL parser."""

import pytest

from sqlviz.errors import ParseError, UnsupportedSQLError
from sqlviz.parser import parse_sql


def test_simple_select():
    """Test simple SELECT query."""
    sql = "SELECT * FROM users"
    result = parse_sql(sql)
    assert "users" in result["tables"]
    assert len(result["joins"]) == 0


def test_inner_join():
    """Test INNER JOIN."""
    sql = "SELECT * FROM users INNER JOIN orders ON users.id = orders.user_id"
    result = parse_sql(sql)
    assert "users" in result["tables"]
    assert "orders" in result["tables"]
    assert len(result["joins"]) == 1
    assert result["joins"][0]["type"] == "INNER"


def test_left_join():
    """Test LEFT JOIN."""
    sql = "SELECT * FROM products LEFT JOIN categories ON products.category_id = categories.id"
    result = parse_sql(sql)
    assert len(result["joins"]) == 1
    assert result["joins"][0]["type"] == "LEFT"


def test_where_clause():
    """Test WHERE clause."""
    sql = "SELECT * FROM users WHERE users.active = 1"
    result = parse_sql(sql)
    assert len(result["filters"]) > 0


def test_group_by():
    """Test GROUP BY."""
    sql = "SELECT name, COUNT(*) FROM users GROUP BY name"
    result = parse_sql(sql)
    assert result["group_by"] is not None


def test_unsupported_cte():
    """Test that CTEs are rejected."""
    sql = "WITH temp AS (SELECT * FROM users) SELECT * FROM temp"
    with pytest.raises(UnsupportedSQLError):
        parse_sql(sql)


def test_unsupported_union():
    """Test that UNION is rejected."""
    sql = "SELECT * FROM users UNION SELECT * FROM orders"
    with pytest.raises(UnsupportedSQLError):
        parse_sql(sql)


def test_unsupported_subquery():
    """Test that subqueries are rejected."""
    sql = "SELECT * FROM (SELECT * FROM users) AS temp"
    with pytest.raises(UnsupportedSQLError):
        parse_sql(sql)


def test_empty_sql():
    """Test empty SQL raises error."""
    with pytest.raises(ParseError):
        parse_sql("")
