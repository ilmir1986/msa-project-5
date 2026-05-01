-- Файл: scripts/init_db.sql

CREATE TABLE IF NOT EXISTS orders (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER,
    amount DECIMAL(10, 2),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO orders (order_id, customer_id, amount, status) VALUES
(1, 101, 1500.00, 'COMPLETED'),
(2, 102, 2300.50, 'COMPLETED'),
(3, 103, 990.00, 'PENDING'),
(4, 104, 5000.00, 'COMPLETED'),
(5, 105, 1200.00, 'CANCELLED'),
(6, 106, 3400.00, 'COMPLETED'),
(7, 107, 890.00, 'PENDING'),
(8, 108, 4100.00, 'COMPLETED'),
(9, 109, 2700.00, 'COMPLETED'),
(10, 110, 1800.00, 'PENDING');