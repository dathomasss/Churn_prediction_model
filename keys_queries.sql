ALTER TABLE customer_dim
ADD PRIMARY KEY (customerid);

ALTER TABLE demographic_dim
ADD FOREIGN KEY (customerid)
REFERENCES customer_dim(customerid);

ALTER TABLE bank_relationship_report
ADD FOREIGN KEY (customerid)
REFERENCES customer_dim(customerid);

ALTER TABLE financial_report
ADD FOREIGN KEY (customerid)
REFERENCES customer_dim(customerid);