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
- `POST /generate-plan` with JSON body `{ "portal_id": 123, "target_expertise": "Java", "include_explanation": false }` (retrieval breadth: set **`LEARNING_PATH_TOP_K`** in `.env` on the API host, default `15`)

## Streamlit UI

Chat-style UI: type a sentence (e.g. “plan for portal 24463, focus on Java”). The app parses **portal ID** and optional **target expertise**, confirms the ID against `user_master`, and calls the API. Use the **➕** control for **Include explanation** and **Include optional courses**.

With the API running:

```bash
streamlit run app/streamlit_app.py
```

Set the API base URL in the sidebar if it is not `http://127.0.0.1:8000`.

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
