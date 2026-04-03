# AI Learning Path Assistant

## 📌 Overview

This project builds an **intelligent learning path generation system** that creates personalized course plans for employees based on:

* Employee profile (grade, practice, training goal)
* Completed courses
* Course metadata (summary, prerequisites, duration)
* Target expertise (e.g., Java, Data Engineering)

The system combines:

* **Rule-based planning (deterministic core)**
* **Semantic search (ChromaDB)**
* **Optional LLM reasoning (GenAI enhancement)**

---

## 🎯 Objectives

* Generate **personalized learning plans**
* Remove **already completed courses**
* Maintain **prerequisite order**
* Optimize plan based on **annual training hours**
* Provide **explanations using LLM (optional)**

---

## 🧱 High-Level Architecture

```
                ┌────────────────────┐
                │   Streamlit UI     │
                └─────────┬──────────┘
                          │ API Call
                          ▼
                ┌────────────────────┐
                │   FastAPI Backend  │
                │ (Core Orchestrator)│
                └─────────┬──────────┘
                          │
        ┌─────────────────┼─────────────────┐
        ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────┐
│ User Service │  │ Completion   │  │ Course Service │
│ (Pandas)     │  │ Service      │  │ + ChromaDB     │
└──────────────┘  └──────────────┘  └────────────────┘
        │                 │                 │
        └────────────┬────┴───────┬────────┘
                     ▼            ▼
              ┌────────────────────────┐
              │ Learning Plan Engine   │
              │ - Filter completed     │
              │ - Resolve prerequisites│
              │ - Optimize hours       │
              └────────────┬───────────┘
                           ▼
                 ┌────────────────────┐
                 │ LLM (Optional)     │
                 │ Explanation Layer  │
                 └────────────────────┘
                           ▼
                    Final Response
```

---

## 📂 Project Structure

```
ai-learning-path-assistant/
│
├── data/
│   ├── raw/                 # Excel files
│   ├── processed/           # Clean CSVs
│   └── chroma/              # Vector DB storage
│
├── src/
│   ├── ingestion/           # Data loading & Chroma build
│   ├── services/            # Business logic services
│   ├── planning/            # Learning plan engine
│   ├── llm/                 # LLM integration (optional)
│   ├── api/                 # FastAPI routes
│   └── utils/               # Helpers
│
├── app/                     # Streamlit UI
├── tests/
├── requirements.txt
└── README.md
```

---

## 📊 Data Sources

### 1. User Master

* Portal ID (Primary Key)
* Grade
* Training Goal (hours/year)
* Practice / Country

### 2. Completion Data

* Portal ID
* Course ID
* Completion Status

### 3. Course Master

* Course ID
* Course Name
* Summary (contains prerequisites + duration)

---

## 🔄 End-to-End Flow

### Step 1: Input

```
Portal ID + Target Expertise
```

---

### Step 2: Fetch User

* Get employee profile
* Extract:

  * grade
  * training goal

---

### Step 3: Fetch Completed Courses

* Filter:

```
Completion Status = completed
```

---

### Step 4: Retrieve Relevant Courses

Two approaches:

#### Option A (Rule-based)

* Keyword match on course title/summary

#### Option B (Recommended)

* Use **ChromaDB semantic search**

```
Query: "Java developer courses"
→ Retrieve top relevant courses
```

---

### Step 5: Extract Metadata from Summary

From course summary extract:

* prerequisites
* intended audience
* duration (hours)

---

### Step 6: Filter Courses

Remove:

* already completed courses
* courses not suitable for employee grade

---

### Step 7: Resolve Prerequisites

Ensure order:

```
Prerequisite → Main Course
```

---

### Step 8: Optimize for Training Hours

* Target = Training Goal
* Compute:

  * completed hours
  * remaining hours
* Add courses until target is met

---

### Step 9: Generate Final Plan

Return:

* ordered course list
* course duration
* total planned hours
* remaining gap

---

### Step 10 (Optional): LLM Explanation

Generate:

* reasoning for course selection
* skill gap summary

---

## 🧠 Core Components

---

### 1. Ingestion Pipeline

#### Input:

Excel files

#### Output:

* Pandas DataFrames
* ChromaDB index (course master)

---

### 2. ChromaDB (Vector Store)

Used for:

* semantic search on course summaries

Stored in:

```
data/chroma/learning_catalog_db/
```

---

### 3. Learning Plan Engine

Responsibilities:

* filter completed courses
* resolve prerequisites
* order courses
* calculate hours

---

### 4. API Layer (FastAPI)

Endpoints:

```
POST /generate-plan
GET /health
```

---

### 5. UI Layer (Streamlit)

Features:

* input portal ID
* select expertise
* display plan
* show explanation

---

## ⚙️ Implementation Steps

---

### Phase 1: Setup

* Create repo structure
* Install dependencies:

```
pip install pandas chromadb openpyxl fastapi streamlit
```

---

### Phase 2: Data Ingestion

* Load Excel into DataFrames
* Clean missing values
* Store processed CSVs

---

### Phase 3: Build ChromaDB

* Convert course rows → documents
* Embed summaries
* Store in Chroma

---

### Phase 4: Backend Services

Implement:

* user_service
* completion_service
* course_service
* planning_engine

---

### Phase 5: Learning Plan Logic

Implement:

* completed course filtering
* prerequisite ordering
* duration calculation

---

### Phase 6: API Layer

* Create FastAPI endpoints
* Integrate services

---

### Phase 7: UI

* Build Streamlit interface
* Connect to backend API

---

### Phase 8: LLM Integration (Optional)

* Explanation generation
* Skill gap summary

---

## 📊 Sample Output

```json
{
  "portal_id": 24463,
  "employee_name": "Shefali Joisa",
  "training_goal_hours": 16,
  "completed_hours": 4,
  "remaining_hours": 12,
  "recommended_courses": [
    {
      "course_name": "JAXP",
      "hours": 3
    },
    {
      "course_name": "Effective Java",
      "hours": 4
    }
  ],
  "total_planned_hours": 7,
  "gap_after_plan": 5
}
```

---

## 🚀 Optional Enhancements

* LLM-based prerequisite extraction
* Skill gap analysis
* Conversational interface
* Recommendation scoring
* Course clustering

---

## ⚠️ Design Considerations

* Do NOT use L1–L6 for learning logic
* Use summary carefully (noise vs signal)
* Handle missing duration gracefully
* Ensure deterministic core logic

---

## 🎯 Final Positioning

> AI-powered learning path assistant that combines structured employee data, unstructured course metadata, and intelligent planning logic to generate personalized, prerequisite-aware, and goal-driven learning plans.

---

## ✅ Success Criteria

* Correct filtering of completed courses
* Logical course sequencing
* Training goal alignment
* Clean API + UI integration
* Optional AI explanation layer

---

## 🔥 Future Scope

* Multi-skill recommendation
* Integration with LMS
* Reinforcement learning feedback loop
* Personalized difficulty adjustment

---
