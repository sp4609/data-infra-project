# Lab 1: Data Lifecycle Map
Suyang Pan

## Data Product

A tool for exploring urban population shares from 2000 to 2024,
using World Bank indicator data and country metadata.

## 1. Ingestion

I downloaded the World Bank CSV archive for indicator
SP.URB.TOTL.IN.ZS and extracted the indicator and country metadata.
I selected 2000–2024, reshaped the indicator into long format,
and saved both tables in the data folder.

Source: https://data.worldbank.org/indicator/SP.URB.TOTL.IN.ZS

## 2. Validation

I loaded both CSV files into DuckDB and inspected their types using
DESCRIBE and their column profiles using SUMMARIZE. The main table
contains 6,650 rows, and the metadata table contains 265 rows.

The main table has 25 missing indicator values (0.38%), no duplicate
country-year keys, and no non-missing percentages outside 0–100.
Neither table has missing country codes. Metadata codes are unique.

Of 266 distinct main-table codes, 265 match the metadata.
INX ("Not classified") is the only unmatched code.

## 3. Transformation

I renamed the main-table columns and converted the annual columns
into year and urban_pct fields. Empty fields and common missing-value
markers were recognized as NULL during loading.

I preserved missing percentages rather than replacing them with zero.
For the economy ranking, I restricted the main table to codes with
non-missing Region metadata to exclude aggregate groups. This rule
should be reviewed if the metadata structure changes.

The future join key is:
urban.country_code = countries."Country Code".

A left join would preserve all main-table records, including INX,
while leaving its metadata fields missing. Current income groups
must not be interpreted as historical classifications for every year.

## 4. Scheduling — Proposed

No automated refresh is implemented in this lab.
For a future application, I would check for source updates quarterly
and after the annual income-classification release.

Each refresh should retain a dated source snapshot and rerun type,
missingness, range, uniqueness, and key-coverage checks.
Unexpected changes should be reviewed before replacing published data.

## 5. Interface — Proposed

A user could select an economy and view its annual urban population
share, with a table showing the underlying values.

Example question:
"How has China's urban population share changed between 2000 and 2024?"

The interface should show the source, observation years, and retrieval
date. It should display missing values explicitly and distinguish
economies from aggregate groups. It should explain that national urban
definitions may differ and that urban share does not measure housing
quality or infrastructure performance.

## Most Fragile Stage

Transformation is the most fragile stage for these tables.
A query can run successfully while mixing economies with overlapping
aggregate groups, excluding unmatched codes without explanation,
or applying current income classifications to historical years.

These choices can produce plausible but misleading results.
Explicit filtering rules, join-coverage checks, and documentation
are therefore necessary before interpreting comparisons.
