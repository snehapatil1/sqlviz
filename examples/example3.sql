SELECT customers.name, COUNT(orders.id) as order_count
FROM customers
INNER JOIN orders ON customers.id = orders.customer_id
WHERE orders.status = 'completed'
GROUP BY customers.name
