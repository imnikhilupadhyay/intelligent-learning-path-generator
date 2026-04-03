# AI Learning Path Assistant

## 📌 Overview

This project builds an **intelligent learning path generation system** that creates personalized course plans for employees based on:

* Employee profile (grade, practice, training goal)
* Completed courses
* Course metadata (summary, prerequisites, duration)
* Target expertise (e.g., Java, Data Engineering)
* **Practice → Skill mapping (NEW enhancement)**

The system combines:

* **Rule-based planning (deterministic core)**
* **Semantic search (ChromaDB)**
* **Practice-aware recommendation engine (NEW)**
* **Optional LLM reasoning (GenAI enhancement)**

---

## 🎯 Objectives

* Generate **personalized learning plans**
* Remove **already completed courses**
* Maintain **prerequisite order**
* Optimize plan based on **annual training hours**
* Use **practice-based skills for relevance**
* Provide **explanations using LLM (optional)**

---

## 🧠 Practice → Skill Mapping (CORE INTELLIGENCE LAYER 🔥)

### 📌 Why this is needed

The `user_master` table contains:

* `emp_practise`

But it does NOT define:

* primary technical skills
* course recommendations

👉 This layer bridges that gap.

---

### 🔷 Practice Mapping

#### 🟦 Application Services

**Skills:**

* Programming (Java, Python, .NET)
* Backend / Frontend
* Testing (Selenium)
* Architecture (OOP, Design Patterns)

---

#### 🟩 BPS (Business Process Services)

**Skills:**

* Communication
* Business processes
* Domain knowledge
* Coordination

---

#### 🟨 Cloud & Security

**Skills:**

* Cloud platforms
* Networking
* Cybersecurity
* DevOps

---

### 🧩 Implementation

```python
PRACTICE_SKILL_MAP = {
    "Application Services": [
        "java", "python", "programming", "testing",
        "backend", "frontend", "architecture"
    ],
    "BPS": [
        "communication", "business", "process",
        "domain", "coordination"
    ],
    "Cloud & Security": [
        "cloud", "networking", "security",
        "devops", "infrastructure"
    ]
}
```

---

## 🧱 High-Level Architecture (UPDATED)

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
        ┌─────────────────┼──────────────────┐
        ▼                 ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌────────────────────┐
│ User Service │  │ Completion   │  │ Course Service     │
│ (Pandas)     │  │ Service      │  │ + ChromaDB         │
└──────────────┘  └──────────────┘  └────────────────────┘
        │
        ▼
┌────────────────────────────┐
│ Practice → Skill Mapper 🔥 │
└────────────┬───────────────┘
             ▼
      ┌───────────────────────┐
      │ Learning Plan Engine  │
      │ - Filter completed    │
      │ - Resolve prereq      │
      │ - Optimize hours      │
      └────────────┬──────────┘
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
│   ├── raw/
│   ├── processed/
│   └── chroma/
│
├── src/
│   ├── ingestion/
│   ├── services/
│   ├── planning/
│   ├── llm/
│   ├── api/
│   └── utils/
│
├── app/
├── tests/
└── README.md
```

---

## 📊 Data Sources

### 1. User Master

* Portal ID
* Grade
* Training Goal (hours/year)
* emp_practise

---

### 2. Completion Data

* Portal ID
* Course ID
* Completion Status

---

### 3. Course Master

* Course ID
* Course Name
* Summary (unstructured)

---

## 🔄 End-to-End Flow (UPDATED)

### Step 1: Input

```
Portal ID + Target Expertise (optional)
```

---

### Step 2: Fetch User

* grade
* training goal
* **emp_practise**

---

### Step 3: Map Practice → Skills 🔥

Example:

```
Application Services → Java, Testing, Backend
```

---

### Step 4: Retrieve Relevant Courses

#### Using:

* Practice-based skills
* Target expertise
* ChromaDB semantic search

---

### Step 5: Fetch Completed Courses

```
Completion Status = completed
```

---

### Step 6: Filter Courses

Remove:

* completed courses
* irrelevant courses

---

### Step 7: Extract Metadata

From summary:

* prerequisites
* duration

---

### Step 8: Sequence Courses

```
Prerequisite → Main Course
```

---

### Step 9: Optimize by Training Hours

* fill plan until goal reached

---

### Step 10: Generate Output

---

## 🧠 Core Components

### Practice Mapper (NEW)

* Converts practice → skills
* Drives recommendation logic

---

### Learning Plan Engine

* filtering
* sequencing
* hour optimization

---

### ChromaDB

* semantic retrieval for course summaries

---

## ⚙️ Implementation Steps

### Phase 1–3

(same as before)

---

### Phase 4 (UPDATED)

Add:

* practice_skill_mapper

---

### Phase 5 (UPDATED)

Enhance logic:

* skill-based filtering

---

## 📊 Sample Output

```json
{
  "portal_id": 24463,
  "practice": "Application Services",
  "skills": ["java", "backend", "testing"],
  "recommended_courses": [
    {
      "course_name": "Java Threads",
      "reason": "Matches Java backend skill"
    }
  ]
}
```

---

## 🚀 Optional Enhancements

* LLM skill extraction
* semantic prerequisite parsing
* conversational assistant

---

## ⚠️ Design Considerations

* Do NOT use L1–L6
* Practice mapping is critical
* summary parsing is noisy
* combine rule + semantic

---

## 🎯 Final Positioning (UPDATED)

> Built an intelligent learning path assistant leveraging practice-based skill mapping, course metadata, and completion history to generate personalized, prerequisite-aware, and training-goal-aligned learning plans.

---

## 🔥 Key Takeaway

👉 Practice → Skill mapping is the **core intelligence layer**

Without it:

* generic output

With it:

* personalized, domain-aware system

---
