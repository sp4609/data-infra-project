"""
pipeline.py · Labs 3 + 4 · the pipeline "engine"

YOU DON'T NEED TO EDIT THIS FILE. Your project lives in project.toml.

Every run does five steps, in order:
  1. EXTRACT    fetch every page from the API in project.toml
  2. LOAD       put the rows in a table called raw
  3. VALIDATE   run your checks; if any fail, STOP and publish nothing
  4. TRANSFORM  build the tables listed in project.toml
                (and print answers to any [[report]] questions)
  5. PUBLISH    write them to MotherDuck

How to run it (in your Codespace terminal):
  python pipeline.py            run the whole pipeline
  python pipeline.py --preview  just show the columns and a few rows from your API
GitHub Actions runs `python pipeline.py` every day (see .github/workflows/pipeline.yml).
"""

import os
import sys
import time
import tomllib
from datetime import datetime, timezone, timedelta

import duckdb
import pandas as pd
import requests

SETTINGS_FILE = os.environ.get("PROJECT_FILE", "project.toml")


# ----------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------
def log(step, message):
    """Every line gets a time and a step name, so the run log tells a story."""
    now = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"{now}  [{step:<9}] {message}", flush=True)


def get_json(url, params=None, tries=5, pause=3):
    """Ask the API for data. Waits up to 2 minutes, and retries if the server is slow or busy."""
    for attempt in range(1, tries + 1):
        try:
            r = requests.get(url, params=params, timeout=(10, 120))
            if r.status_code == 429 or r.status_code >= 500:     # busy or broken: worth retrying
                raise requests.HTTPError(f"status {r.status_code}")
            if r.status_code >= 400:                               # our mistake: say so clearly
                raise ValueError(f"the API said {r.status_code}: {r.text[:300]}")
            return r.json()
        except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
            if attempt == tries:
                raise
            log("extract", f"attempt {attempt} failed ({e}); retrying in {pause * attempt}s")
            time.sleep(pause * attempt)


def auto_types(df, keep_as_text=()):
    """APIs often send numbers and dates as text. Convert columns that are clearly numbers or dates.
    Codes stay text: anything listed in keep_as_text, or with zip/code/id in its name."""
    for col in df.columns:
        if col in keep_as_text or any(w in col.lower() for w in ("zip", "code", "_id", "fips", "bbl", "bin")):
            continue
        s = df[col]
        if not (s.dtype == object or pd.api.types.is_string_dtype(s)):
            continue
        nonnull = s.dropna()
        if nonnull.empty or not all(isinstance(v, str) for v in nonnull):
            continue
        nonnull = nonnull.astype(str)
        as_num = pd.to_numeric(nonnull, errors="coerce")
        looks_like_code = nonnull.str.match(r"^0\d").any()     # keep ZIP codes like 02139 as text
        if as_num.notna().all() and not looks_like_code:
            df[col] = pd.to_numeric(s, errors="coerce")
            continue
        if nonnull.str.match(r"^\d{4}-\d{2}-\d{2}").all():
            df[col] = pd.to_datetime(s, errors="coerce", utc=True).dt.tz_localize(None)
    return df


def flatten(rows):
    """Turn a list of nested JSON records into a flat table (a.b becomes a_b)."""
    df = pd.json_normalize(rows)
    df.columns = [c.replace(".", "_") for c in df.columns]
    return df


# ----------------------------------------------------------------------------
# Step 1: EXTRACT, one function per kind of API
# ----------------------------------------------------------------------------
def extract_socrata(src):
    """NYC Open Data and most city portals: pages of up to 1,000 rows, using $limit and $offset."""
    params = {"$order": ":id"}                       # a stable order, so pages don't overlap
    if src.get("columns"):
        params["$select"] = ", ".join(src["columns"])
    where = [w for w in [src.get("filter", "")] if w]
    if src.get("date_column") and src.get("days_back"):
        since = (datetime.now(timezone.utc) - timedelta(days=int(src["days_back"]))).strftime("%Y-%m-%dT00:00:00")
        where.append(f"{src['date_column']} >= '{since}'")
    if where:
        params["$where"] = " AND ".join(f"({w})" for w in where)

    max_rows = int(src.get("max_rows", 20000))
    page_size, rows, page = min(1000, max_rows), [], 0
    while len(rows) < max_rows:
        batch = get_json(src["url"], {**params, "$limit": page_size, "$offset": page * page_size})
        rows.extend(batch)
        page += 1
        log("extract", f"page {page}: {len(batch)} rows")
        if len(batch) < page_size:                   # a short page means we've reached the end
            break
        time.sleep(0.5)                              # be polite between pages
    df = flatten(rows[:max_rows])
    for col in src.get("columns", []):               # Socrata leaves out fields that are empty
        if col not in df.columns:
            df[col] = None
    return auto_types(df, src.get("keep_as_text", []))


def extract_worldbank(src):
    """World Bank: any indicator, for countries only (regions and income groups are removed)."""
    base = "https://api.worldbank.org/v2"

    def pages(url, params):
        rows, page = [], 1
        while True:
            meta, records = get_json(url, {**params, "format": "json", "page": page})
            rows.extend(records or [])
            log("extract", f"page {meta['page']} of {meta['pages']}: {len(records or [])} rows")
            if page >= meta["pages"]:
                return rows
            page += 1
            time.sleep(0.5)

    rows = pages(f"{base}/country/all/indicator/{src['indicator']}",
                 {"date": src.get("years", "2015:2023"), "per_page": 1000})
    data = flatten(rows).rename(columns={"countryiso3code": "country_code", "country_value": "country",
                                         "date": "year", "value": "value"})
    data = data[["country_code", "country", "year", "value"]]
    data["year"] = pd.to_numeric(data["year"])

    countries = flatten(pages(f"{base}/country", {"per_page": 500}))
    countries = countries.rename(columns={"id": "country_code", "region_value": "region",
                                          "incomeLevel_value": "income_level"})
    countries = countries[countries["region"].str.strip() != "Aggregates"]
    before = len(data)
    data = data.merge(countries[["country_code", "region", "income_level"]], on="country_code")
    log("extract", f"kept {len(data)} rows for countries; removed {before - len(data)} rows "
                   f"for regions and income groups (they are not countries)")
    return data


def extract_json(src):
    """Any other API that returns a plain list of records in one request."""
    data = get_json(src["url"], src.get("params", {}))
    if isinstance(data, dict):
        key = src.get("records_key")
        data = data[key] if key else next(v for v in data.values() if isinstance(v, list))
    log("extract", f"1 request: {len(data)} rows")
    df = flatten(data)
    if src.get("columns"):
        df = df[[c for c in src["columns"] if c in df.columns]]
    return auto_types(df, src.get("keep_as_text", []))


EXTRACTORS = {"socrata": extract_socrata, "worldbank": extract_worldbank, "json": extract_json}


# ----------------------------------------------------------------------------
# Steps 2 to 5
# ----------------------------------------------------------------------------
class ValidationError(Exception):
    pass


def load(con, df):
    con.register("incoming", df)
    con.sql("CREATE OR REPLACE TABLE raw AS SELECT * FROM incoming")    # replace, never append
    con.unregister("incoming")
    log("load", f"raw: {len(df)} rows, {len(df.columns)} columns")


def validate(con, checks):
    builtin = [{"name": "raw is not empty", "sql": "SELECT CASE WHEN count(*) > 0 THEN 0 ELSE 1 END FROM raw"}]
    failures = []
    for check in builtin + checks:
        try:
            problems = con.sql(check["sql"]).fetchone()[0]
        except Exception as e:
            raise ValidationError(f"the check '{check['name']}' has an SQL error: {e}")
        status = "PASS" if problems == 0 else "FAIL"
        log("validate", f"{status}  {check['name']}  ({problems} problem rows)")
        if problems:
            failures.append(check["name"])
    if failures:
        raise ValidationError(f"{len(failures)} check(s) failed: {failures}")
    log("validate", "all checks passed")


def transform(con, tables):
    for t in tables:
        try:
            con.sql(f"CREATE OR REPLACE TABLE {t['name']} AS {t['sql']}")
        except Exception as e:
            raise RuntimeError(f"the table '{t['name']}' has an SQL error: {e}")
        n = con.sql(f"SELECT count(*) FROM {t['name']}").fetchone()[0]
        log("transform", f"{t['name']}: {n} rows")


def report(con, questions):
    """Answer the questions in [[report]], from the tables the pipeline just built."""
    if not questions:
        return
    print("\n" + "=" * 70, flush=True)
    print("  WHAT THE DATA SAYS  (the [[report]] questions in project.toml)", flush=True)
    print("=" * 70, flush=True)
    for q in questions:
        print(f"\nQ: {q['question']}", flush=True)
        try:
            df = con.sql(q["sql"]).df().head(10)
            with pd.option_context("display.max_columns", 10, "display.width", 120):
                print(df.to_string(index=False), flush=True)
        except Exception as e:
            print(f"   (this question's SQL has an error: {e})", flush=True)
    print("", flush=True)


def motherduck_token():
    # GitHub stores secret names in capitals; DuckDB looks for either spelling.
    token = os.environ.get("MOTHERDUCK_TOKEN") or os.environ.get("motherduck_token")
    if token:
        os.environ["motherduck_token"] = token
    return token


def publish(con, tables, project_name):
    if not motherduck_token():
        if os.environ.get("GITHUB_ACTIONS"):
            raise RuntimeError("MOTHERDUCK_TOKEN secret is missing. Add it under "
                               "Settings -> Secrets and variables -> Actions.")
        log("publish", "no MotherDuck token found: skipping publish (local test only)")
        return
    md = duckdb.connect("md:")
    md.sql("CREATE DATABASE IF NOT EXISTS course")
    for t in tables:
        md.register("to_share", con.sql(f"SELECT * FROM {t['name']}").df())
        md.sql(f"CREATE OR REPLACE TABLE course.main.{t['name']} AS SELECT * FROM to_share")
        md.unregister("to_share")
        n = md.sql(f"SELECT count(*) FROM course.main.{t['name']}").fetchone()[0]
        log("publish", f"course.main.{t['name']}: {n} rows on MotherDuck")
    md.sql(f"""CREATE OR REPLACE TABLE course.main.pipeline_runs AS
               SELECT '{project_name}' AS project, now() AS last_success""")
    md.close()


def read_settings():
    try:
        with open(SETTINGS_FILE, "rb") as f:
            s = tomllib.load(f)
    except FileNotFoundError:
        sys.exit(f"Can't find {SETTINGS_FILE}. Run this from the top folder of your repo.")
    except tomllib.TOMLDecodeError as e:
        sys.exit(f"{SETTINGS_FILE} has a typo: {e}\n"
                 "Check quotes and brackets on that line. Text goes in \"double quotes\".")
    kind = s.get("source", {}).get("type")
    if kind not in EXTRACTORS:
        sys.exit(f"In {SETTINGS_FILE}, [source] type must be one of {list(EXTRACTORS)}, not {kind!r}.")
    return s


def preview(settings):
    src = settings["source"]
    log("preview", f"asking {src.get('url', src.get('indicator'))} for a sample")
    if src["type"] == "socrata":
        df = EXTRACTORS["socrata"]({**src, "max_rows": 5})
    else:
        df = EXTRACTORS[src["type"]](src).head(5)
    print("\nColumns (use these names in project.toml):")
    for col, dtype in df.dtypes.items():
        print(f"  {col:<30} {dtype}")
    print("\nFirst rows:")
    with pd.option_context("display.max_columns", 12, "display.width", 160):
        print(df.head(5).to_string(index=False))


def main():
    settings = read_settings()
    if "--preview" in sys.argv:
        preview(settings)
        return

    project = settings.get("project", {}).get("name", "my_project")
    started = time.time()
    log("start", f"pipeline for '{project}'")
    con = duckdb.connect()                # a fresh in-memory database every run
    try:
        df = EXTRACTORS[settings["source"]["type"]](settings["source"])
        load(con, df)
        if os.environ.get("BREAK_IT", "").lower() == "true":
            con.sql("DELETE FROM raw")
            log("load", "BREAK_IT is on: emptied raw on purpose, to test the checks")
        validate(con, settings.get("checks", []))
        transform(con, settings.get("tables", []))
        report(con, settings.get("report", []))
        publish(con, settings.get("tables", []), project)
    except ValidationError as e:
        log("STOPPED", f"{e}. Nothing was published; yesterday's tables are untouched.")
        sys.exit(1)                       # a non-zero exit turns the GitHub Actions run red
    except Exception as e:
        log("STOPPED", f"{type(e).__name__}: {e}")
        sys.exit(1)
    log("done", f"success in {time.time() - started:.0f}s")


if __name__ == "__main__":
    main()
