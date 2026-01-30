# SQL Visualizer

A web-based tool that converts simple SQL SELECT queries into visual diagrams using Streamlit and Graphviz.

## Features

- **Simple UI**: Single-page Streamlit application
- **Instant Visualization**: Paste SQL and see diagrams immediately
- **Clean Diagrams**: Graphviz-powered SVG output
- **Error Handling**: Clear, user-friendly error messages

## Supported SQL Features

- `SELECT` - Column selection
- `FROM` - Table specification
- `INNER JOIN` - Inner joins
- `LEFT JOIN` - Left joins
- `WHERE` - Filter conditions
- `GROUP BY` - Aggregation grouping (optional)

## Unsupported Features

The following SQL features are explicitly **not supported** and will raise clear errors:

- Subqueries
- CTEs (WITH clauses)
- Window functions (OVER)
- Nested SELECTs
- UNION / UNION ALL

## Installation

1. Create and activate a Python virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -e .
```

3. Ensure Graphviz is installed on your system:

**macOS:**
```bash
brew install graphviz
```

**Linux:**
```bash
sudo apt-get install graphviz
```

**Windows:**
Download from [Graphviz website](https://graphviz.org/download/)

## Usage

Run the Streamlit app:

```bash
python -m streamlit run sqlviz/app.py
```

The app will open in your browser. Paste a SQL query and click "Visualize" to generate a diagram.

## Example SQL Query

```sql
SELECT users.id, users.name, orders.total
FROM users
INNER JOIN orders ON users.id = orders.user_id
WHERE users.active = 1
```

## Project Structure

```
sqlviz/
 ├─ parser.py      # SQL parsing using sqlparse
 ├─ model.py       # Graph model abstraction
 ├─ renderer.py    # Graphviz visualization
 ├─ errors.py      # Custom exceptions
 └─ app.py         # Streamlit entrypoint

examples/          # Example SQL files
tests/             # Test suite
README.md
pyproject.toml
```

## Running Tests

```bash
pytest tests/
```

![Demo](assets/sqlviz.gif)

## Final Notes

This project is a work-in-progress and a fun way for me to learn and explore. Feel free to poke around.

Liked what you saw? A ⭐ is the digital high‑five!

Cheers,  
Sneha