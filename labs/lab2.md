# Lab 2 · Reflection

**Name:**Suyang Pan
**Due:** Sunday, November 8 at 11:59 PM

Answer in a few sentences each. Specific beats long.

**1. Your join.** Which column connected your two tables? How many rows went in, how many came out, and what did you do about anything that didn't match?

I joined the two tables on country_code. The urban population table had 6,650 rows before the inner join and 6,625 after it. All 25 unmatched rows had the code INX. I kept them in the source data and excluded them from the regional comparison because the lookup table had no region assignment for that code.

**2. The reading.** Kleppmann describes tables (relational), documents (nested, like JSON) and graphs as different ways to model data. Would any of your two tables have been easier to work with as a document or a graph? Why or why not?

I would keep both datasets as relational tables. The population table has one row per country or area per year, and the lookup table has one row per code. This structure made it easy to join on country_code and calculate regional medians in SQL. A nested document would require unpacking the yearly records, and the analysis did not require traversing relationships in a graph.

---

**Checklist before you submit**

- [ ] `notebooks/lab2_joins.ipynb`: Part A run in class, Part B completed with your own tables
- [ ] Every Part B text cell filled in (grain, unmatched rows, what the result tells you)
- [ ] This file answered
- [ ] Notebook saved (Cmd+S), then committed and pushed
- [ ] Repo URL submitted on CourseWorks
