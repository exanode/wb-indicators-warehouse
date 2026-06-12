from datetime import datetime, timezone

from ingestion.writer import _map_indicator_records, _map_country_records


SAMPLE_INDICATOR_RECORDS = [
    {
        "indicator": {"id": "SP.POP.TOTL", "value": "Population, total"},
        "country": {"id": "IN", "value": "India"},
        "date": "2022",
        "value": 1407563842,
    },
    {
        "indicator": {"id": "SP.POP.TOTL", "value": "Population, total"},
        "country": {"id": "US", "value": "United States"},
        "date": "2022",
        "value": None,  # missing value should be preserved as None
    },
]

SAMPLE_COUNTRY_RECORDS = [
    {
        "id": "IN",
        "iso2Code": "IND",
        "name": "India",
        "capitalCity": "New Delhi",
        "region": {"id": "SAS", "value": "South Asia"},
        "incomeLevel": {"id": "LMIC", "value": "Lower middle income"},
        "lendingType": {"value": "IBRD"},
        "longitude": "77.225",
        "latitude": "28.6353",
    },
    {
        # aggregate region - should be included (filtering happens in dbt)
        "id": "1W",
        "iso2Code": None,
        "name": "World",
        "capitalCity": "",
        "region": {"id": "NA", "value": ""},
        "incomeLevel": {"id": "NA", "value": "Aggregates"},
        "lendingType": {"value": "Aggregates"},
        "longitude": None,
        "latitude": None,
    },
]


def test_map_indicator_records_basic():
    now = datetime.now(tz=timezone.utc)
    result = _map_indicator_records(SAMPLE_INDICATOR_RECORDS, run_id="test-run", ingested_at=now)

    assert len(result) == 2
    india = next(r for r in result if r["country_iso2"] == "IN")
    assert india["value"] == 1407563842
    assert india["year"] == 2022
    assert india["indicator_code"] == "SP.POP.TOTL"


def test_map_indicator_records_null_value_preserved():
    now = datetime.now(tz=timezone.utc)
    result = _map_indicator_records(SAMPLE_INDICATOR_RECORDS, run_id="r1", ingested_at=now)
    us = next(r for r in result if r["country_iso2"] == "US")
    assert us["value"] is None


def test_map_country_records():
    now = datetime.now(tz=timezone.utc)
    result = _map_country_records(SAMPLE_COUNTRY_RECORDS, ingested_at=now)

    india = next(r for r in result if r["country_iso2"] == "IN")
    assert india["country_name"] == "India"
    assert india["region_id"] == "SAS"
    assert india["latitude"] == 28.6353


def test_map_country_drops_null_iso2():
    now = datetime.now(tz=timezone.utc)
    # record with no id
    records = [{"id": None, "name": "Ghost", "region": {}, "incomeLevel": {}, "lendingType": {}}]
    result = _map_country_records(records, ingested_at=now)
    assert result == []
