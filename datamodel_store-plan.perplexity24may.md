# Database Design for Transaction Management System

Based on the analysis of your current transaction data, this report presents a comprehensive database design that will transform your existing Excel-based bookkeeping into a robust, scalable PostgreSQL system. The current data reveals a printer and computer service business with mixed transaction types, redundant data structures, and normalization opportunities that can be significantly improved through proper database design.

## Current Data Analysis and Issues

### Data Structure Assessment

Your existing Excel file contains four sheets with overlapping and redundant information[1]. The `INVOICE` sheet tracks basic invoice information, while the `TRANSACTION` sheet combines detailed transaction records with duplicated invoice data in additional columns[1]. This structure creates several data integrity risks and maintenance challenges.

The transaction data reveals a business model focused on printer services, computer repairs, and related product sales[1]. Clients include healthcare facilities (RSUM SURYA MELATI), government offices (KELURAHAN DERMO), schools (SMPN 2 NGADILUWIH), and various businesses[1]. Transaction types are categorized as either "PEMBELIAN" (purchases) or "SERVICE" operations, with amounts ranging from 50,000 to over 8,000,000 Indonesian Rupiah[1].

### Identified Data Quality Issues

Several inconsistencies exist in the current structure that the new database design must address. Date formats vary between sheets, with some using standard date formats while others use string representations[1]. The `TRANSACTION` sheet contains both invoiced and non-invoiced entries, indicated by either proper invoice IDs or dash symbols[1]. Additionally, the same customer names appear with slight variations, such as "PT ENSEVAL" and "ENSEVAL"[1].

The mixing of sales transactions with expense entries in the same table creates analytical challenges[1]. Personal expenses for fuel (consistently recorded for "NANDA") are interspersed with business transactions, making financial reporting more complex than necessary[1].

## Recommended Database Schema Design

### Core Entity Design

The proposed schema follows normalization principles while maintaining practical query efficiency. The design separates distinct business entities into dedicated tables with clear relationships and proper constraints.

```sql
-- Customers/Clients Table
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    customer_code VARCHAR(20) UNIQUE NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    customer_type VARCHAR(50) DEFAULT 'BUSINESS', -- BUSINESS, GOVERNMENT, INDIVIDUAL
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    tax_id VARCHAR(50),
    payment_terms INTEGER DEFAULT 30, -- days
    credit_limit DECIMAL(15,2) DEFAULT 0.00,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Employees/Members Table
CREATE TABLE employees (
    employee_id SERIAL PRIMARY KEY,
    employee_code VARCHAR(20) UNIQUE NOT NULL,
    employee_name VARCHAR(255) NOT NULL,
    position VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products and Services Catalog
CREATE TABLE items (
    item_id SERIAL PRIMARY KEY,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    item_type VARCHAR(20) NOT NULL, -- PRODUCT, SERVICE
    category VARCHAR(100),
    description TEXT,
    unit_of_measure VARCHAR(20) DEFAULT 'PCS',
    standard_price DECIMAL(15,2),
    cost_price DECIMAL(15,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers Table
CREATE TABLE suppliers (
    supplier_id SERIAL PRIMARY KEY,
    supplier_code VARCHAR(20) UNIQUE NOT NULL,
    supplier_name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    payment_terms INTEGER DEFAULT 30,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Transaction and Invoice Management

The invoice and transaction structure addresses the complexities identified in database design discussions[2][3], ensuring proper audit trails and flexible invoice generation capabilities.

```sql
-- Sales Invoices
CREATE TABLE invoices (
    invoice_id SERIAL PRIMARY KEY,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    customer_id INTEGER REFERENCES customers(customer_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    invoice_date DATE NOT NULL,
    due_date DATE,
    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT, SENT, PAID, VOID, OVERDUE
    subtotal DECIMAL(15,2) DEFAULT 0.00,
    tax_amount DECIMAL(15,2) DEFAULT 0.00,
    total_amount DECIMAL(15,2) DEFAULT 0.00,
    paid_amount DECIMAL(15,2) DEFAULT 0.00,
    payment_method VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Sales Invoice Line Items
CREATE TABLE invoice_items (
    invoice_item_id SERIAL PRIMARY KEY,
    invoice_id INTEGER REFERENCES invoices(invoice_id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES items(item_id),
    line_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_price DECIMAL(15,2) NOT NULL,
    line_total DECIMAL(15,2) NOT NULL,
    UNIQUE(invoice_id, line_number)
);

-- Purchase Orders
CREATE TABLE purchases (
    purchase_id SERIAL PRIMARY KEY,
    purchase_number VARCHAR(50) UNIQUE NOT NULL,
    supplier_id INTEGER REFERENCES suppliers(supplier_id),
    employee_id INTEGER REFERENCES employees(employee_id),
    purchase_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, RECEIVED, PAID, CANCELLED
    subtotal DECIMAL(15,2) DEFAULT 0.00,
    tax_amount DECIMAL(15,2) DEFAULT 0.00,
    total_amount DECIMAL(15,2) DEFAULT 0.00,
    paid_amount DECIMAL(15,2) DEFAULT 0.00,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Purchase Line Items
CREATE TABLE purchase_items (
    purchase_item_id SERIAL PRIMARY KEY,
    purchase_id INTEGER REFERENCES purchases(purchase_id) ON DELETE CASCADE,
    item_id INTEGER REFERENCES items(item_id),
    line_number INTEGER NOT NULL,
    description TEXT NOT NULL,
    quantity DECIMAL(10,3) NOT NULL,
    unit_cost DECIMAL(15,2) NOT NULL,
    line_total DECIMAL(15,2) NOT NULL,
    UNIQUE(purchase_id, line_number)
);
```

### Payment and Expense Tracking

The payment tracking system supports both customer payments and supplier payments while maintaining clear audit trails.

```sql
-- Payment Records
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    payment_number VARCHAR(50) UNIQUE NOT NULL,
    payment_type VARCHAR(20) NOT NULL, -- CUSTOMER, SUPPLIER, EXPENSE
    reference_id INTEGER, -- invoice_id, purchase_id, or expense_id
    payer_payee_id INTEGER, -- customer_id or supplier_id
    payment_date DATE NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Business Expenses
CREATE TABLE expenses (
    expense_id SERIAL PRIMARY KEY,
    expense_number VARCHAR(50) UNIQUE NOT NULL,
    employee_id INTEGER REFERENCES employees(employee_id),
    expense_date DATE NOT NULL,
    category VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    payment_method VARCHAR(50),
    is_reimbursable BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, APPROVED, PAID, REJECTED
    receipt_path VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP,
    approved_by INTEGER REFERENCES employees(employee_id)
);
```

## Indexing and Performance Optimization

### Strategic Index Implementation

Performance optimization requires carefully planned indexes that support both transactional operations and reporting queries without creating excessive maintenance overhead.

```sql
-- Primary lookup indexes
CREATE INDEX idx_customers_name ON customers(customer_name);
CREATE INDEX idx_customers_code ON customers(customer_code);
CREATE INDEX idx_invoices_customer ON invoices(customer_id);
CREATE INDEX idx_invoices_date ON invoices(invoice_date);
CREATE INDEX idx_invoices_status ON invoices(status);

-- Composite indexes for common query patterns
CREATE INDEX idx_invoices_customer_date ON invoices(customer_id, invoice_date);
CREATE INDEX idx_payments_type_date ON payments(payment_type, payment_date);
CREATE INDEX idx_expenses_employee_date ON expenses(employee_id, expense_date);

-- Text search capabilities
CREATE INDEX idx_items_name_trgm ON items USING gin(item_name gin_trgm_ops);
CREATE INDEX idx_customers_name_trgm ON customers USING gin(customer_name gin_trgm_ops);
```

### Referential Integrity and Constraints

Data integrity constraints prevent common data quality issues while maintaining system reliability.

```sql
-- Check constraints for data validation
ALTER TABLE invoices ADD CONSTRAINT chk_invoice_amounts 
    CHECK (subtotal >= 0 AND tax_amount >= 0 AND total_amount >= 0 AND paid_amount >= 0);

ALTER TABLE invoices ADD CONSTRAINT chk_paid_not_exceed_total 
    CHECK (paid_amount  0 AND unit_price >= 0 AND line_total >= 0);

-- Triggers for automatic calculations
CREATE OR REPLACE FUNCTION update_invoice_totals()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE invoices SET
        subtotal = (SELECT COALESCE(SUM(line_total), 0) FROM invoice_items WHERE invoice_id = NEW.invoice_id),
        updated_at = CURRENT_TIMESTAMP
    WHERE invoice_id = NEW.invoice_id;
    
    UPDATE invoices SET
        total_amount = subtotal + tax_amount
    WHERE invoice_id = NEW.invoice_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_update_invoice_totals
    AFTER INSERT OR UPDATE OR DELETE ON invoice_items
    FOR EACH ROW EXECUTE FUNCTION update_invoice_totals();
```

## Integration with Business Applications

### Invoicing System Support

The database design facilitates robust invoicing workflows by maintaining clear separation between draft transactions and final invoices[2]. The invoice status progression from `DRAFT` to `SENT` to `PAID` provides clear audit trails while supporting flexible invoice modification before finalization.

Invoice generation queries can efficiently aggregate transaction data while maintaining referential integrity between line items and master records. The design supports both product sales and service billing, accommodating the mixed business model evident in your current data[1].

### Transaction Entry Applications

The normalized structure supports efficient transaction entry through well-defined entity relationships. New sales transactions follow a clear path from item selection through invoice generation to payment recording. The separation of concerns between invoices, line items, and payments allows for flexible transaction handling while maintaining data consistency.

Purchase transaction entry follows similar patterns but maintains separate workflows appropriate for supplier relationship management. The expense tracking system provides clear employee expense management capabilities separate from customer transactions.

### Reporting and Analytics Framework

The schema design prioritizes reporting efficiency through strategic de-normalization where appropriate and comprehensive indexing strategies. Financial reports can efficiently aggregate data across multiple dimensions including customer, time period, product category, and employee performance.

Standard financial reports including profit and loss statements, accounts receivable aging, and cash flow analysis are supported through straightforward query patterns. The separation of sales, purchases, and expenses enables accurate gross margin analysis and operational expense tracking.

## Data Migration Strategy

### Converting Existing Data

The migration from your current Excel structure to the new database requires careful data cleansing and transformation. Customer data consolidation will resolve naming inconsistencies, while transaction categorization will properly separate sales, purchases, and expenses into appropriate tables[1].

```sql
-- Sample migration script for customers
INSERT INTO customers (customer_code, customer_name, customer_type)
SELECT 
    UPPER(REPLACE(TRIM("CLIENT NAME"), ' ', '_')) as customer_code,
    TRIM("CLIENT NAME") as customer_name,
    CASE 
        WHEN "CLIENT NAME" LIKE '%KELURAHAN%' OR "CLIENT NAME" LIKE '%BPJS%' THEN 'GOVERNMENT'
        WHEN "CLIENT NAME" LIKE '%HOTEL%' OR "CLIENT NAME" LIKE '%APOTEK%' THEN 'BUSINESS'
        ELSE 'BUSINESS'
    END as customer_type
FROM (SELECT DISTINCT "CLIENT NAME" FROM existing_transaction_data 
      WHERE "CLIENT NAME" IS NOT NULL AND "CLIENT NAME" != 'NANDA') customers_raw;
```

### Validation and Quality Assurance

Post-migration validation ensures data integrity through comprehensive reconciliation processes. Transaction totals, customer balances, and inventory levels must match between the original Excel data and the new database structure before going live with the new system.

## Scalability and Future Considerations

### Performance Scaling

The design accommodates growth through horizontal partitioning strategies for high-volume tables. Transaction tables can be partitioned by date ranges, while customer and product tables remain centralized for referential integrity. Connection pooling and read replicas support increased concurrent user loads as the business expands.

### Feature Extension Capabilities

The modular design supports future enhancements including inventory management, advanced pricing strategies, and multi-currency operations. The clean separation between core entities and business processes allows for additional modules without fundamental schema changes.

Integration capabilities support future connections to accounting systems, customer relationship management platforms, and e-commerce applications through well-defined API endpoints built on the stable database foundation.

## Implementation Recommendations

### Development Phases

Implementation should proceed through structured phases beginning with core entity creation and basic transaction recording. Invoice generation and payment tracking follow as secondary phases, with advanced reporting and analytics capabilities in the final implementation stage.

Each phase requires comprehensive testing with your actual historical data to ensure accuracy and performance before proceeding to the next development stage. User training and system documentation should parallel technical development to ensure smooth adoption.

### Monitoring and Maintenance

Ongoing database health monitoring includes query performance analysis, index usage tracking, and data growth pattern assessment. Regular backup strategies and disaster recovery procedures ensure business continuity while maintaining data security and compliance requirements.

Citations:
[1] https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/43767246/fbfae8e0-65a3-4510-ae5b-70ab3d003fac/SHEET-BOOKKEEPING-TEMPLATED.xlsx
[2] https://postgrespro.com/list/thread-id/1359667
[3] https://docs.oracle.com/cd/F26413_51/books/DMR/c-Invoices-afs1015848.html
[4] https://datasciencehorizons.com/database-normalization-a-practical-guide/
[5] https://www.ibm.com/docs/en/safer-payments/6.5?topic=types-transaction-centric-model
[6] https://www.mydbops.com/blog/postgresql-indexing-best-practices-guide
[7] https://www.restack.io/p/creating-foreign-key-indexes-answer
[8] https://reintech.io/blog/best-practices-database-schema-design-postgresql
[9] https://dev.to/dbvismarketing/building-a-postgresql-database-for-e-commerce-96o
[10] https://stackoverflow.com/questions/11450032/need-help-designing-my-invoice-db-structure
[11] https://www.softwareideas.net/a/1511/invoicing--invoice-database-model-using-erd
[12] https://anthonysmoak.com/2015/12/22/normalization-a-database-best-practice/
[13] https://www.ibm.com/docs/en/integration-bus/10.0?topic=transactions-transactional-model
[14] https://www.restack.io/p/ai-infrastructure-answer-postgres-indexing-foreign-keys-cat-ai
[15] http://learnline.cdu.edu.au/units/databaseconcepts/module1/popups/createinvoicedb.html
[16] https://guides.visual-paradigm.com/balancing-data-integrity-and-performance-normalization-vs-denormalization-in-database-design/
[17] https://docs.bigchaindb.com/projects/server/en/v0.10.3/data-models/transaction-model.html
[18] https://dba.stackexchange.com/questions/224535/payment-method-schema-design
[19] https://www.codecademy.com/learn/how-do-i-make-sure-my-database-stays-fast/modules/normalizing-a-database/cheatsheet
[20] https://www.essentialsql.com/database-normalization/
[21] https://www.postgresql.org/message-id/20020328183521.A10904@quillandmouse.com
[22] https://www.cybertec-postgresql.com/en/postgresql-sequences-vs-invoice-numbers/
[23] https://stackoverflow.com/questions/34098326/how-to-select-a-schema-in-postgres-when-using-psql
[24] https://www.postgresql.org/message-id/Pine.LNX.4.21.0105032153120.14951-100000@ludwig
[25] https://www.linkedin.com/advice/1/what-some-best-practices-database-normalization
[26] https://learn.microsoft.com/en-us/office/troubleshoot/access/database-normalization-description
[27] https://www.timescale.com/learn/postgresql-performance-tuning-optimizing-database-indexes
[28] https://www.postgresql.org/docs/current/indexes.html
[29] https://www.percona.com/blog/a-practical-guide-to-postgresql-indexes/
[30] https://www.timescale.com/learn/designing-your-database-schema-wide-vs-narrow-postgres-tables
[31] https://www.timescale.com/learn/how-to-design-postgresql-database-two-schema-examples
[32] https://www.datensen.com/database-design/postgresql-database-design.html
[33] https://www.w3schools.com/postgresql/postgresql_create_table.php
[34] https://the-pi-guy.com/blog/postgresql_indexing_best_practices_for_faster_queries/
[35] https://tembo.io/docs/getting-started/postgres_guides/postgres-indexing-strategies
[36] https://www.codecademy.com/learn/fscp-designing-relational-databases/modules/fscp-designing-a-database/cheatsheet
[37] https://dev.mysql.com/doc/sakila/en/sakila-structure-tables-customer.html
[38] https://www.crunchydata.com/blog/building-customer-facing-real-time-dashboards-with-postgres
[39] https://experienceleague.adobe.com/en/docs/commerce-business-intelligence/mbi/analyze/tables/cust-ent-table
[40] https://www.codecademy.com/learn/paths/design-databases-with-postgresql/tracks/how-do-i-make-and-populate-my-own-database/modules/designing-a-database-schema/cheatsheet
[41] https://ksi.cpsc.ucalgary.ca/courses/451-97/projects/s1/Detailed%20Design%20Document/ERD.html

---
Answer from Perplexity: pplx.ai/share