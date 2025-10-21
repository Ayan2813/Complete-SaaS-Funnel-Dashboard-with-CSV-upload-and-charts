INSERT INTO Plans (plan_name, price, duration_days)
VALUES
('Basic', 29.99, 30),
('Pro', 59.99, 30),
('Enterprise', 199.99, 30);

INSERT INTO Sources (source_name)
VALUES
('Organic'),
('Paid Ads'),
('Referral'),
('Social Media');

INSERT INTO Users (name, email, signup_date, plan_id, source_id, country)
VALUES
('Alice Johnson', 'alice@example.com', '2025-10-01 10:00:00', 1, 1, 'USA'),
('Bob Smith', 'bob@example.com', '2025-10-02 11:30:00', 2, 2, 'Canada'),
('Carol Lee', 'carol@example.com', '2025-10-03 09:45:00', 3, 3, 'UK'),
('David Kim', 'david@example.com', '2025-10-04 15:20:00', 1, 4, 'Australia'),
('Eva Patel', 'eva@example.com', '2025-10-05 08:10:00', 2, 1, 'India');

INSERT INTO Events (user_id, event_type, event_date)
VALUES
(1, 'visit', '2025-10-01 09:50:00'),
(1, 'signup', '2025-10-01 10:00:00'),
(1, 'trial', '2025-10-01 10:05:00'),
(1, 'paid', '2025-10-03 12:00:00'),

(2, 'visit', '2025-10-02 11:00:00'),
(2, 'signup', '2025-10-02 11:30:00'),
(2, 'trial', '2025-10-02 11:35:00'),

(3, 'visit', '2025-10-03 09:30:00'),
(3, 'signup', '2025-10-03 09:45:00'),

(4, 'visit', '2025-10-04 15:00:00'),
(4, 'signup', '2025-10-04 15:20:00'),
(4, 'trial', '2025-10-04 15:25:00'),
(4, 'paid', '2025-10-06 10:00:00'),

(5, 'visit', '2025-10-05 08:00:00'),
(5, 'signup', '2025-10-05 08:10:00');

