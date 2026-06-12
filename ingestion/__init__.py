import io
import logging
from datetime import datetime, timezone

import boto3
import pyarrow as pa
import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

INDICATOR_SCHEMA = pa.schema([
    pa.field("indicator_code", pa.string(), nullable=False),
    pa.field("indicator_name", pa.string(), nullable=True),
    pa.field("country_iso2", pa.string(), nullable=False),
    pa.field("country_name", pa.string(), nullable=True),
    pa.field("year", pa.int32(), nullable=False),
    pa.field("value", pa.float64(), nullable=True),
    pa.field("ingested_at", pa.timestamp("us", tz="UTC"), nullable=False),
    pa.field("run_id", pa.string(), nullable=False),
])

COUNTRY_SCHEMA = pa.schema([
    pa.field("country_iso2", pa.string(), nullable=False),
    pa.field("country_iso3", pa.string(), nullable=True),
    pa.field("country_name", pa.string(), nullable=False),
    pa.field("capital_city", pa.string(), nullable=True),
    pa.field("region_id", pa.string(), nullable=True),
    pa.field("region_name", pa.string(), nullable=True),
    pa.field("income_level_id", pa.string(), nullable=True),
    pa.field("income_level_name", pa.string(), nullable=True),
    pa.field("lending_type", pa.string(), nullable=True),
    pa.field("longitude", pa.float64(), nullable=True),
    pa.field("latitude", pa.float64(), nullable=True),
    pa.field("ingested_at", pa.timestamp("us", tz="UTC"), nullable=False),
])


def _map_indicator_records(records: list[dict], run_id: str, ingested_at) -> list[dict]:
    mapped = []
    for r in records:
        val = r.get("value")
        mapped.append({
            "indicator_code": r.get("indicator", {}).get("id"),
            "indicator_name": r.get("indicator", {}).get("value"),
            "country_iso2": r.get("country", {}).get("id"),
            "country_name": r.get("country", {}).get("value"),
            "year": int(r["date"]) if r.get("date") else None,
            "value": float(val) if val is not None else None,
            "ingested_at": ingested_at,
            "run_id": run_id,
        })
    return [m for m in mapped if m["indicator_code"] and m["country_iso2"] and m["year"]]


def _map_country_records(records: list[dict], ingested_at) -> list[dict]:
    mapped = []
    for r in records:
        try:
            lon = float(r["longitude"]) if r.get("longitude") else None
            lat = float(r["latitude"]) if r.get("latitude") else None
        except (ValueError, TypeError):
            lon, lat = None, None

        mapped.append({
            "country_iso2": r.get("id"),
            "country_iso3": r.get("iso2Code"),  # WB swaps iso2/iso3 field names
            "country_name": r.get("name"),
            "capital_city": r.get("capitalCity"),
            "region_id": r.get("region", {}).get("id"),
            "region_name": r.get("region", {}).get("value"),
            "income_level_id": r.get("incomeLevel", {}).get("id"),
            "income_level_name": r.get("incomeLevel", {}).get("value"),
            "lending_type": r.get("lendingType", {}).get("value"),
            "longitude": lon,
            "latitude": lat,
            "ingested_at": ingested_at,
        })
    return [m for m in mapped if m["country_iso2"]]


def _write_parquet_to_s3(table: pa.Table, bucket: str, key: str, region: str) -> None:
    buf = io.BytesIO()
    pq.write_table(table, buf, compression="snappy")
    buf.seek(0)
    client = boto3.client("s3", region_name=region)
    client.put_object(Bucket=bucket, Key=key, Body=buf.getvalue())
    logger.info("s3 write complete bucket=%s key=%s rows=%d", bucket, key, table.num_rows)


def write_indicator_to_s3(
    records: list[dict],
    indicator_code: str,
    run_date: str,
    run_id: str,
    s3_config,
) -> str:
    if not records:
        logger.warning("no records for indicator=%s", indicator_code)
        return None

    ingested_at = datetime.now(tz=timezone.utc)
    mapped = _map_indicator_records(records, run_id=run_id, ingested_at=ingested_at)

    df_mapped = pa.Table.from_pylist(mapped, schema=INDICATOR_SCHEMA).to_pandas()
    df_mapped = df_mapped.drop_duplicates(subset=["indicator_code", "country_iso2", "year"])
    table = pa.Table.from_pandas(df_mapped, schema=INDICATOR_SCHEMA, preserve_index=False)

    safe_code = indicator_code.replace(".", "_")
    key = f"{s3_config.raw_prefix}/run_date={run_date}/indicator={safe_code}/data.parquet"
    _write_parquet_to_s3(table, s3_config.bucket, key, s3_config.region)
    return key


def write_countries_to_s3(records: list[dict], run_date: str, s3_config) -> str:
    if not records:
        return None

    ingested_at = datetime.now(tz=timezone.utc)
    mapped = _map_country_records(records, ingested_at=ingested_at)
    table = pa.Table.from_pylist(mapped, schema=COUNTRY_SCHEMA)
    key = f"{s3_config.raw_prefix}/run_date={run_date}/countries/data.parquet"
    _write_parquet_to_s3(table, s3_config.bucket, key, s3_config.region)
    return key
