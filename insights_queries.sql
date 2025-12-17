-- Query 1
-- Objective: Calculate the customer churn rate (average 'exited' status) grouped by geography and gender to identify demographic segments with the highest propensity to churn.
SELECT
    d.geography,
    d.gender,
    AVG(b.exited) AS churn_rate,
    COUNT(c.customerid) AS total_customers
FROM
    customer_dim c
JOIN
    demographic_dim d ON c.customerid = d.customerid
JOIN
    bank_relationship_report b ON c.customerid = b.customerid
GROUP BY
    d.geography,
    d.gender
ORDER BY
    churn_rate DESC;
    
-- Query 2
-- Objective: Compare the average age and the average number of products held by churned customers versus active customers.
SELECT
    b.exited,
    AVG(d.age) AS avg_age,
    AVG(f.numofproducts) AS avg_num_products,
    COUNT(c.customerid) AS total_customers
FROM
    customer_dim c
JOIN
    bank_relationship_report b ON c.customerid = b.customerid
JOIN
    demographic_dim d ON c.customerid = d.customerid
JOIN
    financial_report f ON c.customerid = f.customerid
GROUP BY
    b.exited;
    
-- Query 3
-- Objective: Determine the average estimated salary and average bank balance for customers who are active members versus those who are not.
SELECT
    f.isactivemember,
    AVG(f.estimatedsalary) AS avg_estimated_salary,
    AVG(f.balance) AS avg_balance,
    COUNT(c.customerid) AS total_customers
FROM
    customer_dim c
JOIN
    financial_report f ON c.customerid = f.customerid
GROUP BY
    f.isactivemember;

-- Query 4
-- Objective: Identify customers who hold more than one product and show their average balance and tenure, ordered by balance to see if higher balances correlate with product count and tenure.
SELECT
    f.numofproducts,
    AVG(f.balance) AS avg_balance,
    AVG(b.tenure) AS avg_tenure,
    COUNT(c.customerid) AS total_customers
FROM
    customer_dim c
JOIN
    financial_report f ON c.customerid = f.customerid
JOIN
    bank_relationship_report b ON c.customerid = b.customerid
WHERE
    f.numofproducts > 1
GROUP BY
    f.numofproducts
ORDER BY
    avg_balance DESC;

-- Query 5
-- Objective: Find the maximum and minimum age of customers who have churned ('exited' = 1) to understand the age range of customers most likely to leave.
SELECT
    MAX(d.age) AS max_age_churned,
    MIN(d.age) AS min_age_churned
FROM
    customer_dim c
JOIN
    demographic_dim d ON c.customerid = d.customerid
JOIN
    bank_relationship_report b ON c.customerid = b.customerid
WHERE
    b.exited = 1;
    

    
    
