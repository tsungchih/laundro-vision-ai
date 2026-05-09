from unittest.mock import patch

import respx
from httpx import Response

from laundro_vision_ai.services.location import MockMapProvider, OSMMapProvider


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


@respx.mock
def test_osm_provider_geocode():
    respx.get("https://nominatim.openstreetmap.org/search").mock(
        return_value=Response(200, json=[{"lat": "25.0338352", "lon": "121.5644995"}])
    )
    provider = OSMMapProvider()
    lat, lng = provider.geocode("Taipei 101")
    assert round(lat, 7) == 25.0338352
    assert round(lng, 7) == 121.5644995


@patch("requests.post")
def test_osm_provider_enrich(mock_post):
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {
        "elements": [
            {"tags": {"shop": "laundry", "name": "Wash"}},
            {"tags": {"shop": "convenience", "name": "7-11"}},
            {"tags": {"amenity": "cafe", "name": "Starbucks"}},
        ]
    }
    mock_post.return_value.raise_for_status.return_value = None

    provider = OSMMapProvider()
    result = provider.enrich_location(25.0, 121.0)
    assert result["has_competitor_in_1000m"] is True
    assert result["competitors_data"] == ["Wash"]
    assert "7-11" in result["cvs_mcd_in_200m"]
    assert result["has_starbucks"] is True
