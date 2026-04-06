# intelligent-learning-path-generator

AI-powered system to generate personalized learning paths based on employee profile, course prerequisites, and annual training goals, with dynamic filtering of completed courses.

## Overview

This repository implements the **AI Learning Path Assistant** described in `workflow.md`: a hybrid planner combining practice-to-skill mapping, completion rules, Chroma-backed semantic retrieval, deterministic ranking and hour optimization, and optional LLM explanations.

Each successful **`POST /generate-plan`** gets a UUID **`run_id`**, appends a row to **`data/evaluation/run_ids/session.csv`** (new runs only), and saves the full response to **`data/evaluation/session_runs/<run_id>_session.json`** for auditing and **on-demand RAGAS** scoring via **`GET /evaluation/ragas-metrics/{run_id}`**.

## Prerequisites

- Python 3.12+
- Excel sources under `data/raw/` (or set **`LEARNING_PATH_RAW_DIR`**): either `user_master.xlsx`, `completion_data.xlsx`, `course_master.xlsx` **or** the capstone export names `User Master List.xlsx`, `Completion Data.xlsx`, `Course Master List.xlsx` (first existing match is used). Per-file overrides: **`LEARNING_PATH_USER_MASTER_XLSX`**, **`LEARNING_PATH_COMPLETION_XLSX`**, **`LEARNING_PATH_COURSE_MASTER_XLSX`** (see `.env.example`).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Data pipeline

```bash
python run_ingestion.py
```

This preprocesses Excel files to `data/processed/`, writes `course_master_enriched.csv`, and builds the Chroma index under `data/chroma/learning_catalog_db/`.

## API

From the repository root (adds `src` to the path automatically in `main.py`):

```bash
uvicorn api.main:app --app-dir src --reload
```

- `GET /` — redirects to **`/docs`** (Swagger UI)
- `GET /health`
- `POST /generate-plan` — **Minimal body** (only **`portal_id`** is required; other fields default in JSON):

  ```json
  { "portal_id": 123 }
  ```

  Typical optional fields:

  ```json
  {
    "portal_id": 123,
    "target_expertise": "Java",
    "include_explanation": false,
    "include_optional_courses": false
  }
  ```

  Do **not** send **`session_run_id`** until you already have a **`run_id`** from a previous response. For a repeat plan for the same employee in the same client session, pass **`"session_run_id": "<that run_id>"`** so the server can reuse the same run id when the saved session still matches **`portal_id`**.

  Retrieval breadth is **not** in the body: set **`LEARNING_PATH_TOP_K`** in `.env` on the API host (default `15`). The response includes a newly minted or reused **`run_id`**, **`employee_intro`**, **`ragas_evaluation_inputs`**, etc. (see OpenAPI).

- `GET /evaluation/ragas-metrics/{run_id}` — RAGAS **faithfulness** and **answer relevancy** as JSON (**`OPENAI_API_KEY`** or Azure key on the API host). Uses **`RAGAS_LLM_MODEL`** (default **`gpt-4o-mini`**) and **`RAGAS_EMBEDDING_MODEL`** (default **`text-embedding-3-small`**) so metrics stay separate from **`OPENAI_MODEL`** (e.g. o-series for explanations). Loads the snapshot from **`data/evaluation/session_runs/`** (with fallback to a legacy JSON at `data/evaluation/<run_id>_session.json` if present).

**Why two routes:** plan generation stays a focused **`POST /generate-plan`** without embedding evaluation logic. Scoring and future metrics (**`GET /evaluation/...`**) can grow as separate endpoints (or “plugins”) that read the persisted **`run_id`** snapshot, without bloating the plan handler.

## Streamlit UI

Chat-style UI: type a sentence (e.g. “plan for portal 24463, focus on Java”). The app parses **portal ID** and optional **target expertise**, confirms the ID against `user_master`, and calls the API (sending **`session_run_id`** when the same portal was planned again in that browser session). Use the **➕** control for **Include explanation** and **Include optional courses**. After a successful plan, you can ask for **RAGAS scores** (or **rag scores**); the UI calls the metrics endpoint for the session’s last plan **`run_id`** and shows **Run ID**, **Portal ID**, a score table, and short metric descriptions.

With the API running:

```bash
streamlit run app/streamlit_app.py
```

Set the API base URL in the sidebar if it is not `http://127.0.0.1:8000`.

## Evaluation

Rule-engine helpers live under `src/evaluation/`. From the **repo root**:

```powershell
$env:PYTHONPATH = "src"
python -m evaluation
```

Or, without setting `PYTHONPATH`, from the repo root:

```powershell
python src/evaluation/__main__.py
```

That runs a **small demo** (completion exclusion, hour coverage, keyword proxy) and prints **RAGAS** setup notes.

- **Runtime RAGAS (HTTP):** after generating a plan, call **`GET /evaluation/ragas-metrics/{run_id}`** or use the Streamlit RAGAS prompt. Implementation: `src/evaluation/ragas_metrics.py` reads the saved session payload from **`session_store`**.
- **Programmatic use:** import `evaluation.evaluate_rule_engine` (e.g. `completed_exclusion_accuracy`, `training_goal_coverage`, `practice_keyword_precision`) or `evaluation.evaluate_rag.compare_strategies` in your own script/notebook, with `PYTHONPATH=src` or an editable install.
- **Offline RAGAS note:** `python src/evaluation/ragas_runner.py` (also sets `sys.path` for `src`).

Offline RAGAS experiments may use a labeled JSONL dataset (see `workflow.md` §12); the HTTP metrics path scores whatever was stored for that **`run_id`**.

## Tests

```bash
set PYTHONPATH=src
python -m pytest tests -v
```

On WSL, activate your project virtualenv and run the same `pytest` command from the repo root with `PYTHONPATH=src`.

## Configuration

- `config/practice_skill_map.yaml` — practice → skill keywords
- `config/retrieval_config.yaml` — Chroma collection name and merge settings
- `config/parser_config.yaml` — duration regexes and fallbacks
- **`.env`** (copy from `.env.example`) — API keys, **`OPENAI_MODEL`** / optional **`OPENAI_REASONING_EFFORT`** for explanations, **`RAGAS_LLM_MODEL`** / **`RAGAS_EMBEDDING_MODEL`** for metric calls, **`LEARNING_PATH_TOP_K`**, optional raw data paths

## Project layout

See `workflow.md` §8 for the full directory map (`src/`, `app/`, `config/`, `data/`, `tests/`, `notebooks/`). Notable data dirs:

- `data/evaluation/session_runs/` — `<run_id>_session.json` snapshots from the API
- `data/evaluation/run_ids/session.csv` — append-only log of new **`run_id`** values
