# LaundroVision AI MVP Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the LaundroVision AI MVP end-to-end, featuring a FastAPI backend for POI fetching, scoring, and LLM
insights, and a progressive Streamlit frontend for field consultants.

**Architecture:**

- **Backend:** FastAPI exposes endpoints for competitor evaluation (`/evaluate-competitor`) and total score calculation
  (`/calculate-score`). A scoring service applies dynamic weights based on competitor presence.
- **Frontend:** Streamlit uses `st.session_state` to transition through 4 stages: INIT (Address input) ->
  COMPETITOR_EVAL (Knock-out check) -> TARGET_EVAL (Full survey) -> REPORT (Results & Financials).

**Tech Stack:** Python 3.11+, `uv` (package manager), FastAPI, Pydantic, Streamlit, pytest (99% coverage required).

---

### Task 1: Define API Schemas

**Files:**

- Create: `src/laundro_vision_ai/models/schemas.py`
- Create: `tests/test_schemas.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_schemas.py
import pytest
from pydantic import ValidationError
from laundro_vision_ai.models.schemas import CompetitorEvalRequest, AssessmentRequest

def test_competitor_eval_request_validation():
    req = CompetitorEvalRequest(
        q2_residential=4, q3_visibility=4, q4_signage=3,
        q5_motorcycle=5, q7_machine_status=4, q8_cleanliness=5
    )
    assert req.q2_residential == 4

    with pytest.raises(ValidationError):
        CompetitorEvalRequest(
            q2_residential=6, q3_visibility=4, q4_signage=3,
            q5_motorcycle=5, q7_machine_status=4, q8_cleanliness=5
        )

def test_assessment_request_validation():
    req = AssessmentRequest(
        has_competitor=False,
        q1_cvs=5, q2_residential=4, q3_visibility=3,
        q4_signage=4, q5_motorcycle=5
    )
    assert req.has_competitor is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_schemas.py -v` Expected: FAIL (ModuleNotFoundError: No module named
'laundro_vision_ai.models')

- [ ] **Step 3: Write minimal implementation**

```python
# src/laundro_vision_ai/models/__init__.py
# (Empty file to make it a package)

# src/laundro_vision_ai/models/schemas.py
from typing import Optional
from pydantic import BaseModel, Field

class CompetitorEvalRequest(BaseModel):
    q2_residential: int = Field(ge=1, le=5)
    q3_visibility: int = Field(ge=1, le=5)
    q4_signage: int = Field(ge=1, le=5)
    q5_motorcycle: int = Field(ge=1, le=5)
    q7_machine_status: int = Field(ge=1, le=5)
    q8_cleanliness: int = Field(ge=1, le=5)

class CompetitorEvalResponse(BaseModel):
    competitor_score: float
    knock_out: bool
    message: str

class AssessmentRequest(BaseModel):
    has_competitor: bool
    q1_cvs: int = Field(ge=1, le=5)
    q2_residential: int = Field(ge=1, le=5)
    q3_visibility: int = Field(ge=1, le=5)
    q4_signage: int = Field(ge=1, le=5)
    q5_motorcycle: int = Field(ge=1, le=5)
    q7_machine_status: Optional[int] = Field(None, ge=1, le=5)
    q8_cleanliness: Optional[int] = Field(None, ge=1, le=5)

class CategoryScores(BaseModel):
    audience: float
    hardware: float
    operations: Optional[float]

class AssessmentResponse(BaseModel):
    total_score: float
    category_scores: CategoryScores
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_schemas.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_schemas.py src/laundro_vision_ai/models/
git commit -m "feat: add pydantic schemas for api requests and responses"
```

---

### Task 2: Implement Competitor Evaluation Service

**Files:**

- Create: `src/laundro_vision_ai/services/scoring.py`
- Create: `tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scoring.py
from laundro_vision_ai.services.scoring import evaluate_competitor
from laundro_vision_ai.models.schemas import CompetitorEvalRequest

def test_evaluate_competitor_knockout():
    # Avg of (4+4+4+4+4+4) = 4.0 -> knock out (> 3.0)
    req = CompetitorEvalRequest(
        q2_residential=4, q3_visibility=4, q4_signage=4,
        q5_motorcycle=4, q7_machine_status=4, q8_cleanliness=4
    )
    res = evaluate_competitor(req)
    assert res.competitor_score == 4.0
    assert res.knock_out is True
    assert "過於強大" in res.message

def test_evaluate_competitor_pass():
    # Avg of (2+2+2+2+2+2) = 2.0 -> pass (<= 3.0)
    req = CompetitorEvalRequest(
        q2_residential=2, q3_visibility=2, q4_signage=2,
        q5_motorcycle=2, q7_machine_status=2, q8_cleanliness=2
    )
    res = evaluate_competitor(req)
    assert res.competitor_score == 2.0
    assert res.knock_out is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scoring.py -v` Expected: FAIL (ImportError)

- [ ] **Step 3: Write minimal implementation**

```python
# src/laundro_vision_ai/services/__init__.py
# (Empty file)

# src/laundro_vision_ai/services/scoring.py
from laundro_vision_ai.models.schemas import CompetitorEvalRequest, CompetitorEvalResponse

def evaluate_competitor(req: CompetitorEvalRequest) -> CompetitorEvalResponse:
    total = sum([
        req.q2_residential, req.q3_visibility, req.q4_signage,
        req.q5_motorcycle, req.q7_machine_status, req.q8_cleanliness
    ])
    avg_score = round(total / 6.0, 2)

    knock_out = avg_score > 3.0
    msg = "對手過於強大，建議放棄此店址" if knock_out else "對手威脅可控，請繼續評估候選店址"

    return CompetitorEvalResponse(
        competitor_score=avg_score,
        knock_out=knock_out,
        message=msg
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_scoring.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_scoring.py src/laundro_vision_ai/services/
git commit -m "feat: implement competitor knockout scoring logic"
```

---

### Task 3: Implement Total Score Engine

**Files:**

- Modify: `src/laundro_vision_ai/services/scoring.py`
- Modify: `tests/test_scoring.py`

- [ ] **Step 1: Write the failing test**

```python
# append to tests/test_scoring.py
from laundro_vision_ai.services.scoring import calculate_total_score
from laundro_vision_ai.models.schemas import AssessmentRequest

def test_calculate_total_score_no_competitor():
    req = AssessmentRequest(
        has_competitor=False,
        q1_cvs=5, q2_residential=5, q3_visibility=5,
        q4_signage=5, q5_motorcycle=5
    )
    res = calculate_total_score(req)
    # Audience: 5*0.35 + 5*0.25 = 3.0
    # Hardware: 5*0.15 + 5*0.15 + 5*0.10 = 2.0
    # Total: 5.0
    assert res.total_score == 5.0
    assert res.category_scores.audience == 3.0
    assert res.category_scores.hardware == 2.0
    assert res.category_scores.operations is None

def test_calculate_total_score_with_competitor():
    req = AssessmentRequest(
        has_competitor=True,
        q1_cvs=5, q2_residential=5, q3_visibility=5,
        q4_signage=5, q5_motorcycle=5, q7_machine_status=5, q8_cleanliness=5
    )
    res = calculate_total_score(req)
    # Audience: 5*0.30 + 5*0.20 = 2.5
    # Hardware: 5*0.10 + 5*0.10 + 5*0.10 = 1.5
    # Operations: 5*0.10 + 5*0.10 = 1.0
    # Total: 5.0
    assert res.total_score == 5.0
    assert res.category_scores.operations == 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_scoring.py -v` Expected: FAIL (calculate_total_score not defined)

- [ ] **Step 3: Write minimal implementation**

```python
# append to src/laundro_vision_ai/services/scoring.py
from laundro_vision_ai.models.schemas import AssessmentRequest, AssessmentResponse, CategoryScores

def calculate_total_score(req: AssessmentRequest) -> AssessmentResponse:
    if req.has_competitor:
        if req.q7_machine_status is None or req.q8_cleanliness is None:
            raise ValueError("q7 and q8 are required when competitor exists")
        audience = (req.q1_cvs * 0.30) + (req.q2_residential * 0.20)
        hardware = (req.q3_visibility * 0.10) + (req.q4_signage * 0.10) + (req.q5_motorcycle * 0.10)
        operations = (req.q7_machine_status * 0.10) + (req.q8_cleanliness * 0.10)
        total = audience + hardware + operations
    else:
        audience = (req.q1_cvs * 0.35) + (req.q2_residential * 0.25)
        hardware = (req.q3_visibility * 0.15) + (req.q4_signage * 0.15) + (req.q5_motorcycle * 0.10)
        operations = None
        total = audience + hardware

    return AssessmentResponse(
        total_score=round(total, 2),
        category_scores=CategoryScores(
            audience=round(audience, 2),
            hardware=round(hardware, 2),
            operations=round(operations, 2) if operations else None
        )
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_scoring.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_scoring.py src/laundro_vision_ai/services/scoring.py
git commit -m "feat: implement total score calculation with dynamic weights"
```

---

### Task 4: Setup FastAPI Application and Routes

**Files:**

- Create: `src/laundro_vision_ai/api/main.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from laundro_vision_ai.api.main import app

client = TestClient(app)

def test_evaluate_competitor_endpoint():
    response = client.post(
        "/api/v1/assessments/evaluate-competitor",
        json={
            "q2_residential": 4, "q3_visibility": 4, "q4_signage": 4,
            "q5_motorcycle": 4, "q7_machine_status": 4, "q8_cleanliness": 4
        }
    )
    assert response.status_code == 200
    assert response.json()["knock_out"] is True

def test_calculate_score_endpoint():
    response = client.post(
        "/api/v1/assessments/calculate-score",
        json={
            "has_competitor": False,
            "q1_cvs": 5, "q2_residential": 5, "q3_visibility": 5,
            "q4_signage": 5, "q5_motorcycle": 5
        }
    )
    assert response.status_code == 200
    assert response.json()["total_score"] == 5.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_api.py -v` Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Write minimal implementation**

```python
# src/laundro_vision_ai/api/__init__.py
# (Empty file)

# src/laundro_vision_ai/api/main.py
from fastapi import FastAPI
from laundro_vision_ai.models.schemas import (
    CompetitorEvalRequest, CompetitorEvalResponse,
    AssessmentRequest, AssessmentResponse
)
from laundro_vision_ai.services.scoring import evaluate_competitor, calculate_total_score

app = FastAPI(title="LaundroVision AI MVP API")

@app.post("/api/v1/assessments/evaluate-competitor", response_model=CompetitorEvalResponse)
def evaluate_competitor_route(req: CompetitorEvalRequest):
    return evaluate_competitor(req)

@app.post("/api/v1/assessments/calculate-score", response_model=AssessmentResponse)
def calculate_score_route(req: AssessmentRequest):
    return calculate_total_score(req)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_api.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_api.py src/laundro_vision_ai/api/
git commit -m "feat: add fastapi endpoints for scoring engine"
```

---

### Task 5: Build Streamlit Frontend App

**Files:**

- Create: `src/laundro_vision_ai/data/taiwan_districts.json`
- Create: `src/laundro_vision_ai/ui/app.py`
- Modify: `tests/test_ui_mock.py` (For testing imports, actual UI is manually tested)

- [ ] **Step 1: Write the failing test**

```python
# tests/test_ui_mock.py
def test_ui_import():
    try:
        import laundro_vision_ai.ui.app
        assert True
    except Exception as e:
        assert False, f"Import failed: {e}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_ui_mock.py -v` Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

```python
# src/laundro_vision_ai/ui/__init__.py
# (Empty file)

# src/laundro_vision_ai/ui/app.py
import streamlit as st
import requests
import json
import os

API_BASE_URL = "http://localhost:8000/api/v1"

@st.cache_data
def load_taiwan_districts():
    # Load from the local JSON file
    file_path = os.path.join(os.path.dirname(__file__), "..", "data", "taiwan_districts.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback for plan/testing if file not created yet
        return {
            "台北市": ["信義區", "大安區", "中山區"],
            "新北市": ["板橋區", "三重區", "新莊區"]
        }

def init_session():
    if "stage" not in st.session_state:
        st.session_state.stage = "INIT"
    if "has_competitor" not in st.session_state:
        st.session_state.has_competitor = False
    if "competitor_knockout" not in st.session_state:
        st.session_state.competitor_knockout = False

def render_init():
    st.title("LaundroVision AI")
    st.header("Step 1: 站點定位")

    districts_data = load_taiwan_districts()
    city = st.selectbox("縣市", list(districts_data.keys()))
    district = st.selectbox("鄉鎮市區", districts_data[city])

    address = st.text_input("地址/街道")
    if st.button("搜尋周邊"):
        # MVP Mock API Call
        st.session_state.has_competitor = True # Hardcoded for demo
        st.session_state.stage = "COMPETITOR_EVAL"
        st.rerun()

def render_competitor_eval():
    st.header("Step 2: 競爭對手評估模式")
    q2 = st.radio("Q2. 住宅型態", [1, 2, 3, 4, 5], horizontal=True)
    q3 = st.radio("Q3. 視覺攔截力", [1, 2, 3, 4, 5], horizontal=True)
    q4 = st.radio("Q4. 招牌設立", [1, 2, 3, 4, 5], horizontal=True)
    q5 = st.radio("Q5. 機車停靠", [1, 2, 3, 4, 5], horizontal=True)
    q7 = st.radio("Q7. 機器運轉", [1, 2, 3, 4, 5], horizontal=True)
    q8 = st.radio("Q8. 整潔度", [1, 2, 3, 4, 5], horizontal=True)

    if st.button("驗證對手強度"):
        payload = {
            "q2_residential": q2, "q3_visibility": q3, "q4_signage": q4,
            "q5_motorcycle": q5, "q7_machine_status": q7, "q8_cleanliness": q8
        }
        res = requests.post(f"{API_BASE_URL}/assessments/evaluate-competitor", json=payload).json()
        if res["knock_out"]:
            st.error(res["message"])
        else:
            st.session_state.stage = "TARGET_EVAL"
            st.rerun()

def render_target_eval():
    st.header("Step 3: 候選店址評估")
    st.info("Q1 已經由 API 預填為 5")
    q1 = 5
    q2 = st.radio("Q2. 住宅型態", [1, 2, 3, 4, 5], horizontal=True)
    q3 = st.radio("Q3. 視覺攔截力", [1, 2, 3, 4, 5], horizontal=True)
    q4 = st.radio("Q4. 招牌設立", [1, 2, 3, 4, 5], horizontal=True)
    q5 = st.radio("Q5. 機車停靠", [1, 2, 3, 4, 5], horizontal=True)
    q7 = 5 if st.session_state.has_competitor else None
    q8 = 5 if st.session_state.has_competitor else None

    notes = st.text_area("綜合文字評述 (顧問筆記)")

    if st.button("產生分析報告"):
        payload = {
            "has_competitor": st.session_state.has_competitor,
            "q1_cvs": q1, "q2_residential": q2, "q3_visibility": q3,
            "q4_signage": q4, "q5_motorcycle": q5,
            "q7_machine_status": q7, "q8_cleanliness": q8
        }
        res = requests.post(f"{API_BASE_URL}/assessments/calculate-score", json=payload).json()
        st.session_state.total_score = res["total_score"]
        st.session_state.stage = "REPORT"
        st.rerun()

def render_report():
    st.header("Step 4: AI 決策報告")
    score = st.session_state.get("total_score", 0)

    if score >= 4.0:
        st.success(f"🟢 綠燈！總分：{score}")
        with st.expander("展開財務試算面板", expanded=True):
            st.write("預估回本月數：24 個月")
    elif score >= 3.0:
        st.warning(f"🟡 黃燈！總分：{score}")
    else:
        st.error(f"🔴 紅燈！總分：{score}")

    if st.button("重新評估"):
        st.session_state.stage = "INIT"
        st.rerun()

def main():
    init_session()
    if st.session_state.stage == "INIT":
        render_init()
    elif st.session_state.stage == "COMPETITOR_EVAL":
        render_competitor_eval()
    elif st.session_state.stage == "TARGET_EVAL":
        render_target_eval()
    elif st.session_state.stage == "REPORT":
        render_report()

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_ui_mock.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_ui_mock.py src/laundro_vision_ai/ui/app.py
git commit -m "feat: implement progressive disclosure streamlit frontend"
```
