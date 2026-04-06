CREATE DATABASE IF NOT EXISTS grade_platform CHARACTER SET utf8mb4;
USE grade_platform;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('student', 'professor', 'admin') NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE account_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    role ENUM('student', 'professor') NOT NULL,
    status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin par défaut
INSERT INTO users (username, email, password_hash, role) 
VALUES ('admin', 'admin@guardia.cs', '$2b$12$examplehash1234567890abcdefghijklmnopqrstuvwxyz', 'admin')
ON DUPLICATE KEY UPDATE email=email;