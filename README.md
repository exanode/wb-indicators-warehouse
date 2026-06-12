# wb-indicators-warehouse

Warehouse for World Bank development indicators: 60+ years, 200+ countries, 10 indicators. Paginated REST API ingest -> S3 Parquet -> Snowflake -> dbt Kimball star schema.

---

## Architecture

```
World Bank REST API  (api.worldbank.org/v2)
  |  paginated per indicator, checkpoint/retry on failures
S3 raw/wb/indicators/run_date=YYYY-MM-DD/indicator=NY_GDP_MKTP_CD/data.parquet
  |  COPY INTO
Snowflake RAW schema
  |  dbt
Snowflake MARTS.fct_indicator_values  (grain: country x indicator x year)
Snowflake MARTS.dim_country
Snowflake MARTS.dim_indicator
Snowflake SNAPSHOTS.scd_dim_country   (SCD2, tracks income level reclassifications)
```

---

## Star schema

**Fact grain**: `country_iso2 x indicator_code x year`  
~1M+ rows for default indicator set across 60+ years.

**dim_country** is SCD2 via `dbt snapshot`. Countries do get reclassified (China moved from lower-middle to upper-middle income in 2010). The snapshot preserves that history.

**Incremental strategy**: on each run, re-processes the last 2 years to catch WB's late-arriving corrections. Earlier years are stable.

---

## Default indicators

`NY.GDP.MKTP.CD`, `SP.POP.TOTL`, `SL.UEM.TOTL.ZS`, `SE.XPD.TOTL.GD.ZS`, `SH.XPD.CHEX.GD.ZS`, `EN.ATM.CO2E.PC`, `FP.CPI.TOTL.ZG`, `NE.EXP.GNFS.ZS`

Override via `INDICATOR_CODES` in `.env` (comma-separated WB indicator codes).

---

## Setup

```bash
git clone https://github.com/sachin-ram/wb-indicators-warehouse.git
cd wb-indicators-warehouse
python -m venv env && source env/bin/activate
pip install -r requirements.txt
cp .env.example .env

cd dbt_project && dbt deps && dbt debug
```

---

## Running

```bash
python -m ingestion.main                        # today
python -m ingestion.main --run-date 2024-01-15  # specific date
python -m ingestion.main --dry-run              # fetch only

cd dbt_project
dbt run
dbt snapshot
dbt test
```

---

## Tests

```bash
pytest tests/ -v
```

---

## Folder structure

```
wb-indicators-warehouse/
|-- ingestion/
|   |-- config.py      env-based config, default indicator list
|   |-- checkpoint.py  indicator-level ingest state
|   |-- fetch.py       paginated WB API with tenacity retry
|   |-- writer.py      PyArrow schema -> S3 Parquet
|   |-- logger.py      structured JSON logging
|   `-- main.py        CLI entrypoint
|-- dbt_project/
|   |-- models/staging/
|   |-- models/intermediate/
|   |-- models/marts/
|   |-- snapshots/
|   `-- macros/
|-- airflow/dags/
|-- tests/
`-- sample_data/
```
