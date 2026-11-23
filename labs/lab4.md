# Labs 3 + 4 · Pipeline submission

**Name:** Suyang Pan
**Due:** Sunday, November 22 at 11:59 PM

## Links

**A successful run of your pipeline** (Actions tab → the green run → copy the address):
https://github.com/sp4609/data-infra-project/actions/runs/45164564628

**A deliberately failed run** (Run workflow with "Break the data on purpose" ticked → the red run → copy the address):
https://github.com/sp4609/data-infra-project/actions/runs/45165095909

**Your table on MotherDuck:** `course.main.population_growth`

## Reflections

Answer in a few sentences each. Specific beats long.

**1. Your checks.** Which of your checks would you be most worried to see fail, and what would go wrong for a user of your app if bad data got through?

I would be most worried if the country-year key check failed. A duplicate country-year record could give one country extra weight in the annual average and inflate the number of countries reported as having declining populations. Missing keys could also prevent records from matching the urban population data.

**2. Run it twice.** What happens to your MotherDuck table if your pipeline runs twice in one day? How do you know?

Run it twice. If both runs pass validation, the second run replaces the first run’s tables. I know this because the publish step uses `CREATE OR REPLACE TABLE`. If the source data is identical, the row counts and values stay the same. If the second run fails validation, the previous tables stay in place.

**3. Your schedule.** How often does your source actually update? Is daily the right schedule for it, and would you take a full copy or only what's new?

The World Bank population growth indicator is annual, and my pipeline uses a fixed 2015–2023 window. I would refresh it when the World Bank revises the series. I would take a full copy of that window each time so the pipeline picks up corrections to earlier years as well.

**4. What leaves your control.** Next week an AI model will see your table's description and users' questions. Is there anything in your data, or anything a user might type, that shouldn't be sent to a free AI service? Why or why not?

My table contains public, country-level World Bank statistics, so its schema and description are fine to share. A user’s question could still contain a name, address, or API token. I would remove that information before sending the question to an external AI service because it is unnecessary for querying the table and the service may retain prompts.
---

## Set up your secrets (once)

Your MotherDuck token is a password. It goes in two secret stores, **never** in a file, a notebook, or an AI chat.

**Get a token:** app.motherduck.com → your name (bottom left) → **Settings** → **Access Tokens** → **Create token**. Name it `codespaces`. Copy it.

**A. For your Codespace** (so `python pipeline.py` can publish):
github.com → your profile picture → **Settings** → **Codespaces** → **New secret**. Name `MOTHERDUCK_TOKEN`, paste the token, choose your course repo under **Repository access**, **Add secret**. Then restart your Codespace.

**B. For GitHub Actions** (so the daily run can publish):
your course repo on github.com → **Settings** (repo tab, not your profile) → **Secrets and variables** → **Actions** → **New repository secret**. Name `MOTHERDUCK_TOKEN`, paste the same token, **Add secret**.

If a token ever leaks, delete it in MotherDuck right away and make a new one (then update both secrets).

---

**Checklist before you submit**

- [ ] `project.toml` points to **your** API, with at least five checks of your own (each with a why) and at least three tables: one clean table and at least two analysis tables (trend, key metrics or ranking)
- [ ] `docs/findings.md`: three findings, each backed by one of your tables
- [ ] A green run and a red run on the Actions tab, both linked above
- [ ] `docs/data_dictionary.md` filled in for every table you publish
- [ ] This file answered
- [ ] No token anywhere in your files (tokens start with `eyJ`: search your repo with Cmd+Shift+F)
- [ ] Committed and pushed; repo URL submitted on CourseWorks
