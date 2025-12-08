# Copilot / AI Agent Instructions for Workforce System

Short purpose: help AI agents make useful, safe edits and be aware of project-specific constraints.

- Summary
  - CLI-based workforce analytics for a MySQL backend. Main entry: `main.py`.
  - Key modules: `modules/db.py` (connection/context manager), `modules/crud.py` (SQL CRUD), `modules/analytics.py` (business logic), `modules/textlog.py` (file-logging).
  - DB config via `config/db_config.py` using env vars: `WORKFORCE_DB_HOST`, `WORKFORCE_DB_PORT`, `WORKFORCE_DB_USER`, `WORKFORCE_DB_PASSWORD`, `WORKFORCE_DB_NAME`, `WORKFORCE_DB_TIMEOUT`.

- Big picture architecture
  - This is a small, single-process CLI app that interacts with a MySQL database. The `Database` class in `modules/db.py` owns connections and yields a `mysql.connector` connection via a context manager.
  - `modules/crud.py` contains SQL statements and is the single place that talks to schema objects (tables/views). Agents should modify this file for data-layer changes.
  - `modules/analytics.py` imports CRUD helpers and runs domain logic (headcount, payroll projection, weekly hours). Changes that affect the shape of employee or time entry rows must update analytics accordingly.

- Developer workflows (quick commands)
  - Setup virtualenv and deps (PowerShell):

    ```powershell
    python -m venv .venv
    .\.venv\Scripts\Activate
    python -m pip install -r requirements.txt
    ```

  - Run the CLI: `python main.py`
  - Set DB host/credentials for the session in PowerShell:

    ```powershell
    $env:WORKFORCE_DB_HOST = "localhost"
    $env:WORKFORCE_DB_PORT = "3306"
    $env:WORKFORCE_DB_USER = "root"
    $env:WORKFORCE_DB_PASSWORD = "password"
    $env:WORKFORCE_DB_NAME = "workforce"
    ```

- Important project-specific patterns and conventions
  - Use `Database` context manager `with db.connect() as conn:` and `conn.cursor(dictionary=True)` to operate on rows as dicts.
  - Always use parameterized queries (the code uses `%s` placeholders) to avoid SQL injection; queries are committed explicitly with `conn.commit()`.
  - When commanding table or view names from user input, the code validates existence in `information_schema` (`list_database_views`, `list_database_tables`) then uses backticks to safely access that object.
  - Logging is configured in `modules/textlog.py` and writes to `logs/workforce.log`. Do not log secrets (DB password).

- Schema assumptions and initialization
  - `Database.initialize()` is currently a no-op: the project expects an existing schema. You must not assume migrations or auto-creation; check schema externally.
  - Commonly-referenced tables and views (exhaustive list found in code): `employees`, `department`, `shift`, `time_records`, `payroll`, and views `v_burnout_ranking`, `v_daily_payroll`, `v_weekly_hours_summary`.

- Critical integration points
  - MySQL connector: dependency `mysql-connector-python` (see `requirements.txt`). The app uses `mysql.connector` directly.
  - Environment variables determine the DB connection; tests or CI should set those variables to a test database.
  - File logging path: `logs/workforce.log` (configured in `modules/textlog.py`).

- Codebase gotchas and cross-file consistency (must-read for agents)
  - Watch for naming mismatches between modules and `main.py` (employee vs emp_id/id; time entries: `add_time_record` vs `add_time_entry`, `fetch_time_records` vs `fetch_time_entries`). Before changing any function/field name, update callers across modules and CLI.
  - Rows are returned as dictionaries; keys may vary across schema versions (e.g., `emp_id` vs `id` and `hours_worked` vs `hours`). When editing analytics or CLI code, normalize both possibilities or standardize the schema and update all call sites.
  - `modules/db.py` mutates `sys.path` when executed directly: keep the import structure intact when adding new modules.

- Example tasks and how to approach them (practical examples)
  1) Add a new field `email` to `employees` and expose it in the CLI:
     - Update SQL in `modules/crud.py` `add_employee`, `get_all_employees`, `update_employee`.
     - Update `main.py` flows that add/update/list employees to prompt/display `email`.
     - Update `modules/analytics.py` if any code references employee columns by position or name.
  2) Add a new view preview option to `featured_views_flow`:
     - Add the view name to the list in `main.py`.
     - No DB schema changes needed if view exists; otherwise, ensure DB has the view.

- Tests and CI (notes for agents)
  - There are no unit tests in the workspace. When adding tests:
    - Prefer Pytest and local DB fixtures or mocking `Database` to avoid needing a MySQL server.
    - For small integration testing, use a disposable MySQL instance or a test DB schema.

- Safety and security
  - The `config/db_config.py` provides default DB credentials (including a default password). This is not secure for production; avoid committing or publishing secrets.
  - Always validate user-supplied table/view names using metadata (follow `fetch_view_rows`/`fetch_table_rows` examples).

- Recommended edits and refactors for maintainability (when appropriate)
  - Normalize row keys and unify names: pick `employee_id` or `emp_id` consistently across `modules/crud.py`, `modules/analytics.py`, and `main.py`.
  - Add a helper to normalize dict keys across older schema variations and document it in `modules/analytics.py`.
  - Add a small migration script or Dockerized test DB schema to make setup reproducible.

  - Naming mismatches (concrete examples)
    - Example 1: `main.py` imports `add_time_entry` and `fetch_time_entries`, while `modules/crud.py` implements `add_time_record` and `fetch_time_records`.
      - When you change one, update the other import or rename the implementation across modules.
    - Example 2: `modules/crud.py` and `modules/analytics.py` may use different employee identifiers: `emp_id` (string) vs `id` (int). Use a normalization helper or standardize on one key and update all call sites.


---

If you want, I can:
- Add a simple `README.md` describing the schema and run instructions.
- Add a migration script to bootstrap a test schema or a quick Pytest scaffold with a DB mock.

Please tell me any particular areas you want emphasized or if you want an initial PR with the README/test scaffold.