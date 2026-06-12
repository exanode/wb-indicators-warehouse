import argparse
import logging
import time
import uuid
from datetime import datetime

from ingestion.checkpoint import is_done, mark_done
from ingestion.config import load_config
from ingestion.fetch import fetch_indicator, fetch_country_metadata
from ingestion.logger import setup_logging
from ingestion.writer import write_indicator_to_s3, write_countries_to_s3

logger = logging.getLogger(__name__)


def run_ingest(run_date: str = None, dry_run: bool = False) -> dict:
    run_id = str(uuid.uuid4())
    start = time.time()

    config = load_config(run_date=run_date)
    pipeline = config["pipeline"]
    s3 = config["s3"]
    wb = config["wb_api"]

    if not pipeline.run_date:
        pipeline.run_date = datetime.today().strftime("%Y-%m-%d")

    setup_logging(log_path=pipeline.log_path)
    logger.info("wb ingest started", extra={"run_id": run_id, "run_date": pipeline.run_date})

    # fetch and persist country metadata first (used as dim_country)
    countries = fetch_country_metadata(wb.base_url, per_page=wb.per_page)
    if countries and not dry_run:
        write_countries_to_s3(countries, run_date=pipeline.run_date, s3_config=s3)
        logger.info("countries written count=%d", len(countries))

    rows_read = 0
    rows_written = 0
    failed = []
    skipped = 0

    for indicator in pipeline.indicators:
        if is_done(pipeline.checkpoint_path, indicator):
            logger.info("skipping indicator=%s (already done)", indicator)
            skipped += 1
            continue

        try:
            records = fetch_indicator(
                base_url=wb.base_url,
                indicator_code=indicator,
                start_year=pipeline.start_year,
                end_year=pipeline.end_year,
                per_page=wb.per_page,
            )
            rows_read += len(records)

            if dry_run:
                logger.info("dry_run indicator=%s rows=%d", indicator, len(records))
                continue

            s3_key = write_indicator_to_s3(
                records=records,
                indicator_code=indicator,
                run_date=pipeline.run_date,
                run_id=run_id,
                s3_config=s3,
            )
            if s3_key:
                rows_written += len(records)
                mark_done(pipeline.checkpoint_path, indicator, s3_key)

        except Exception as exc:
            logger.error("indicator failed indicator=%s error=%s", indicator, str(exc))
            failed.append(indicator)

        time.sleep(0.5)

    duration = round(time.time() - start, 2)
    summary = {
        "run_id": run_id,
        "run_date": pipeline.run_date,
        "indicators_total": len(pipeline.indicators),
        "indicators_skipped": skipped,
        "indicators_failed": len(failed),
        "rows_read": rows_read,
        "rows_written": rows_written,
        "duration_seconds": duration,
        "status": "success" if not failed else "partial",
    }
    logger.info("wb ingest completed", extra=summary)
    return summary


def main():
    parser = argparse.ArgumentParser(description="World Bank indicator ingest to S3")
    parser.add_argument("--run-date", help="Run date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = run_ingest(run_date=args.run_date, dry_run=args.dry_run)
    if result.get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
