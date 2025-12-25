import requests
import time
import random
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


def make_request_with_retries(url, max_retries=10, backoff_factor=1.0, timeout=5, delay_between_requests=2):
    """Make HTTP request with retries and exponential backoff."""
    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS"]
    )
    session.mount("https://", HTTPAdapter(max_retries=retries))

    logger.debug(f"Starting request to {url} with up to {max_retries} retries and timeout of {timeout} seconds.")

    for attempt in range(max_retries):
        if attempt > 0:
            logger.debug(f"Delaying {delay_between_requests} seconds before next attempt.")
            time.sleep(delay_between_requests)

        logger.debug(f"Attempt {attempt + 1} of {max_retries} for URL: {url}")
        try:
            logger.debug(f"Sending GET request to {url}")
            response = session.get(url, timeout=timeout)
            time.sleep(1)
            logger.debug(f"Response status code: {response.status_code} on attempt {attempt + 1}")
            if response.status_code == 200:
                logger.debug(f"Successfully retrieved data from {url} on attempt {attempt + 1}.")
                return response
            else:
                logger.error(f"Failed to retrieve data from {url}. Status code: {response.status_code} on attempt {attempt + 1}")
        except requests.Timeout as e:
            logger.error(f"Request to {url} timed out on attempt {attempt + 1}. Exception: {e}")
        except requests.RequestException as e:
            logger.error(f"Request to {url} failed on attempt {attempt + 1} with exception: {e}")

        # Exponential backoff with jitter
        sleep_time = backoff_factor * (2 ** attempt) + random.uniform(0, 1)
        logger.warning(f"Retrying after {sleep_time:.2f} seconds (Attempt {attempt + 1}).")
        time.sleep(sleep_time)

    logger.error(f"Max retries ({max_retries}) exceeded with URL: {url}. Giving up.")
    return None
