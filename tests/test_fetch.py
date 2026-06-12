import pytest
from unittest.mock import patch

from ingestion.fetch import fetch_indicator, fetch_country_metadata


MOCK_INDICATOR_PAGE_1 = [
    {"page": 1, "pages": 2, "per_page": 2, "total": 4},
    [
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "IN", "value": "India"},
            "date": "2022",
            "value": 3.385e12,
        },
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "US", "value": "United States"},
            "date": "2022",
            "value": 2.52e13,
        },
    ],
]

MOCK_INDICATOR_PAGE_2 = [
    {"page": 2, "pages": 2, "per_page": 2, "total": 4},
    [
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "CN", "value": "China"},
            "date": "2022",
            "value": 1.78e13,
        },
        {
            "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
            "country": {"id": "DE", "value": "Germany"},
            "date": "2022",
            "value": 4.07e12,
        },
    ],
]

MOCK_COUNTRY_RESPONSE = [
    {"page": 1, "pages": 1, "per_page": 500, "total": 2},
    [
        {
            "id": "IN", "iso2Code": "IND", "name": "India",
            "capitalCity": "New Delhi",
            "region": {"id": "SAS", "value": "South Asia"},
            "incomeLevel": {"id": "LMIC", "value": "Lower middle income"},
            "lendingType": {"value": "IBRD"},
            "longitude": "77.225", "latitude": "28.6353",
        },
    ],
]


@patch("ingestion.fetch._get")
def test_fetch_indicator_paginates(mock_get):
    mock_get.side_effect = [MOCK_INDICATOR_PAGE_1, MOCK_INDICATOR_PAGE_2]
    records = fetch_indicator(
        base_url="https://api.worldbank.org/v2",
        indicator_code="NY.GDP.MKTP.CD",
        start_year=2022,
        end_year=2022,
    )
    assert len(records) == 4
    assert mock_get.call_count == 2


@patch("ingestion.fetch._get")
def test_fetch_indicator_empty_response(mock_get):
    mock_get.return_value = [{"page": 1, "pages": 1}, []]
    records = fetch_indicator("https://api.worldbank.org/v2", "BAD.CODE", 2020, 2022)
    assert records == []


@patch("ingestion.fetch._get")
def test_fetch_country_metadata(mock_get):
    mock_get.return_value = MOCK_COUNTRY_RESPONSE
    countries = fetch_country_metadata("https://api.worldbank.org/v2")
    assert len(countries) == 1
    assert countries[0]["id"] == "IN"
