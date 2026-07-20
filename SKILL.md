---
name: warehouse-data
description: "Warehouse sales, revenue, units, channels, promotions, and calendar or fiscal time questions over governed Oracle SH star-schema views."
---

# Warehouse Data

Answer warehouse sales, revenue, units, channel, promotion, and calendar or
fiscal time questions by authoring one Oracle `SELECT` over the governed
views below and calling `cognic-tool-oracle-schema/run_readonly_query`.

This instruction skill teaches SQL; it never executes code. The governed
tool runs the query under the asking user's entitlement.

## Query contract

Pass exactly:

- `scope_id`: `warehouse`
- `sql`: one plain Oracle `SELECT`, using only the governed views below
- `max_rows`: optional, default 100 and hard-capped by the tool

Schema-qualify every view. On a refusal, relay the returned message and stop.

## Governed views

### `SH.V_SALES_STAR`

The sales fact at (`PROD_ID`, `CUST_ID`, `TIME_ID`, `CHANNEL_ID`, `PROMO_ID`)
grain.

| column | meaning |
|---|---|
| `PROD_ID`, `CUST_ID` | product and customer keys; names are not exposed |
| `TIME_ID` | sale date; join to `SH.V_CALENDAR` |
| `CHANNEL_ID` | channel key |
| `PROMO_ID` | promotion key; join to `SH.V_PROMOTIONS` |
| `QUANTITY_SOLD` | units sold |
| `AMOUNT_SOLD` | sales revenue |

### `SH.V_CALENDAR`

One row per date. It carries both hierarchies:

- calendar week, month number/description/name, quarter number/description,
  and year;
- fiscal week, month number/description/name, quarter number/description,
  and year.

Join on `SH.V_SALES_STAR.TIME_ID = SH.V_CALENDAR.TIME_ID`.

### `SH.V_PROMOTIONS`

One row per promotion with `PROMO_ID`, `PROMO_NAME`, `PROMO_SUBCATEGORY`,
`PROMO_CATEGORY`, `PROMO_BEGIN_DATE`, and `PROMO_END_DATE`.

`V_PROMOTIONS` deliberately excludes `PROMO_COST`; margin and return-on-cost
questions are unanswerable from this scope.

### `SH.V_SALES_BY_CHANNEL`

One row per channel x calendar-month grain. Columns are `CHANNEL_ID`,
`CHANNEL_DESC`, `CALENDAR_YEAR`, `CALENDAR_MONTH_NUMBER`,
`CALENDAR_MONTH_DESC`, `TOTAL_QUANTITY_SOLD`, and `TOTAL_AMOUNT_SOLD`.

This view is already aggregated. Sum its monthly rows across a wider period,
but do not join it back to day-grain `SH.V_CALENDAR` or counts will fan out.

## Star joins and grain traps

- For fact analysis, join dimensions THROUGH `SH.V_SALES_STAR`, never
  dimension-to-dimension.
- Join each dimension once on its fact key before aggregation.
- The product and customer dimensions are not exposed. Product/customer
  names, categories, regions, demographics, and addresses are unavailable;
  answer with IDs only when the user accepts IDs.
- `AMOUNT_SOLD` is money; `QUANTITY_SOLD` is units. Never substitute one for
  the other.
- State whether a time answer uses the calendar or fiscal hierarchy.
- Filter `TIME_ID` with a direct date range when practical; avoid wrapping the
  fact partition key in a function.

## 9.1 AMBIGUOUS

- `"revenue"` -> `AMOUNT_SOLD` stated-default.
- bare `"sales/sell"` -> present BOTH labeled cuts: revenue from
  `AMOUNT_SOLD` and units from `QUANTITY_SOLD`.
- explicit calendar/fiscal -> answer.

For a revenue question, answer using `AMOUNT_SOLD` and state that default.
For bare sales/sell wording, present both labeled cuts in one answer; do not
force a round trip. Clarification is reserved for identity ambiguity, where
answering every candidate would not resolve which person or entity was meant.
When calendar or fiscal wording is explicit, use that hierarchy and answer
without asking again.

## Worked examples

Calendar-year revenue:

```sql
SELECT SUM(f.amount_sold) AS total_revenue
  FROM sh.v_sales_star f
  JOIN sh.v_calendar c ON c.time_id = f.time_id
 WHERE c.calendar_year = 2020
```

Monthly Internet-channel units from the safe aggregate:

```sql
SELECT calendar_month_desc, SUM(total_quantity_sold) AS units
  FROM sh.v_sales_by_channel
 WHERE channel_desc = 'Internet'
   AND calendar_year = 2020
 GROUP BY calendar_month_desc
 ORDER BY calendar_month_desc
```

Revenue by promotion category:

```sql
SELECT p.promo_category, SUM(f.amount_sold) AS revenue
  FROM sh.v_sales_star f
  JOIN sh.v_promotions p ON p.promo_id = f.promo_id
 GROUP BY p.promo_category
 ORDER BY revenue DESC, p.promo_category
```

## Refusal boundaries

- Raw SH tables and non-governed objects refuse with
  `agent_sql_object_out_of_scope`.
- Margin requires `PROMO_COST`, which is not exposed.
- Named product/customer analysis is unavailable because those dimensions
  are not exposed.
- For PII, dimensions, or another access boundary, name the required
  entitlement/approval and offer to request the governed path. Approval alone
  does not expose data: serving it later also requires a bank-entitled scope.
- For a structurally impossible cross-scope ask with neither grants nor a
  governed join key, accurate boundary naming is sufficient; do not invent an
  approval request path that cannot make the join possible.
- One scope per query. Do not mix SH objects with another data scope.
- One plain `SELECT`; DML, DDL, PL/SQL, locking reads, and multiple statements
  refuse.
- Respect `truncated: true` by narrowing or aggregating the query.
