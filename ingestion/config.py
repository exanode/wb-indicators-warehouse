import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()

# indicators we track by default
DEFAULT_INDICATORS = [
    "NY.GDP.MKTP.CD",      # GDP (current US$)
    "SP.POP.TOTL",          # Population
    "SL.UEM.TOTL.ZS",       # Unemployment rate
    "SE.XPD.TOTL.GD.ZS",   # Education expenditure (% of GDP)
    "SH.XPD.CHEX.GD.ZS",   # Health expenditure (% of GDP)
    "EN.ATM.CO2E.PC",       # CO2 emissions per capita
    "SI.POV.NAHC",          # Poverty headcount ratio
    "FP.CPI.TOTL.ZG",       # Inflation (CPI)
    "NE.EXP.GNFS.ZS",       # Exports (% of GDP)
    "BX.KLT.DINV.WD.GD.ZS",# FDI (% of GDP)
]


@dataclass
class S3Config:
    bucket: str
    region: str
    raw_prefix: str = "raw/wb/indicators"


@dataclass
class SnowflakeConfig:
    account: str
    user: str
    password: str
    role: str
    warehouse: str
    database: str
    schema: str


@dataclass
class WBApiConfig:
    base_url: str = "https://api.worldbank.org/v2"
    per_page: int = 1000
    max_date_per_call: int = 60  # years per API call (WB allows full history)


@dataclass
class PipelineConfig:
    run_date: str
    indicators: list = field(default_factory=lambda: DEFAULT_INDICATORS)
    checkpoint_path: str = "checkpoints/wb_checkpoint.json"
    log_path: str = "logs/wb_pipeline.log"
    start_year: int = 1960
    end_year: int = 2023


def load_config(run_date: str = None) -> dict:
    raw_indicators = os.environ.get("INDICATOR_CODES", "")
    indicators = [i.strip() for i in raw_indicators.split(",") if i.strip()] or DEFAULT_INDICATORS

    return {
        "s3": S3Config(
            bucket=os.environ["S3_BUCKET"],
            region=os.environ.get("AWS_REGION", "us-east-1"),
        ),
        "snowflake": SnowflakeConfig(
            account=os.environ["SNOWFLAKE_ACCOUNT"],
            user=os.environ["SNOWFLAKE_USER"],
            password=os.environ["SNOWFLAKE_PASSWORD"],
            role=os.environ.get("SNOWFLAKE_ROLE", "TRANSFORMER"),
            warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "COMPUTE_WH"),
            database=os.environ.get("SNOWFLAKE_DATABASE", "WB_WAREHOUSE"),
            schema=os.environ.get("SNOWFLAKE_SCHEMA", "RAW"),
        ),
        "wb_api": WBApiConfig(),
        "pipeline": PipelineConfig(
            run_date=run_date or os.environ.get("RUN_DATE"),
            indicators=indicators,
        ),
    }
