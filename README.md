# intelligent-learning-path-generator

AI-powered system to generate personalized learning paths based on employee profile, course prerequisites, and annual training goals, with dynamic filtering of completed courses.

## Overview

This repository implements the **AI Learning Path Assistant** described in `workflow.md`: a hybrid planner combining practice-to-skill mapping, completion rules, Chroma-backed semantic retrieval, deterministic ranking and hour optimization, and optional LLM explanations.

## Prerequisites

- Python 3.12+
- Excel sources under `data/raw/`: either `user_master.xlsx`, `completion_data.xlsx`, `course_master.xlsx` **or** the capstone export names `User Master List.xlsx`, `Completion Data.xlsx`, `Course Master List.xlsx` (first existing match is used)

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

- `GET /health`
- `POST /generate-plan` with JSON body `{ "portal_id": 123, "target_expertise": "Java", "include_explanation": false }` (retrieval breadth: set **`LEARNING_PATH_TOP_K`** in `.env` on the API host, default `15`). Response includes **`run_id`** (UUID) and **`ragas_evaluation_inputs`**. Optional **`session_run_id`**: same UUID as a prior response for that employee in your client session; the server reuses it only if `data/evaluation/session_runs/<run_id>_session.json` exists and **`portal_id`** matches (otherwise a new **`run_id`** is minted and a row is appended to **`data/evaluation/run_ids/session.csv`**).
- `GET /evaluation/ragas-metrics/{run_id}` — RAGAS faithfulness + answer relevancy JSON (**`OPENAI_API_KEY`** required on the API host). Metrics use **`RAGAS_LLM_MODEL`** (default **`gpt-4o-mini`**) and **`RAGAS_EMBEDDING_MODEL`** (default **`text-embedding-3-small`**) so they stay separate from **`OPENAI_MODEL`** (e.g. o-series). Streamlit uses the last plan’s **`run_id`** when you ask for “RAGAS scores”; API clients pass **`run_id`** explicitly.

## Streamlit UI

Chat-style UI: type a sentence (e.g. “plan for portal 24463, focus on Java”). The app parses **portal ID** and optional **target expertise**, confirms the ID against `user_master`, and calls the API. Use the **➕** control for **Include explanation** and **Include optional courses**. After a successful plan, you can ask for **RAGAS scores** (or **rag scores**); the UI calls the metrics endpoint for the current session’s last plan **`run_id`** and shows a table plus short metric descriptions.

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

- **Programmatic use:** import `evaluation.evaluate_rule_engine` (e.g. `completed_exclusion_accuracy`, `training_goal_coverage`, `practice_keyword_precision`) or `evaluation.evaluate_rag.compare_strategies` in your own script/notebook, with `PYTHONPATH=src` or an editable install.
- **RAGAS note only:** `python src/evaluation/ragas_runner.py` (also sets `sys.path` for `src`).

Full RAGAS runs need a labeled JSONL dataset (see `workflow.md` §12) and your LLM/embeddings configuration; the repo ships scaffolding, not a turnkey RAGAS CLI.

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

## Project layout

See `workflow.md` §8 for the full directory map (`src/`, `app/`, `config/`, `data/`, `tests/`, `notebooks/`).
