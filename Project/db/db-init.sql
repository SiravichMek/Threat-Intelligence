CREATE DATABASE IF NOT EXISTS myapp_db;

USE myapp_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

# Insert sample users
INSERT INTO users (username, password, email, full_name) VALUES 
('admin', 'password', 'admin@example.com', 'Admin User'),
('john_doe', 'password123', 'john@example.com', 'John Doe'),
('jane_smith', 'mypassword', 'jane@example.com', 'Jane Smith'),
('alice_johnson', 'secret123', 'alice@example.com', 'Alice Johnson'),
('bob_brown', 'qwerty', 'bob@example.com', 'Bob Brown');

