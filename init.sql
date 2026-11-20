
CREATE TABLE IF NOT EXISTS employees (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
);

INSERT INTO employees (id, name, department)
VALUES
    (101, 'Ravi', 'IT'),
    (102, 'Priya', 'HR'),
    (103, 'Kiran', 'Finance')
ON DUPLICATE KEY UPDATE
    name = VALUES(name),
    department = VALUES(department);
CREATE TABLE IF NOT EXISTS products (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    price DECIMAL(10,2) NOT NULL
);

INSERT IGNORE INTO products (id, name, price) VALUES
(201, 'Laptop', 55000.00),
(202, 'Keyboard', 1500.00);
