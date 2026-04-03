
# AI Learning Path Assistant

## 1. Purpose

AI Learning Path Assistant is a hybrid recommendation system that generates personalized learning plans for employees using:

- structured employee data from the user master table
- course completion history from the completion table
- unstructured course metadata from the course master table
- practice-to-skill mapping
- lightweight semantic retrieval using ChromaDB
- optional LLM-based explanation and metadata extraction
- RAG evaluation using RAGAS for the retrieval/explanation layer

This project is designed for the capstone use case where the system must generate a learning plan for an employee based on their profile, annual training target, completed courses, and role context.

This is **not** a full chatbot system and **not** a pure RAG application.

It is a **hybrid planning system** where:

- deterministic business logic is the backbone
- semantic retrieval is a supporting layer
- optional LLM reasoning improves explainability and extraction
- evaluation covers both business logic quality and RAG quality separately

---

## 2. Business Problem

Employees have:

- a profile in the user master table
- a set of completed courses
- an annual training goal in hours
- a practice such as Application Services, BPS, Cloud & Security, or Global Support

The raw data has these limitations:

- `emp_practise` does not directly specify the employee’s primary skills
- course summaries are partly unstructured
- prerequisite and duration information may be hidden inside summary text
- employees should not be recommended courses already completed
- recommendations should align with annual training target hours
- recommendations should align with the employee’s practice and optional target expertise

The project solves this by generating a personalized, relevant, prerequisite-aware learning plan with hour tracking and optional natural-language explanation.

---

## 3. Core Objectives

The system must:

1. Accept an employee identifier (`Portal ID`)
2. Read employee metadata from the user master table
3. Read completed courses from the completion table
4. Retrieve relevant courses from the course master table
5. Use practice-to-skill mapping to improve relevance
6. Remove already completed courses
7. Resolve prerequisite order where possible
8. Estimate and accumulate course duration
9. Align recommendations with the employee’s training goal
10. Return a final learning plan with reasons
11. Evaluate the RAG layer with RAGAS
12. Evaluate the deterministic planner with business metrics

---

## 4. Data Sources and Correct Interpretation

### 4.1 User Master Table

Important fields:

- `Portal ID` → unique employee identifier
- `grade` → employee grade
- `Training Goal` → annual target learning hours
- `emp_practise` → employee business practice
- `employee_type`, `country`, and other fields can be used if needed

Important clarifications:

- `Training Goal` means the number of hours the employee is expected to complete in a year
- `L1` to `L6` are organizational hierarchy fields, not learning-path levels
- `emp_practise` is useful context, but it does not directly define exact skills or direct course mappings

### 4.2 Completion Data Table

Important fields:

- `Course ID`
- `Portal ID`
- `Enrolment Date`
- `Completion Status`
- `Completed Date`

Important business rule:

A course is considered completed only if:

```text
Completion Status = completed
```

This table is used to:

- identify completed courses
- exclude completed courses from recommendation
- optionally calculate completed hours if course duration is available

### 4.3 Course Master Table

Important fields:

- `Course ID`
- `Course Full Name`
- `summary`

The `summary` may contain:

- prerequisite information
- intended audience
- grade or suitability hints
- duration
- learning objectives
- topic or technology keywords

This table is the main source for:

- course relevance
- semantic retrieval
- prerequisite extraction
- duration extraction
- suitability hints

---

## 5. Project Type and Technical Positioning

This project is best described as a:

- personalized learning path recommendation system
- rule-based planning engine
- lightweight RAG-assisted retrieval system
- optional GenAI explanation and extraction layer

### Deterministic Core

Used for:

- employee lookup
- completion filtering
- practice mapping
- ranking
- prerequisite ordering
- hour optimization
- plan assembly

### Lightweight RAG Layer

Used for:

- semantic search over course names and summaries
- retrieving best-fit courses for a practice or target expertise
- grounding LLM explanations
- helping extract prerequisite, duration, and audience details from summary text

### Optional LLM Layer

Used for:

- explanation generation
- skill-gap summary
- metadata extraction from messy summaries
- rationale generation for recommended courses

---

## 6. Practice-to-Skill Mapping Layer

### 6.1 Why It Is Required

The `user_master` table contains `emp_practise`, but it does not directly tell:

- the primary skills for the employee
- which courses should be considered relevant

So the system introduces a knowledge layer:

```text
Practice → Skill Themes → Relevant Course Families
```

This becomes the core recommendation context.

### 6.2 Practice Mapping

#### A. Application Services

Primary skill themes:

- programming and development
- backend engineering
- frontend engineering
- software architecture
- testing and QA

Typical technologies and keywords:

- java
- python
- .net
- php
- spring
- hibernate
- asp.net
- design patterns
- oop
- selenium
- qtp
- angular
- node.js
- html5

Example course fit:

- Java Threads
- JAXP
- Effective Java - General Coding Practices
- Selenium-related courses
- backend/frontend/application architecture courses

#### B. BPS (Business Process Services)

Primary skill themes:

- communication
- process and operations
- business and domain understanding
- project coordination
- quality and documentation

Typical keywords:

- communication
- process
- banking
- healthcare
- insurance
- quality
- customer service
- writing
- etiquette

Example course fit:

- business english
- communication workshop
- banking basics
- BPS process and quality courses

#### C. Cloud & Security

Primary skill themes:

- cloud platforms
- networking and infrastructure
- cybersecurity
- devops and automation
- compliance and governance

Typical keywords:

- cloud
- networking
- security
- firewall
- gdpr
- itil
- devops
- infrastructure
- cybersecurity
- compliance

Example course fit:

- Information Security Management System Training
- Cloud Security Awareness Training
- GDPR-related courses
- Cisco/infrastructure/networking courses
- AWS/Azure/cloud engineering courses

#### D. Global Support

Primary skill themes:

- service desk and support operations
- incident management
- problem management
- change management
- service request handling
- customer and client communication
- service management tooling
- security and compliance awareness

Typical keywords:

- service desk
- incident management
- problem management
- change management
- service request
- servicenow
- itil
- support operations
- customer service
- client communication
- gdpr
- compliance
- security awareness

Best-suited example courses from the uploaded course list include:

- IT Service Desk Fundamental (Grade 4)
- IT Service Desk Fundamental (Grade 5)
- IT Service Desk Intermediate (Grade 6)
- Service Desk - Future Training Force Certification
- ServiceNow Fundamentals
- Servicenow- Incident Handling
- IT Service Management Incident vs Service Request - NanoLearning
- IT Service Management Major Incident Priority Downgrade Policy
- SOM Intro and Incident Management (Distance Learning)
- SOM Problem Management (Distance Learning)
- SOM Change Management (Distance Learning)
- SOM Service Request Management (Distance Learning)
- SOM Knowledge Management E-Learning
- Information Security Management System Training (DS)
- Information Security for Work and Home
- GDPR General Data Protection Regulation
- Security and Compliance
- Tenet Help Desk Training
- Linux Production Support
- MT Production Support
- SitMan and CritSit Procedures
- Service Desk Skill Enhancement Certifications - Level 1
- Windows, Printers, Shares
- Office 365

### 6.3 Practice Mapping Configuration

Store mapping in a config file, preferably:

```text
config/practice_skill_map.yaml
```

Example:

```yaml
Application Services:
  skills:
    - java
    - python
    - programming
    - backend
    - frontend
    - testing
    - architecture
    - spring
    - selenium

BPS:
  skills:
    - communication
    - process
    - business
    - domain
    - quality
    - customer service

Cloud & Security:
  skills:
    - cloud
    - networking
    - security
    - devops
    - infrastructure
    - gdpr
    - compliance
    - itil

Global Support:
  skills:
    - service desk
    - incident management
    - problem management
    - change management
    - service request
    - servicenow
    - itil
    - customer service
    - client communication
    - support operations
    - gdpr
    - compliance
    - security awareness
```

---

## 7. Solution Architecture

### 7.1 High-Level Architecture

```text
                ┌────────────────────────────┐
                │       Streamlit UI         │
                │   User-facing frontend     │
                └─────────────┬──────────────┘
                              │ HTTP
                              ▼
                ┌────────────────────────────┐
                │       FastAPI Backend      │
                │     Core Orchestrator      │
                └─────────────┬──────────────┘
                              │
      ┌───────────────────────┼────────────────────────┐
      ▼                       ▼                        ▼
┌───────────────┐      ┌───────────────┐      ┌────────────────────┐
│ User Service  │      │ Completion    │      │ Course Service     │
│ (Pandas)      │      │ Service       │      │ (Pandas + Chroma)  │
└──────┬────────┘      └──────┬────────┘      └──────────┬─────────┘
       │                      │                          │
       └──────────────┬───────┴───────────────┬──────────┘
                      ▼                       ▼
            ┌──────────────────────┐   ┌──────────────────────┐
            │ Practice Skill Mapper│   │ Summary Parser       │
            │ Context Layer        │   │ Duration / Prereq    │
            └────────────┬─────────┘   └────────────┬─────────┘
                         └──────────────┬───────────┘
                                        ▼
                          ┌──────────────────────────┐
                          │ Learning Plan Engine     │
                          │ - relevance ranking      │
                          │ - completion filtering   │
                          │ - prerequisite ordering  │
                          │ - hour optimization      │
                          └────────────┬─────────────┘
                                       ▼
                        ┌──────────────────────────────┐
                        │ Optional LLM Explanation     │
                        │ and/or Field Extraction      │
                        └────────────┬─────────────────┘
                                     ▼
                          ┌──────────────────────────┐
                          │ Final Response Payload   │
                          └──────────────────────────┘
```

### 7.2 Architecture Principles

1. Deterministic planning first
2. RAG as support, not backbone
3. UI and backend separated
4. Practice mapping config-driven
5. Explainability included
6. Evaluation included for both rule engine and RAG

---

## 8. Project Structure

```text
ai-learning-path-assistant/
│
├── app/
│   └── streamlit_app.py
│
├── config/
│   ├── practice_skill_map.yaml
│   ├── retrieval_config.yaml
│   └── parser_config.yaml
│
├── data/
│   ├── raw/
│   │   ├── user_master.xlsx
│   │   ├── completion_data.xlsx
│   │   └── course_master.xlsx
│   │
│   ├── processed/
│   │   ├── user_master.csv
│   │   ├── completion_data.csv
│   │   ├── course_master.csv
│   │   └── course_master_enriched.csv
│   │
│   └── chroma/
│       └── learning_catalog_db/
│
├── src/
│   ├── api/
│   │   ├── main.py
│   │   ├── routes.py
│   │   └── schemas.py
│   │
│   ├── ingestion/
│   │   ├── load_excel.py
│   │   ├── preprocess_data.py
│   │   ├── build_chroma.py
│   │   └── enrich_course_master.py
│   │
│   ├── services/
│   │   ├── user_service.py
│   │   ├── completion_service.py
│   │   ├── course_service.py
│   │   ├── retrieval_service.py
│   │   ├── practice_mapper.py
│   │   └── explanation_service.py
│   │
│   ├── planning/
│   │   ├── ranking_engine.py
│   │   ├── prerequisite_resolver.py
│   │   ├── duration_estimator.py
│   │   ├── hour_optimizer.py
│   │   └── plan_builder.py
│   │
│   ├── llm/
│   │   ├── prompts.py
│   │   ├── llm_client.py
│   │   └── metadata_extractor.py
│   │
│   ├── evaluation/
│   │   ├── evaluate_rule_engine.py
│   │   ├── evaluate_rag.py
│   │   ├── ragas_runner.py
│   │   └── datasets/
│   │
│   └── utils/
│       ├── logging_utils.py
│       ├── text_utils.py
│       ├── file_utils.py
│       └── constants.py
│
├── tests/
│   ├── test_user_service.py
│   ├── test_completion_service.py
│   ├── test_practice_mapper.py
│   ├── test_retrieval_service.py
│   ├── test_duration_estimator.py
│   ├── test_prerequisite_resolver.py
│   └── test_plan_builder.py
│
├── notebooks/
│   └── eda.ipynb
│
├── requirements.txt
├── README.md
└── .env.example
```

---

## 9. End-to-End Functional Flow

### Step 1. User submits request

Input fields:

- `portal_id`
- optional `target_expertise`
- optional `top_k`
- optional `include_explanation`

Example:

```json
{
  "portal_id": 24463,
  "target_expertise": "Java",
  "include_explanation": true,
  "top_k": 15
}
```

### Step 2. Fetch employee profile

From user master:

- portal id
- grade
- training goal
- emp_practise

Validation:

- portal id exists
- training goal numeric where possible
- emp_practise normalized

### Step 3. Build employee context

Context assembled from:

- practice
- optional target expertise
- grade
- possibly employee type and country if needed later

### Step 4. Map practice to skill themes

Example:

```text
Global Support
→ service desk
→ incident management
→ servicenow
→ support operations
→ customer service
→ compliance
```

If target expertise is present, merge it with practice keywords.

### Step 5. Retrieve candidate courses

Use hybrid retrieval:

#### A. Rule-based retrieval
- title keyword match
- summary keyword match
- exact phrase match against practice skills

#### B. Semantic retrieval using ChromaDB
Example query:

```text
Global Support service desk incident management servicenow support operations
```

Retrieve top-k candidate courses.

#### C. Merge and deduplicate
Combine keyword and semantic results.

### Step 6. Fetch completed courses

From completion data, filter:

```text
Portal ID = given employee
Completion Status = completed
```

### Step 7. Parse course metadata

Extract from summary if possible:

- duration
- prerequisite text
- intended audience
- grade suitability
- topic hints

Use regex parser first.  
Use optional LLM extraction if parsing confidence is low.

Persist enriched data in:

```text
data/processed/course_master_enriched.csv
```

### Step 8. Filter candidate courses

Remove:

- completed courses
- duplicates
- invalid records
- low relevance entries
- grade-incompatible courses if reliable grade rules exist

### Step 9. Score and rank candidates

Suggested weighted score:

```text
final_score =
    0.35 * practice_match_score +
    0.25 * semantic_similarity_score +
    0.15 * expertise_match_score +
    0.10 * grade_fit_score +
    0.10 * prerequisite_readiness_score +
    0.05 * support_bonus_score
```

### Step 10. Resolve prerequisites

If a prerequisite is found:

- try to map prerequisite text to an existing course
- if mapped and not completed, insert it before the dependent course
- if not mapped, keep it as advisory note

### Step 11. Optimize against annual target hours

Compute:

- annual target hours
- completed hours if known
- remaining target hours
- planned hours

Selection rules:

- prioritize highest-ranked relevant courses
- maintain prerequisite order
- stop when target is met or closely approached
- avoid excessive overshoot unless explicitly allowed

### Step 12. Generate explanation

Optional LLM explanation should state:

- why the course was recommended
- how it aligns with practice or expertise
- whether it supports prerequisite progression
- how it contributes to target hours

### Step 13. Return final response

Include:

- employee context
- completed courses
- recommended courses
- duration totals
- remaining gap
- rationale
- warnings if parsing or duration is uncertain

---

## 10. Recommendation Logic Details

### 10.1 Recommendation Priority

1. completed-course exclusion
2. practice relevance
3. target expertise relevance
4. prerequisite correctness
5. hour alignment
6. grade suitability
7. explanation quality

### 10.2 Handling Optional Target Expertise

If target expertise is supplied:

- it should boost relevant courses
- it should not fully override practice unless required by business rule

Examples:

- Application Services + Java
- Global Support + ServiceNow
- Cloud & Security + AWS
- BPS + Communication

### 10.3 Practice-Specific Preference Rules

#### Application Services
Prefer development, testing, architecture, frontend/backend.

#### BPS
Prefer communication, process, business/domain, quality.

#### Cloud & Security
Prefer cloud, network, security, compliance, devops.

#### Global Support
Prefer service desk, incident handling, ServiceNow, support operations, customer service, compliance.

---

## 11. Lightweight RAG Design

### 11.1 Why RAG Is Used

Course summaries are unstructured. Keyword-only retrieval may miss good matches.  
So lightweight RAG is used for:

- semantic course retrieval
- explanation grounding
- supporting metadata extraction

### 11.2 What RAG Does Not Do

RAG does not decide:

- which completed courses to exclude
- final hour optimization
- deterministic prerequisite ordering on its own

Those remain rule-based.

### 11.3 ChromaDB Design

Use a persistent Chroma collection such as:

- `course_master_collection`

Suggested document:

```text
Course ID: 118
Course Full Name: Java Threads
Summary: A thread is a single sequential flow...
Parsed Topics: java, threads, multitasking
Parsed Audience: grade 5 and above
Parsed Prerequisite: Java Application Deployment
Parsed Duration Hours: 2
```

Suggested metadata:

```json
{
  "course_id": "118",
  "course_name": "Java Threads",
  "topics": ["java", "threads", "backend"],
  "source": "course_master"
}
```

### 11.4 Retrieval Flow

1. build query from practice skills + target expertise
2. query Chroma
3. fetch top-k semantic matches
4. merge with keyword matches
5. deduplicate and score

---

## 12. RAGAS and Evaluation Plan

### 12.1 Evaluation Tracks

There are two evaluation tracks:

1. rule-engine metrics
2. RAG metrics using RAGAS

### 12.2 Rule-Engine Metrics

#### A. Completed Course Exclusion Accuracy
Whether completed courses are correctly excluded.

#### B. Prerequisite Ordering Accuracy
Whether prerequisite courses appear before dependent courses.

#### C. Training Goal Coverage

```text
planned_hours / target_hours
```

#### D. Practice Relevance Score
Whether final recommendations align with mapped practice skills.

#### E. Recommendation Precision
Relevant recommendations divided by total recommendations.

#### F. Duplicate Recommendation Rate
How often duplicates or near-duplicates appear.

### 12.3 RAGAS Metrics

Use RAGAS for the retrieval/explanation layer only.

#### A. Faithfulness
Whether generated explanation is grounded in retrieved course context.

#### B. Answer Relevancy
Whether the answer/explanation addresses the query.

#### C. Context Precision
Whether retrieved context is relevant.

#### D. Context Recall
Whether the retrieval captured enough useful context.

### 12.4 Example RAG Evaluation Queries

- What courses are most relevant for Global Support?
- Why was ServiceNow Fundamentals recommended?
- What is the prerequisite for Java Threads?
- Which courses are suitable for Application Services and Java?

Example evaluation record:

```json
{
  "question": "What courses are relevant for Global Support?",
  "ground_truth": "Service desk, incident management, ServiceNow, compliance, and support operations courses are relevant.",
  "contexts": [
    "IT Service Desk Fundamental...",
    "ServiceNow Fundamentals...",
    "SOM Intro and Incident Management..."
  ],
  "answer": "Recommended courses include IT Service Desk Fundamental and ServiceNow Fundamentals because they align with service desk operations, incident handling, and support workflows."
}
```

### 12.5 Retrieval Strategy Comparison

Compare:

- keyword-only retrieval
- semantic retrieval only
- hybrid retrieval
- hybrid retrieval plus practice mapping

---

## 13. Detailed Module Responsibilities

### 13.1 user_service.py

Responsibilities:

- load user master
- fetch employee by portal id
- normalize practice
- validate training goal

### 13.2 completion_service.py

Responsibilities:

- load completion table
- fetch completed courses by portal id
- return course ids and statuses

### 13.3 course_service.py

Responsibilities:

- load course master
- fetch course by id
- search by title or keywords
- load enriched course fields

### 13.4 practice_mapper.py

Responsibilities:

- load practice mapping config
- return skill list for a practice
- handle aliases and normalization

### 13.5 retrieval_service.py

Responsibilities:

- construct retrieval query
- query ChromaDB
- combine keyword and semantic matches
- deduplicate candidates

### 13.6 duration_estimator.py

Responsibilities:

- parse duration from summary text
- estimate fallback if missing

Suggested regex patterns:

- `(\d+)\s*hours?`
- `duration\s*[:\-]?\s*(\d+)`
- `(\d+)\s*hr`

### 13.7 prerequisite_resolver.py

Responsibilities:

- parse prerequisite text
- map text to course candidates where possible
- build prerequisite ordering

### 13.8 ranking_engine.py

Responsibilities:

- compute relevance score
- combine practice, expertise, semantic similarity, grade, readiness

### 13.9 hour_optimizer.py

Responsibilities:

- pick best ordered recommendations
- align with target hours
- manage overshoot logic

### 13.10 plan_builder.py

Responsibilities:

- assemble final response
- attach reasons and notes
- format plan output

### 13.11 explanation_service.py

Responsibilities:

- call optional LLM
- create concise grounded explanation
- avoid unsupported claims

---

## 14. API Design

### 14.1 Health Endpoint

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### 14.2 Generate Plan Endpoint

```http
POST /generate-plan
```

Request example:

```json
{
  "portal_id": 24463,
  "target_expertise": "Java",
  "include_explanation": true,
  "top_k": 15
}
```

Response example:

```json
{
  "portal_id": 24463,
  "employee_name": "Shefali Joisa",
  "grade": 13,
  "practice": "Application Services",
  "target_expertise": "Java",
  "annual_training_goal_hours": 16,
  "completed_course_ids": [118],
  "completed_hours": 2,
  "remaining_target_hours": 14,
  "skills_used_for_retrieval": [
    "java",
    "backend",
    "programming",
    "testing"
  ],
  "recommended_courses": [
    {
      "course_id": 119,
      "course_name": "JAXP",
      "hours": 3,
      "prerequisite": "Knowledge of Java Application Deployment",
      "reason": "Matches Java skill theme and is relevant for application development."
    },
    {
      "course_id": 120,
      "course_name": "Effective Java - General Coding Practices",
      "hours": 4,
      "prerequisite": null,
      "reason": "Improves coding practices for Java developers."
    }
  ],
  "planned_hours": 7,
  "remaining_gap_after_plan": 7,
  "explanation": "These recommendations align with Application Services and focus on Java development fundamentals and coding quality."
}
```

---

## 15. Streamlit UI Requirements

The UI should support:

- input field for Portal ID
- optional input for Target Expertise
- checkbox for Include Explanation
- button to Generate Plan

The UI should display:

- employee metadata
- training goal
- completed courses
- recommended courses
- hours per course
- total planned hours
- remaining gap
- optional explanation

Optional advanced UI:

- show retrieved candidate courses
- show filtered-out completed courses
- show ranking explanation
- show notes for unknown duration or unmapped prerequisites

---

## 16. Ingestion and Data Preparation Pipeline

### Step 1. Load Excel Files

Read:

- user master
- completion data
- course master

### Step 2. Clean Columns

- trim whitespace
- standardize column names
- normalize practice values
- preserve raw summary
- create lowercase summary copy for keyword processing

### Step 3. Persist Processed CSVs

Save cleaned datasets in:

```text
data/processed/
```

### Step 4. Enrich Course Master

Add parsed columns such as:

- `parsed_topics`
- `parsed_duration_hours`
- `parsed_prerequisite_text`
- `parsed_grade_hint`
- `parsed_audience_text`

### Step 5. Build ChromaDB

Convert each course to a retrieval document and persist in:

```text
data/chroma/learning_catalog_db/
```

---

## 17. Build Roadmap

### Phase 1. Repo and Config Setup

- create directory structure
- create requirements file
- create config YAML files
- create `.env.example`

### Phase 2. Data Ingestion

- load excel
- preprocess and clean
- export processed CSVs
- enrich course master

### Phase 3. Retrieval Layer

- build Chroma collection
- implement keyword retrieval
- implement semantic retrieval
- merge into hybrid retrieval

### Phase 4. Core Services

- user service
- completion service
- course service
- practice mapper

### Phase 5. Planning Engine

- scoring/ranking
- prerequisite resolution
- duration parsing
- hour optimization
- plan assembly

### Phase 6. API Layer

- create FastAPI app
- define schemas
- add routes
- health endpoint
- generate-plan endpoint

### Phase 7. UI Layer

- build Streamlit form
- connect to API
- render plan and explanation

### Phase 8. Optional LLM Layer

- explanation prompt
- metadata extraction prompt
- JSON output enforcement
- fallback to deterministic parser

### Phase 9. Evaluation

- business metrics runner
- RAGAS runner
- retrieval strategy comparison

### Phase 10. Packaging

- finalize README
- add screenshots
- add examples
- add tests
- prepare demo scenarios

---

## 18. LLM Prompt Guidance

### 18.1 Explanation Prompt

Use retrieved course text and employee context to explain:

- why the course was recommended
- how it aligns with the employee’s practice or target expertise
- what capability it builds

Rules:

- stay grounded in provided course text
- do not invent prerequisite information
- do not invent duration if absent
- use concise reasoning

### 18.2 Metadata Extraction Prompt

When parsing is uncertain, ask the LLM to extract:

- prerequisite
- duration
- intended audience
- grade suitability hints

Rules:

- return JSON only
- use `null` when not found
- do not guess

Suggested output:

```json
{
  "duration_hours": null,
  "prerequisite": "Knowledge of Java Application Deployment",
  "audience": "Developers of Grade 5 and above",
  "grade_hint": "5+"
}
```

---

## 19. Error Handling and Fallbacks

### A. Missing Portal ID
Return business error:
- employee not found

### B. Missing Practice
Fallback:
- use target expertise if provided
- otherwise use generic retrieval

### C. Missing Duration
Fallback:
- estimate conservative duration
- or mark duration as unknown

### D. Unmapped Prerequisite
Fallback:
- keep prerequisite as advisory note

### E. No Relevant Courses Found
Fallback:
- return empty plan
- include reason
- suggest broader expertise filter

### F. Poor Summary Format
Fallback:
- rely more on title keywords
- use semantic retrieval
- skip unreliable fields

---

## 20. Testing Strategy

### Unit Tests

Test:

- practice mapping
- completion filtering
- duration parsing
- prerequisite parsing
- ranking logic
- hour optimization

### Integration Tests

Test:

- API end-to-end
- Chroma retrieval integration
- enrichment pipeline
- explanation integration

### Demo Scenarios

- Application Services + Java
- Global Support without target expertise
- Global Support + ServiceNow
- Cloud & Security + AWS
- BPS + communication
- employee with many completed courses
- employee with zero completed courses

---

## 21. Success Criteria

The project is successful if it can:

1. correctly fetch employee context
2. exclude completed courses
3. recommend practice-relevant courses
4. preserve prerequisite order where known
5. align plan with annual target hours
6. use semantic retrieval effectively for messy summaries
7. optionally explain recommendations clearly
8. report both rule-engine and RAG metrics

---

## 22. Final Positioning

AI Learning Path Assistant is a hybrid recommendation engine that combines structured employee data, practice-aware skill mapping, course completion history, semantic retrieval over course metadata, and deterministic planning logic to generate personalized, prerequisite-aware, and training-goal-aligned learning plans.

---

## 23. Future Enhancements

Possible future improvements:

- skill graph instead of simple keyword mapping
- richer course difficulty modeling
- feedback loop from employee selections
- manager approval workflow
- LMS integration
- personalized ranking based on historical completions
- dashboard for organization-level training-goal compliance
- multilingual course handling
- stronger metadata extraction using fine-tuned prompts

---

## 24. Suggested Dependencies

Example `requirements.txt` entries:

```text
pandas
openpyxl
fastapi
uvicorn
streamlit
chromadb
pydantic
python-dotenv
pyyaml
ragas
datasets
langchain
langchain-community
sentence-transformers
pytest
```

If OpenAI or Azure OpenAI is used for explanation or extraction, also include the relevant client package.

---

## 25. Suggested Environment Variables

Example `.env.example`:

```text
OPENAI_API_KEY=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_DEPLOYMENT=
CHROMA_DB_PATH=data/chroma/learning_catalog_db
LOG_LEVEL=INFO
```

---

## 26. Final Build Notes for an Agent

When using this document as a build workflow for an agent, follow this order strictly:

1. create project structure
2. implement data ingestion
3. export processed CSVs
4. enrich course metadata
5. build Chroma index
6. implement services
7. implement planning engine
8. implement FastAPI endpoint
9. implement Streamlit UI
10. add optional LLM explanation
11. add evaluation scripts
12. run demo scenarios
13. document outputs and edge cases

Important guardrails for implementation:

- do not use `L1-L6` as learning sequence
- do not let LLM override deterministic completion filtering
- do not let RAG replace the planner
- keep recommendation logic reproducible and testable
- keep practice mapping configurable, not hardcoded inside the endpoint
