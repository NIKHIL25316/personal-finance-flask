-- Create Database
CREATE DATABASE my_web_app_db;
USE my_web_app_db;

-- Users Table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- Accounts Table with institution_name
CREATE TABLE accounts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    institution_name VARCHAR(100),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Transactions Table with debit and credit columns
CREATE TABLE transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_id INT NOT NULL,
    debit DECIMAL(10, 2),
    credit DECIMAL(10, 2),
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

drop table transactions

ALTER TABLE accounts CHANGE name type VARCHAR(255);


-- Investment Transactions Table
CREATE TABLE investment_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_id INT NOT NULL,
    ticker VARCHAR(10), -- Stock or Asset symbol
    transaction_type VARCHAR(20), -- Buy/Sell
    quantity INT,
    amount DECIMAL(10, 2),
    transaction_date DATE NOT NULL,
    description VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

-- Deposit Transactions Table
CREATE TABLE deposit_transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    account_id INT NOT NULL,
    amount DECIMAL(10, 2),
    period INT, -- Period of deposit in months or years
    interest_rate DECIMAL(5, 2), -- Interest rate percentage
    transaction_date DATE NOT NULL,
    description VARCHAR(255),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);


CREATE TABLE uploads (
    id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(id),
    account_id INT REFERENCES accounts(id),
    file_name VARCHAR(255),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
