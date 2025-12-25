import re
import logging
from bs4 import BeautifulSoup
from app.utils import make_request_with_retries

logger = logging.getLogger(__name__)


def scrape_user_profile(user_profile_link):
    """Scrape a user's profile link for user_id and account_id."""
    response = make_request_with_retries(user_profile_link)
    if response is None or response.status_code != 200:
        logger.debug(f"Failed to fetch user profile for link {user_profile_link}")
        return None, None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract user_id from the URL
    user_id_str = user_profile_link.split('/')[-2]
    try:
        user_id = int(user_id_str)
    except ValueError as e:
        logger.debug(f"User ID parsing error: {e} for user_id_str: {user_id_str}")
        user_id = None
    
    # Extract account_id using regex
    account_id_script = soup.find('script', string=lambda text: text and 'accountId' in text)
    if account_id_script:
        account_id_match = re.search(r'accountId\s*:\s*(\d+)', account_id_script.string)
        if account_id_match:
            account_id = int(account_id_match.group(1))
        else:
            logger.debug(f"Account ID not found in script for user link: {user_profile_link}")
            account_id = None
    else:
        logger.debug(f"No accountId script found for user link: {user_profile_link}")
        account_id = None
    
    return user_id, account_id
