SELECT products.name, categories.name, products.price
FROM products
LEFT JOIN categories ON products.category_id = categories.id
WHERE products.price > 100
