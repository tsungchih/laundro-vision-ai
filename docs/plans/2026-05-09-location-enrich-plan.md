# Location Enrich API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the `/locations/enrich` API backend and integrate it into the Streamlit UI to dynamically determine
the presence of competitors and pre-fill the Q1 evaluation score based on nearby POIs.

**Architecture:** A FastAPI backend with a strategy pattern (`MapProvider`) for fetching location data. The MVP will
default to an OpenStreetMap (OSM) provider using Nominatim and Overpass, with a Mock provider available for tests. The
Streamlit frontend will call this API and use the response to drive its state machine and pre-fill evaluation forms.

**Tech Stack:** Python 3.11+, FastAPI, Pydantic, pydantic-settings, requests, Streamlit, pytest, respx (for mocking
HTTP).

---

### Task 1: Add Configuration Settings

**Files:**

- Create: `src/laundro_vision_ai/core/config.py`
- Modify: `pyproject.toml` (Add `pydantic-settings` to dependencies if not present)
- Create: `tests/test_config.py`

- [ ] **Step 1: Check dependencies** If `pydantic-settings` is missing, add it to `pyproject.toml` under `dependencies`
      and run `uv lock`.

- [ ] **Step 2: Write the failing test** Create `tests/test_config.py`:

```python
import os
from laundro_vision_ai.core.config import get_settings

def test_config_defaults():
    settings = get_settings()
    assert settings.MAP_PROVIDER == "OSM"

def test_config_override():
    os.environ["MAP_PROVIDER"] = "MOCK"
    settings = get_settings()
    assert settings.MAP_PROVIDER == "MOCK"
    del os.environ["MAP_PROVIDER"]
```

- [ ] **Step 3: Run test to verify it fails** Run: `uv run pytest tests/test_config.py -v` Expected: FAIL with
      `ModuleNotFoundError: No module named 'laundro_vision_ai.core'`

- [ ] **Step 4: Write minimal implementation** Create `src/laundro_vision_ai/core/__init__.py`. Create
      `src/laundro_vision_ai/core/config.py`:

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    MAP_PROVIDER: str = "OSM"
    GOOGLE_MAPS_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 5: Run test to verify it passes** Run: `uv run pytest tests/test_config.py -v` Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml src/laundro_vision_ai/core/__init__.py src/laundro_vision_ai/core/config.py tests/test_config.py
git commit -m "feat(core): add pydantic settings for MAP_PROVIDER"
```

---

### Task 2: Create Request and Response Schemas

**Files:**

- Modify: `src/laundro_vision_ai/models/schemas.py`
- Modify: `tests/test_schemas.py`

- [ ] **Step 1: Write the failing test** Add to `tests/test_schemas.py`:

```python
from laundro_vision_ai.models.schemas import LocationEnrichRequest, LocationEnrichResponse

def test_location_enrich_request():
    req = LocationEnrichRequest(address="Taipei 101", lat=25.0, lng=121.5)
    assert req.address == "Taipei 101"

def test_location_enrich_response():
    resp = LocationEnrichResponse(
        has_competitor_in_1000m=True,
        competitors_data=["Laundry A"],
        cvs_mcd_in_200m=["7-11"],
        has_starbucks=False,
        recommended_q1_score=3
    )
    assert resp.recommended_q1_score == 3
```

- [ ] **Step 2: Run test to verify it fails** Run: `uv run pytest tests/test_schemas.py -v` Expected: FAIL with
      `ImportError`

- [ ] **Step 3: Write minimal implementation** Add to `src/laundro_vision_ai/models/schemas.py`:

```python
class LocationEnrichRequest(BaseModel):
    address: str
    lat: float | None = None
    lng: float | None = None

class LocationEnrichResponse(BaseModel):
    has_competitor_in_1000m: bool
    competitors_data: list[str]
    cvs_mcd_in_200m: list[str]
    has_starbucks: bool
    recommended_q1_score: int
```

- [ ] **Step 4: Run test to verify it passes** Run: `uv run pytest tests/test_schemas.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/laundro_vision_ai/models/schemas.py tests/test_schemas.py
git commit -m "feat(models): add LocationEnrich request and response schemas"
```

---

### Task 3: Map Provider Interface & Mock Implementation

**Files:**

- Create: `src/laundro_vision_ai/services/location.py`
- Create: `tests/test_location.py`

- [ ] **Step 1: Write the failing test** Create `tests/test_location.py`:

```python
import pytest
from laundro_vision_ai.services.location import MockMapProvider

def test_mock_provider_geocode():
    provider = MockMapProvider()
    lat, lng = provider.geocode("Taipei")
    assert isinstance(lat, float)
    assert isinstance(lng, float)

def test_mock_provider_enrich():
    provider = MockMapProvider()
    result = provider.enrich_location(25.0, 121.0)
    assert "has_competitor_in_1000m" in result
    assert result["has_starbucks"] is False
```

- [ ] **Step 2: Run test to verify it fails** Run: `uv run pytest tests/test_location.py -v` Expected: FAIL with
      `ImportError`

- [ ] **Step 3: Write minimal implementation** Create `src/laundro_vision_ai/services/location.py`:

```python
from abc import ABC, abstractmethod

class MapProvider(ABC):
    @abstractmethod
    def geocode(self, address: str) -> tuple[float, float]:
        """Converts an address string into (latitude, longitude)."""
        pass

    @abstractmethod
    def enrich_location(self, lat: float, lng: float) -> dict:
        """Performs POI searches and returns the enrichment data dictionary."""
        pass

class MockMapProvider(MapProvider):
    def geocode(self, address: str) -> tuple[float, float]:
        return (25.033964, 121.564472)

    def enrich_location(self, lat: float, lng: float) -> dict:
        return {
            "has_competitor_in_1000m": True,
            "competitors_data": ["Mock Laundry 1"],
            "cvs_mcd_in_200m": ["7-11", "McDonald's"],
            "has_starbucks": False,
        }
```

- [ ] **Step 4: Run test to verify it passes** Run: `uv run pytest tests/test_location.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/laundro_vision_ai/services/location.py tests/test_location.py
git commit -m "feat(services): add MapProvider interface and MockMapProvider"
```

---

### Task 4: OSM Map Provider Implementation

**Files:**

- Modify: `src/laundro_vision_ai/services/location.py`
- Modify: `tests/test_location.py`

- [ ] **Step 1: Write the failing test** Add to `tests/test_location.py`:

```python
import respx
from httpx import Response
from laundro_vision_ai.services.location import OSMMapProvider

@respx.mock
def test_osm_provider_geocode():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=Response(200, json=[{"lat": "25.033964", "lon": "121.564472"}])
    )
    provider = OSMMapProvider()
    lat, lng = provider.geocode("Taipei 101")
    assert lat == 25.033964
    assert lng == 121.564472

@respx.mock
def test_osm_provider_enrich():
    overpass_response = {
        "elements": [
            {"tags": {"shop": "laundry", "name": "Wash"}},
            {"tags": {"shop": "convenience", "name": "7-11"}},
            {"tags": {"amenity": "cafe", "name": "Starbucks"}},
        ]
    }
    respx.post("https://overpass-api.de/api/interpreter").mock(
        return_value=Response(200, json=overpass_response)
    )
    provider = OSMMapProvider()
    result = provider.enrich_location(25.0, 121.0)
    assert result["has_competitor_in_1000m"] is True
    assert result["competitors_data"] == ["Wash"]
    assert "7-11" in result["cvs_mcd_in_200m"]
    assert result["has_starbucks"] is True
```

- [ ] **Step 2: Run test to verify it fails** Run: `uv run pytest tests/test_location.py -v` Expected: FAIL (Ensure
      `respx` is installed, add to `pyproject.toml` dev dependencies if missing).

- [ ] **Step 3: Write minimal implementation** Add to `src/laundro_vision_ai/services/location.py`:

```python
import requests

class OSMMapProvider(MapProvider):
    def geocode(self, address: str) -> tuple[float, float]:
        headers = {"User-Agent": "LaundroVision/1.0"}
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": address, "format": "json", "limit": 1}
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        if not data:
            raise ValueError(f"Could not geocode address: {address}")
        return float(data[0]["lat"]), float(data[0]["lon"])

    def enrich_location(self, lat: float, lng: float) -> dict:
        query = f"""
        [out:json];
        (
          node(around:1000,{lat},{lng})["shop"="laundry"];
          node(around:200,{lat},{lng})["shop"="convenience"];
          node(around:200,{lat},{lng})["amenity"="fast_food"];
          node(around:200,{lat},{lng})["amenity"="cafe"];
        );
        out tags;
        """
        response = requests.post("https://overpass-api.de/api/interpreter", data={"data": query})
        response.raise_for_status()
        elements = response.json().get("elements", [])

        competitors = []
        cvs_mcd = []
        has_starbucks = False

        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name", "Unknown")

            if tags.get("shop") == "laundry":
                competitors.append(name)
            elif tags.get("shop") == "convenience":
                cvs_mcd.append(name)
            elif tags.get("amenity") == "fast_food" and ("McDonald" in name or "麥當勞" in name):
                cvs_mcd.append(name)
            elif tags.get("amenity") == "cafe" and ("Starbucks" in name or "星巴克" in name):
                has_starbucks = True

        return {
            "has_competitor_in_1000m": len(competitors) > 0,
            "competitors_data": competitors,
            "cvs_mcd_in_200m": cvs_mcd,
            "has_starbucks": has_starbucks,
        }
```

- [ ] **Step 4: Run test to verify it passes** Run: `uv run pytest tests/test_location.py -v` Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/laundro_vision_ai/services/location.py tests/test_location.py
git commit -m "feat(services): implement OSMMapProvider with geocoding and Overpass"
```

---

### Task 5: Factory and Q1 Scoring Logic

**Files:**

- Modify: `src/laundro_vision_ai/services/location.py`
- Modify: `tests/test_location.py`

- [ ] **Step 1: Write the failing test** Add to `tests/test_location.py`:

```python
import os
from laundro_vision_ai.services.location import get_map_provider, calculate_q1_score

def test_get_map_provider():
    os.environ["MAP_PROVIDER"] = "MOCK"
    provider = get_map_provider()
    assert isinstance(provider, MockMapProvider)
    del os.environ["MAP_PROVIDER"]

def test_calculate_q1_score():
    assert calculate_q1_score(True, []) == 1
    assert calculate_q1_score(False, []) == 1
    assert calculate_q1_score(False, ["7-11"]) == 3
    assert calculate_q1_score(False, ["7-11", "FamilyMart"]) == 5
    assert calculate_q1_score(False, ["McDonald's"]) == 5
```

- [ ] **Step 2: Run test to verify it fails** Run: `uv run pytest tests/test_location.py -v`

- [ ] **Step 3: Write minimal implementation** Add to `src/laundro_vision_ai/services/location.py`:

```python
from laundro_vision_ai.core.config import get_settings

def get_map_provider() -> MapProvider:
    provider = get_settings().MAP_PROVIDER
    if provider == "MOCK":
        return MockMapProvider()
    return OSMMapProvider()

def calculate_q1_score(has_starbucks: bool, cvs_mcd: list[str]) -> int:
    if has_starbucks or not cvs_mcd:
        return 1

    has_mcd = any("McDonald" in name or "麥當勞" in name for name in cvs_mcd)
    if has_mcd or len(cvs_mcd) >= 2:
        return 5

    if len(cvs_mcd) == 1:
        return 3

    return 1
```

- [ ] **Step 4: Run test to verify it passes** Run: `uv run pytest tests/test_location.py -v`

- [ ] **Step 5: Commit**

```bash
git add src/laundro_vision_ai/services/location.py tests/test_location.py
git commit -m "feat(services): add factory get_map_provider and calculate_q1_score"
```

---

### Task 6: FastAPI Route Implementation

**Files:**

- Modify: `src/laundro_vision_ai/api/main.py`
- Modify: `tests/test_api.py`

- [ ] **Step 1: Write the failing test** Add to `tests/test_api.py`:

```python
import os
from fastapi.testclient import TestClient
from laundro_vision_ai.api.main import app

client = TestClient(app)

def test_enrich_location_endpoint():
    os.environ["MAP_PROVIDER"] = "MOCK"
    response = client.post("/api/v1/locations/enrich", json={"address": "Taipei"})
    assert response.status_code == 200
    data = response.json()
    assert "has_competitor_in_1000m" in data
    assert "recommended_q1_score" in data
    assert data["recommended_q1_score"] in [1, 2, 3, 4, 5]
    if "MAP_PROVIDER" in os.environ:
        del os.environ["MAP_PROVIDER"]
```

- [ ] **Step 2: Run test to verify it fails** Run: `uv run pytest tests/test_api.py -v` Expected: FAIL with
      `404 Not Found`

- [ ] **Step 3: Write minimal implementation** Modify `src/laundro_vision_ai/api/main.py`:

```python
from laundro_vision_ai.models.schemas import LocationEnrichRequest, LocationEnrichResponse
from laundro_vision_ai.services.location import get_map_provider, calculate_q1_score
from fastapi import HTTPException

# Add this route below existing routes
@app.post("/api/v1/locations/enrich", response_model=LocationEnrichResponse)
def enrich_location_route(req: LocationEnrichRequest):
    provider = get_map_provider()
    lat, lng = req.lat, req.lng

    if lat is None or lng is None:
        try:
            lat, lng = provider.geocode(req.address)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    try:
        data = provider.enrich_location(lat, lng)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"POI search failed: {str(e)}")

    q1_score = calculate_q1_score(data["has_starbucks"], data["cvs_mcd_in_200m"])

    return LocationEnrichResponse(
        has_competitor_in_1000m=data["has_competitor_in_1000m"],
        competitors_data=data["competitors_data"],
        cvs_mcd_in_200m=data["cvs_mcd_in_200m"],
        has_starbucks=data["has_starbucks"],
        recommended_q1_score=q1_score
    )
```

- [ ] **Step 4: Run test to verify it passes** Run: `uv run pytest tests/test_api.py -v`

- [ ] **Step 5: Commit**

```bash
git add src/laundro_vision_ai/api/main.py tests/test_api.py
git commit -m "feat(api): implement /locations/enrich endpoint"
```

---

### Task 7: Streamlit UI Integration

**Files:**

- Modify: `src/laundro_vision_ai/ui/app.py`

- [ ] **Step 1: Modify Session State Initialization** In `src/laundro_vision_ai/ui/app.py`, update `init_session()`:

```python
def init_session():
    if "stage" not in st.session_state:
        st.session_state.stage = "INIT"
    if "has_competitor" not in st.session_state:
        st.session_state.has_competitor = False
    if "competitor_knockout" not in st.session_state:
        st.session_state.competitor_knockout = False
    if "recommended_q1_score" not in st.session_state:
        st.session_state.recommended_q1_score = 5
    if "cvs_mcd_in_200m" not in st.session_state:
        st.session_state.cvs_mcd_in_200m = []
```

- [ ] **Step 2: Implement Address Search Call** In `render_init()`:

```python
    if st.button("搜尋周邊"):
        full_address = f"{city}{district}{address}"
        with st.spinner("Geocoding and scanning for competitors..."):
            try:
                res = requests.post(f"{API_BASE_URL}/locations/enrich", json={"address": full_address})
                res.raise_for_status()
                data = res.json()

                st.session_state.has_competitor = data["has_competitor_in_1000m"]
                st.session_state.recommended_q1_score = data["recommended_q1_score"]
                st.session_state.cvs_mcd_in_200m = data["cvs_mcd_in_200m"]

                if st.session_state.has_competitor:
                    st.session_state.stage = "COMPETITOR_EVAL"
                else:
                    st.session_state.stage = "TARGET_EVAL"
                st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"API Request Failed: {e}")
```

- [ ] **Step 3: Render Q1 with default state in Target Eval** In `render_target_eval()`, replace the hardcoded Q1:

```python
    st.header("Step 3: 候選店址評估")

    cvs_list = st.session_state.get('cvs_mcd_in_200m', [])
    st.info(f"API 探測周邊 POI: {cvs_list}")

    default_q1_index = st.session_state.get("recommended_q1_score", 5) - 1

    q1 = st.radio("Q1. CVS / 麥當勞", [1, 2, 3, 4, 5], index=default_q1_index, horizontal=True)
```

- [ ] **Step 4: Manual UI Testing** Start the API: `uv run uvicorn laundro_vision_ai.api.main:app --reload` Start
      Streamlit: `uv run streamlit run src/laundro_vision_ai/ui/app.py` Verify the address search routes to the correct
      evaluation step and pre-fills the Q1 score properly.

- [ ] **Step 5: Commit**

```bash
git add src/laundro_vision_ai/ui/app.py
git commit -m "feat(ui): integrate locations/enrich API for automated competitor scan"
```

---
