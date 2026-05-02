# Database Schema

Approved Phase 1 tables:

- `main.customers`: customer profile and lifecycle fields.
- `main.orders`: order facts including customer, status, dates, and totals.
- `main.order_items`: line-item facts linked to orders and products.
- `main.products`: product dimension fields.

Suggested joins:

- `main.orders.customer_id` to `main.customers.customer_id`.
- `main.order_items.order_id` to `main.orders.order_id`.
- `main.order_items.product_id` to `main.products.product_id`.

Known data-quality issues:

- Customer email and phone fields are PII and must be redacted.
- Some legacy orders may have missing status values.
