WITH total_users AS (
    SELECT COUNT(DISTINCT user_id) AS user_count
    FROM user
    WHERE install_at BETWEEN '2023-01-01' AND '2023-01-31'
), 
-- caculated amount of users who installed app in Jan of 2023 using subquery
monthly_payment AS (
    SELECT DATE_FORMAT(p.payment_at, '%Y-%m') AS monthly_payment,
    SUM(p.amount) AS monthly_amount 
    FROM user u
    JOIN payment p ON u.user_id = p.user_id 
    WHERE u.install_at BETWEEN '2023-01-01' AND '2023-01-31'
    GROUP BY monthly_payment
)
-- another subquery to calculate the montly total payment for users who installed the app in Jan by month

SELECT 
    monthly_payment, 
    SUM(monthly_amount) OVER (ORDER BY monthly_payment) / (SELECT user_count FROM total_users) AS cumulative_ARPU
FROM monthly_payment
ORDER BY monthly_payment; 




