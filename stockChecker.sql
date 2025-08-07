-- SQLite
SELECT
    stock.store_id,
    stores.location_name,
    stock.tcin,
    products.title,
    stock.quantity,
    products.price
FROM stock
JOIN stores ON stock.store_id = stores.store_id
JOIN products ON stock.tcin = products.tcin
ORDER BY quantity DESC

