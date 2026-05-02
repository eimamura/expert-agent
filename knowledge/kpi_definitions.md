# KPI Definitions

## Active Customers

Count distinct customers with at least one completed or paid order in the period. Cancelled and refunded-only orders should be excluded.

## Monthly Revenue

Sum order revenue by month using `main.orders.order_total` where status is completed or paid.

## Average Order Value

Monthly revenue divided by the number of qualifying orders in the same period.

## Caveats

Redacted fields cannot support value-level analysis. Missing status values should be treated as uncertain until inspected.
