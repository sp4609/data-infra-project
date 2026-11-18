# Lab 3 · Reflection and project dataset choice

**Name:**
**Due:** Sunday, November 15 at 11:59 PM

Answer in a few sentences each. Specific beats long.

**1. Your checks.** Which of your five checks would you be most worried to see fail, and what would go wrong downstream if it did?

**2. Local vs. cloud.** Your data now lives in two places: `lab3.duckdb` in your Codespace and a table on MotherDuck. When would you want each one?

**3. The reading.** *Fundamentals of Data Engineering* Chapter 7 describes ingestion as more than "download the file": how often data arrives, whether you take a full copy or only what changed, and what happens when the source changes its format. Pick one of those and say how it applies to your API.

---

## Project dataset choice

**API name and link to its documentation:**

**The request URL you used** (no keys or tokens in it):

**Sample response** (paste 1–2 records, or a short excerpt):

```
paste here
```

**What one row means (the grain):**

**Why it fits your project idea** (2–3 sentences):

---

## Set up your MotherDuck token (do this once)

Your token is a password. It goes in a Codespaces secret, **never** in a notebook, a file, or an AI chat.

1. Go to **app.motherduck.com** → click your name (bottom left) → **Settings** → **Access Tokens** → **Create token**. Name it `codespaces`, then copy it.
2. Go to **github.com** → your profile picture → **Settings** → **Codespaces** (left menu) → **New secret**.
3. Name: `MOTHERDUCK_TOKEN` (GitHub shows secret names in capitals). Value: paste the token. Under **Repository access**, pick your course repo. Click **Add secret**.
4. Back in your Codespace, a banner may offer to reload. If not: **Cmd+Shift+P** → type **Rebuild** → choose **Codespaces: Rebuild Container**, or stop and restart the Codespace.
5. Rerun cell A7. It should print `rows_in_cloud`.

---

**Checklist before you submit**

- [ ] `notebooks/lab3_live_data.ipynb`: Part A run in class; Part B completed with your own API (two or more pages, five checks with a why for each, written to MotherDuck)
- [ ] This file answered, including the project dataset choice
- [ ] No token anywhere in your files: tokens start with `eyJ`, so search your repo (Cmd+Shift+F) for `eyJ`
- [ ] Notebook saved (Cmd+S), then committed and pushed
- [ ] Repo URL submitted on CourseWorks
