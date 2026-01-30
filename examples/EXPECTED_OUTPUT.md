# Expected Output Format

This document shows what the SQL visualization diagrams should look like.

## Example 1: Simple SELECT with WHERE

**SQL Query:**
```sql
SELECT id, name FROM users WHERE active = 1
```

**Expected Diagram:**
```
┌─────────────────────────┐
│      users              │
├─────────────────────────┤
│ • id                    │
│ • name                  │
│                         │
│ WHERE:                  │
│   users.active = 1      │
└─────────────────────────┘
```

## Example 2: INNER JOIN

**SQL Query:**
```sql
SELECT users.id, users.name, orders.total
FROM users
INNER JOIN orders ON users.id = orders.user_id
WHERE users.active = 1
```

**Expected Diagram:**
```
┌─────────────────────────┐      INNER JOIN       ┌─────────────────────────┐
│      users               │ ────────────────────>│      orders             │
├─────────────────────────┤  users.id = orders.   ├─────────────────────────┤
│ • id                    │      user_id          │• total                  │
│ • name                  │                       │                         │
│                         │                       │                         │
│ WHERE:                  │                       │                         │
│   users.active = 1      │                       │                         │
└─────────────────────────┘                       └─────────────────────────┘
```

## Example 3: LEFT JOIN with Multiple Columns

**SQL Query:**
```sql
SELECT products.name, categories.name, products.price
FROM products
LEFT JOIN categories ON products.category_id = categories.id
WHERE products.price > 100
```

**Expected Diagram:**
```
┌─────────────────────────┐      LEFT JOIN        ┌─────────────────────────┐
│     products            │ ────────────────────> │    categories            │
├─────────────────────────┤  products.category_  ├─────────────────────────┤
│ • name                  │    id = categories.id │ • name                   │
│ • price                 │                       │                         │
│                         │                       │                         │
│ WHERE:                  │                       │                         │
│   products.price > 100  │                       │                         │
└─────────────────────────┘                       └─────────────────────────┘
```

## Example 4: GROUP BY Query

**SQL Query:**
```sql
SELECT customers.name, COUNT(orders.id) as order_count
FROM customers
INNER JOIN orders ON customers.id = orders.customer_id
WHERE orders.status = 'completed'
GROUP BY customers.name
```

**Expected Diagram:**
```
┌─────────────────────────┐      INNER JOIN       ┌─────────────────────────┐
│    customers            │ ────────────────────> │      orders              │
├─────────────────────────┤  customers.id =      ├─────────────────────────┤
│ • name                  │    orders.customer_id │ • id                     │
│                         │                       │                         │
│                         │                       │ WHERE:                  │
│ [GROUP BY]              │                       │   orders.status =        │
│                         │                       │     'completed'         │
└─────────────────────────┘                       └─────────────────────────┘
```

## Visual Characteristics

1. **Table Nodes**: 
   - Rectangular boxes with rounded corners
   - Table name in bold at the top
   - Selected columns listed with bullet points
   - WHERE clauses shown in italic below columns
   - GROUP BY indicator shown at bottom if present

2. **Join Edges**:
   - Labeled arrows between tables
   - Join type shown (INNER JOIN, LEFT JOIN, etc.)
   - Join condition shown below join type

3. **Layout**:
   - Left-to-right flow (FROM table on left, joined tables to the right)
   - Clean, readable spacing
   - Professional appearance suitable for documentation

## Color Scheme

- Table boxes: Light blue background with rounded corners
- Text: Black with appropriate emphasis (bold for table names, italic for WHERE clauses)
- Arrows: Black with labels
