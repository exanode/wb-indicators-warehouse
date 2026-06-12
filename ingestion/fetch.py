import logging
import time

import requests
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

logger = logging.getLogger(__name__)


class APIError(Exception):
    pass


@retry(
    retry=retry_if_exception_type((requests.Timeout, requests.ConnectionError, APIError)),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
)
def _get(url: str, params: dict) -> dict:
    resp = requests.get(url, params=params, timeout=30)
    if resp.status_code == 429:
        raise APIError(f"rate limited: {url}")
    resp.raise_for_status()
    return resp.json()


def fetch_indicator(
    base_url: str,
    indicator_code: str,
    start_year: int,
    end_year: int,
    per_page: int = 1000,
) -> list[dict]:
    """
    Fetch all country-year values for a single indicator.
    WB API paginates by 'page'; we keep calling until we exhaust pages.
    """
    all_records = []
    page = 1

    while True:
        url = f"{base_url}/country/all/indicator/{indicator_code}"
        params = {
            "format": "json",
            "per_page": per_page,
            "mrv": end_year - start_year + 1,
            "date": f"{start_year}:{end_year}",
            "page": page,
        }

        try:
            response = _get(url, params)
        except Exception as exc:
            logger.error("fetch failed indicator=%s page=%d error=%s", indicator_code, page, exc)
            break

        if not response or len(response) < 2:
            logger.warning("unexpected response shape for indicator=%s", indicator_code)
            break

        meta = response[0]
        records = response[1]

        if not records:
            break

        all_records.extend(records)
        logger.debug("indicator=%s page=%d/%d rows=%d", indicator_code, page, meta.get("pages", "?"), len(records))

        if page >= meta.get("pages", 1):
            break

        page += 1
        time.sleep(0.3)  # polite delay

    logger.info("indicator=%s total_rows=%d", indicator_code, len(all_records))
    return all_records


def fetch_country_metadata(base_url: str, per_page: int = 500) -> list[dict]:
    """Fetch all country metadata from WB API (iso2, iso3, name, region, income group)."""
    url = f"{base_url}/country"
    params = {"format": "json", "per_page": per_page}

    try:
        response = _get(url, params)
        return response[1] if response and len(response) > 1 else []
    except Exception as exc:
        logger.error("country metadata fetch failed: %s", exc)
        return []
