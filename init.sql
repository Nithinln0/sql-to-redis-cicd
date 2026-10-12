
CREATE TABLE IF NOT EXISTS employees (
    id INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100) NOT NULL
);

INSERT INTO employees (id, name, department) VALUES
(101, 'Ravi', 'IT'),
(102, 'Priya', 'HR'),
(103, 'Kiran', 'Finance');
