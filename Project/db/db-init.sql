CREATE DATABASE IF NOT EXISTS myapp_db;

USE myapp_db;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL
);

# Insert a sample user
INSERT INTO users (username, password) VALUES ('admin', 'password');
