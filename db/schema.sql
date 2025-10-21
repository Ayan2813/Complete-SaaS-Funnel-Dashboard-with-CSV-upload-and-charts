CREATE TABLE IF NOT EXISTS Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    signup_date DATETIME,
    plan_id INT,
    source_id INT,
    country VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS Plans (
    plan_id INT AUTO_INCREMENT PRIMARY KEY,
    plan_name VARCHAR(50),
    price DECIMAL(10,2),
    duration_days INT
);

CREATE TABLE IF NOT EXISTS Sources (
    source_id INT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS Events (
    event_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    event_type ENUM('visit','signup','trial','paid') NOT NULL,
    event_date DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

CREATE TABLE IF NOT EXISTS Cohorts (
    cohort_id INT AUTO_INCREMENT PRIMARY KEY,
    cohort_name VARCHAR(50),
    start_date DATE,
    end_date DATE
);

CREATE TABLE IF NOT EXISTS UserCohorts (
    user_id INT,
    cohort_id INT,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    FOREIGN KEY (cohort_id) REFERENCES Cohorts(cohort_id)
);

