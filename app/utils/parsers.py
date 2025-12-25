import re
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


def parse_reputation(reputation_str):
    """Parse reputation string (e.g., '10k', '1.5M') into an integer."""
    try:
        if 'k' in reputation_str:
            return int(float(reputation_str.replace('k', '').replace(',', '')) * 1000)
        elif 'M' in reputation_str:
            return int(float(reputation_str.replace('M', '').replace(',', '')) * 1000000)
        else:
            return int(reputation_str.replace(',', ''))
    except Exception as e:
        logger.debug(f"Reputation parsing error: {e} for reputation string: {reputation_str}")
        return 0


def parse_date(date_str):
    """Parse a date string into a Unix timestamp."""
    # Remove any extra text after the actual date using regex
    match = re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z)?", date_str)
    if match:
        date_str = match.group(0)
    
    date_formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%fZ',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%d %H:%M:%SZ',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%b %d, %Y at %H:%M',
    ]
    
    for fmt in date_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if 'Z' in date_str or fmt.endswith('Z'):
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except (ValueError, TypeError):
            continue
    
    logger.debug(f"Date parsing error: No matching format for date string: {date_str}")
    return None


def parse_view_count(view_count_str):
    """Parse a view count string (e.g., '691k') into an integer."""
    view_count_str = view_count_str.lower().replace('viewed', '').strip()
    
    if not view_count_str:
        logger.warning("View count string is empty, defaulting to 0.")
        return 0

    if 'k' in view_count_str:
        return int(float(view_count_str.replace('k', '').replace(',', '')) * 1000)
    elif 'm' in view_count_str:
        return int(float(view_count_str.replace('m', '').replace(',', '')) * 1000000)
    elif 'b' in view_count_str:
        return int(float(view_count_str.replace('b', '').replace(',', '')) * 1000000000)
    else:
        try:
            return int(view_count_str.replace(',', ''))
        except ValueError as e:
            logger.error(f"Failed to parse view count: {view_count_str} - {str(e)}")
            return 0
