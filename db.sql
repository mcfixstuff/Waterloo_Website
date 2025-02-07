CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    microsoft_id VARCHAR(255) UNIQUE NOT NULL,  -- Unique ID from Microsoft
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('superuser', 'manager', 'basicuser'))
);
