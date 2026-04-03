# AI Learning Path Assistant

## 📌 Overview

This project builds an **intelligent learning path generation system** that creates personalized course plans for employees based on:

* Employee profile (grade, practice, training goal)
* Completed courses
* Course metadata (summary, prerequisites, duration)
* Target expertise (e.g., Java, Data Engineering)
* **Practice → Skill mapping**

The system combines:

* **Rule-based planning (deterministic core)**
* **Semantic search (ChromaDB)**
* **Practice-aware recommendation engine**
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

## 🧠 Practice → Skill Mapping (CORE INTELLIGENCE LAYER)

### 📌 Why this is needed

The `user_master` table contains:

* `emp_practise`

But it does NOT directly define:

* primary technical or functional skills
* course recommendations

This layer bridges that gap by mapping employee practice to skill themes and then to relevant courses.

---

### 🔷 Practice Mapping

#### 🟦 1. Application Services

**Primary Skills:**

* Programming & Development
* Testing & QA
* Software Architecture
* UI / Frontend / Backend

**Relevant Technologies / Skills:**

* Java, .NET, Python, PHP
* Spring, Hibernate, ASP.NET
* Design Patterns, OOP
* Selenium, QTP
* HTML5, Angular, Node.js

**Example Course Mapping:**

* Java Threads
* Spring MVC Module
* Selenium - Multiple modules
* Introduction to Selenium Basics

---

#### 🟩 2. BPS (Business Process Services)

**Primary Skills:**

* Business Communication
* Process & Operations
* Domain Knowledge
* Project Coordination

**Relevant Topics:**

* Business English
* Communication Workshop
* Banking Basics
* Process / Quality

**Example Course Mapping:**

* Business English
* Communication Workshop
* Banking Basics
* BPS_Process Training - Project

---

#### 🟨 3. Cloud & Security

**Primary Skills:**

* Cloud Platforms
* Infrastructure & Networking
* Cybersecurity
* DevOps / Automation

**Relevant Topics:**

* ITIL
* Security Policies
* Cisco Networking
* DevOps

**Example Course Mapping:**

* Information Security Management system
* Cisco Firewall
* ITIL Concepts
* Cloud Security Awareness Training

---

#### 🟪 4. Global Support

**Primary Skills:**

* IT Service Desk / Support Operations
* Incident, Problem, Change, and Request Management
* Customer / Client Communication
* Service Management Tools
* Security & Compliance Awareness
* Support Process Governance

**Relevant Topics:**

* Service Desk fundamentals and intermediate support
* Incident and problem management
* ServiceNow / service management platforms
* Customer service and complaint handling
* Information security, GDPR, and compliance
* Support operations for infrastructure / production environments

**Best-Suited Course Examples from Current Course List:**

* IT Service Desk Fundamental (Grade 4)
* IT Service Desk Fundamental (Grade 5)
* IT Service Desk Intermediate (Grade 6)
* Service Desk - Future Training Force Certification
* ServiceNow Fundamentals
* Servicenow- Incident Handling
* IT Service Management Incident vs Service Request - NanoLearning
* IT Service Management Major Incident Priority Downgrade Policy
* SOM Intro and Incident Management (Distance Learning)
* SOM Problem Management (Distance Learning)
* SOM Change Management (Distance Learning)
* SOM Service Request Management (Distance Learning)
* Information Security Management System Training (DS)
* Information Security for Work and Home
* GDPR General Data Protection Regulation
* Cloud Security Awareness Training
* The Fundamentals of Exceptional Customer Service
* The Customer's Voice
* Workshop - Handling Client Complaints
* Communicating with client

---

### 🧩 Implementation

```python
PRACTICE_SKILL_MAP = {
    "Application Services": [
        "java", "python", ".net", "programming", "testing",
        "backend", "frontend", "architecture", "design patterns",
        "spring", "hibernate", "selenium", "node.js", "html5"
    ],
    "BPS": [
        "communication", "business", "process", "domain",
        "coordination", "banking", "healthcare", "insurance",
        "writing", "etiquette", "customer service"
    ],
    "Cloud & Security": [
        "cloud", "networking", "security", "devops",
        "infrastructure", "firewall", "gdpr", "itil",
        "compliance", "cybersecurity"
    ],
    "Global Support": [
        "service desk", "incident management", "problem management",
        "change management", "service request", "servicenow",
        "it service management", "customer service", "client communication",
        "support operations", "security awareness", "gdpr", "compliance"
    ]
}
```

---

## 🧱 High-Level Architecture

```text
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
│ Practice → Skill Mapper    │
└────────────┬───────────────┘
             ▼
      ┌───────────────────────┐
      │ Learning Plan Engine  │
      │ - Filter completed    │
      │ - Resolve prereq      │
      │ - Optimize hours      │
      │ - Rank by practice fit│
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

```text
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

### 2. Completion Data

* Portal ID
* Course ID
* Completion Status

### 3. Course Master

* Course ID
* Course Name
* Summary (unstructured)

---

## 🔄 End-to-End Flow

### Step 1: Input

```text
Portal ID + Target Expertise (optional)
```

### Step 2: Fetch User

Extract:

* grade
* training goal
* emp_practise

### Step 3: Map Practice → Skills

Example:

```text
Global Support → service desk, incident management, ServiceNow, customer service, security awareness
```

### Step 4: Retrieve Relevant Courses

Use:

* practice-based skill keywords
* optional target expertise
* ChromaDB semantic search over course names and summaries

### Step 5: Fetch Completed Courses

```text
Completion Status = completed
```

### Step 6: Filter Courses

Remove:

* completed courses
* low-relevance courses
* courses not suitable for grade, if grade rules are available

### Step 7: Extract Metadata

From summary:

* prerequisites
* intended audience
* duration

### Step 8: Sequence Courses

```text
Prerequisite → Main Course
```

### Step 9: Optimize by Training Hours

* fill plan until annual target hours are met or closely matched

### Step 10: Generate Output

Return:

* recommended courses
* durations
* total planned hours
* remaining gap
* rationale

---

## 🧠 Core Components

### Practice Mapper

* Converts practice → skills
* Drives recommendation logic
* Supports Application Services, BPS, Cloud & Security, and Global Support

### Learning Plan Engine

* filtering
* sequencing
* hour optimization
* relevance ranking by practice fit

### ChromaDB

* semantic retrieval for course summaries and titles

---

## ⚙️ Implementation Steps

### Phase 1: Setup

* Create repo structure
* Install dependencies

### Phase 2: Data Ingestion

* Load Excel into DataFrames
* Clean missing values
* Store processed CSVs

### Phase 3: Build ChromaDB

* Convert course rows into documents
* Embed summaries
* Store in Chroma

### Phase 4: Backend Services

Implement:

* `user_service`
* `completion_service`
* `course_service`
* `practice_skill_mapper`
* `planning_engine`

### Phase 5: Learning Plan Logic

Implement:

* completed course filtering
* practice-based skill filtering
* prerequisite ordering
* duration calculation
* hour optimization

### Phase 6: API Layer

* Create FastAPI endpoints
* Integrate services

### Phase 7: UI

* Build Streamlit interface
* Connect to backend API

### Phase 8: LLM Integration (Optional)

* explanation generation
* skill gap summary
* reasoning for recommended courses

---

## 📊 Sample Output

```json
{
  "portal_id": 24463,
  "practice": "Global Support",
  "skills": [
    "service desk",
    "incident management",
    "servicenow",
    "customer service",
    "security awareness"
  ],
  "recommended_courses": [
    {
      "course_name": "IT Service Desk Fundamental (Grade 4)",
      "reason": "Strong match for foundational support operations"
    },
    {
      "course_name": "ServiceNow Fundamentals",
      "reason": "Supports service management platform skills"
    },
    {
      "course_name": "SOM Intro and Incident Management (Distance Learning)",
      "reason": "Relevant for incident handling workflows"
    }
  ]
}
```

---

## 🚀 Optional Enhancements

* LLM-based prerequisite extraction
* LLM-based skill extraction from course summaries
* conversational assistant
* recommendation scoring
* feedback-based ranking

---

## ⚠️ Design Considerations

* Do NOT use L1–L6 for learning logic
* Practice mapping is critical
* Combine keyword matching with semantic retrieval
* Handle missing duration gracefully
* Keep core recommendation logic deterministic

---

## 🎯 Final Positioning

> Built an intelligent learning path assistant leveraging practice-based skill mapping, course metadata, and completion history to generate personalized, prerequisite-aware, and training-goal-aligned learning plans.

---

## ✅ Success Criteria

* Correct filtering of completed courses
* Relevant recommendations based on practice
* Logical sequencing of prerequisites
* Training goal alignment
* Clean API + UI integration
* Optional AI explanation layer

---
