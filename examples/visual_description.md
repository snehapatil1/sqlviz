# Visual Description of SQL Diagram Output

## Layout Structure

The diagrams use a **left-to-right flow** showing the relationship between tables:

```
[FROM Table] ──[JOIN]──> [Joined Table]
```

## Node (Table) Structure

Each table is rendered as a box containing:

```
┌─────────────────────────────┐
│   Table Name (Bold)         │  ← Header
├─────────────────────────────┤
│ • column1                   │  ← Selected columns
│ • column2                   │     (with bullet points)
│ • column3                   │
│                             │
│ WHERE:                      │  ← Filter section (if present)
│   condition1                 │     (in italic)
│   condition2                │
│                             │
│ [GROUP BY]                  │  ← Aggregation indicator (if present)
└─────────────────────────────┘
```

## Edge (Join) Structure

Joins are shown as labeled arrows:

```
[Table A] ──INNER JOIN──> [Table B]
          condition
```

The label shows:
- Join type (INNER JOIN, LEFT JOIN, etc.)
- Join condition (e.g., "users.id = orders.user_id")

## Complete Example Visualization

For the query:
```sql
SELECT users.id, users.name, orders.total
FROM users
INNER JOIN orders ON users.id = orders.user_id
WHERE users.active = 1
```

The visual output should appear as:

```
    ┌─────────────────────────────┐
    │         users               │
    ├─────────────────────────────┤
    │ • id                        │
    │ • name                      │
    │                             │
    │ WHERE:                      │
    │   users.active = 1          │
    └─────────────────────────────┘
              │
              │ INNER JOIN
              │ users.id = orders.user_id
              │
              ▼
    ┌─────────────────────────────┐
    │         orders              │
    ├─────────────────────────────┤
    │ • total                     │
    └─────────────────────────────┘
```

## Styling Details

- **Boxes**: Rounded rectangles with light blue fill
- **Table names**: Bold, centered at top
- **Columns**: Bullet list, left-aligned
- **WHERE clauses**: Italic text, indented
- **Arrows**: Black lines with text labels
- **Spacing**: Generous padding for readability
