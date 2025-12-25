import logging
from bs4 import BeautifulSoup
from app.utils import make_request_with_retries, parse_reputation, parse_date
from app.scrapers.users import scrape_user_profile

logger = logging.getLogger(__name__)

BASE_URL = "https://stackoverflow.com"


def scrape_answer_by_id(answer_id):
    """Scrape an answer by its ID."""
    answer_url = f"{BASE_URL}/a/{answer_id}"
    response = make_request_with_retries(answer_url)
    
    if response is None or response.status_code != 200:
        logger.error(f"Failed to fetch answer details for ID {answer_id}")
        return None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    try:
        body_tag = soup.find('div', class_='s-prose js-post-body')
        body = body_tag.get_text().strip() if body_tag else "No body found"
        
        score_tag = soup.find('div', class_='js-vote-count')
        score = int(score_tag['data-value']) if score_tag else 0
        
        question_id_tag = soup.find('div', {'data-questionid': True})
        question_id = int(question_id_tag['data-questionid']) if question_id_tag else None
        
        creation_date = parse_date(soup.find('time', itemprop='dateCreated')['datetime'])
        
        last_edit_date_tag = soup.find('span', class_='relativetime')
        last_edit_date = parse_date(last_edit_date_tag['title']) if last_edit_date_tag else None
        
        timeline_url = f"{BASE_URL}/posts/{answer_id}/timeline"
        timeline_response = make_request_with_retries(timeline_url)

        if timeline_response and timeline_response.status_code == 200:
            timeline_soup = BeautifulSoup(timeline_response.text, 'html.parser')
            last_activity_tag = timeline_soup.find('span', class_='relativetime')
            last_activity_date = parse_date(last_activity_tag['title']) if last_activity_tag else creation_date
        else:
            last_activity_date = last_edit_date if last_edit_date else creation_date

        logger.debug(f"Timeline dates for answer ID {answer_id}: Last edit: {last_edit_date}, Last activity: {last_activity_date}")

        is_accepted = bool(soup.find('div', class_='accepted-answer'))
        logger.debug(f"Is answer ID {answer_id} accepted? {is_accepted}")

        user_cards = soup.find_all('div', class_='user-details')
        if len(user_cards) > 1:
            user_card = user_cards[1]
        else:
            user_card = user_cards[0]

        username = user_card.find('a').text.strip() if user_card.find('a') else "Unknown"
        user_gravatar = soup.find('div', class_='user-gravatar32')
        user_profile_image = user_gravatar.find('img')['src'] if user_gravatar and user_gravatar.find('img') else ""

        user_link = BASE_URL + user_card.find('a')['href'] if user_card.find('a') else ""
        user_id, account_id = scrape_user_profile(user_link) if user_link else (None, None)
        user_reputation_tag = user_card.find('span', class_='reputation-score')
        user_reputation = parse_reputation(user_reputation_tag.text.strip()) if user_reputation_tag else 0
        logger.debug(f"User for answer ID {answer_id}: {username} (ID: {user_id}, Account ID: {account_id}) with reputation {user_reputation}")

        answer_data = {
            'answer_id': int(answer_id),
            'question_id': question_id,
            'score': score,
            'creation_date': creation_date,
            'last_activity_date': last_activity_date,
            'last_edit_date': last_edit_date,
            'is_accepted': is_accepted,
            'owner': {
                'account_id': account_id,
                'reputation': user_reputation,
                'user_id': user_id,
                'user_type': 'registered',
                'profile_image': user_profile_image,
                'display_name': username,
                'link': user_link
            },
            'content_license': "CC BY-SA 4.0",
            'body': body
        }
        
        return answer_data
    except Exception as e:
        logger.error(f"Error processing answer ID {answer_id}: {e}")
        return None


def scrape_answers_from_question_soup(soup, question_id):
    """Scrape answers from a question's page soup."""
    logger.debug(f"Scraping answers from the question page for ID: {question_id}")
    answers = []
    answer_summaries = soup.find_all('div', class_='answer')
    logger.debug(f"Found {len(answer_summaries)} answer summaries on the page.")

    for summary in answer_summaries:
        try:
            answer_id = int(summary['data-answerid'])
            logger.debug(f"Processing answer ID: {answer_id}")

            score_tag = summary.find('div', class_='js-vote-count')
            score = int(score_tag.get_text().strip()) if score_tag else 0
            logger.debug(f"Answer ID: {answer_id} has a score of {score}")

            creation_date_tag = summary.find('time', itemprop='dateCreated')
            creation_date = parse_date(creation_date_tag['datetime']) if creation_date_tag else None
            logger.debug(f"Creation date for answer ID {answer_id}: {creation_date}")

            last_edit_date_tag = summary.find('span', class_='relativetime')
            last_edit_date = parse_date(last_edit_date_tag['title']) if last_edit_date_tag else None

            timeline_url = f"{BASE_URL}/posts/{answer_id}/timeline"
            timeline_response = make_request_with_retries(timeline_url)

            if timeline_response and timeline_response.status_code == 200:
                timeline_soup = BeautifulSoup(timeline_response.text, 'html.parser')
                last_activity_tag = timeline_soup.find('span', class_='relativetime')
                last_activity_date = parse_date(last_activity_tag['title']) if last_activity_tag else creation_date
            else:
                last_activity_date = last_edit_date if last_edit_date else creation_date

            logger.debug(f"Timeline dates for answer ID {answer_id}: Last edit: {last_edit_date}, Last activity: {last_activity_date}")

            is_accepted = 'accepted-answer' in summary['class']
            logger.debug(f"Is answer ID {answer_id} accepted? {is_accepted}")

            user_cards = summary.find_all('div', class_='user-details')
            if len(user_cards) > 1:
                user_card = user_cards[1]
            else:
                user_card = user_cards[0]

            username = user_card.find('a').text.strip() if user_card.find('a') else "Unknown"
            user_gravatar = summary.find('div', class_='user-gravatar32')
            user_profile_image = user_gravatar.find('img')['src'] if user_gravatar and user_gravatar.find('img') else ""

            user_link = BASE_URL + user_card.find('a')['href'] if user_card.find('a') else ""
            user_id, account_id = scrape_user_profile(user_link) if user_link else (None, None)
            user_reputation_tag = user_card.find('span', class_='reputation-score')
            user_reputation = parse_reputation(user_reputation_tag.text.strip()) if user_reputation_tag else 0
            logger.debug(f"User for answer ID {answer_id}: {username} (ID: {user_id}, Account ID: {account_id}) with reputation {user_reputation}")

            body_tag = summary.find('div', class_='s-prose js-post-body')
            body = body_tag.get_text().strip() if body_tag else "No body found"
            logger.debug(f"Body length for answer ID {answer_id}: {len(body)} characters")

            answer_data = {
                'answer_id': answer_id,
                'question_id': int(question_id),
                'score': score,
                'creation_date': creation_date,
                'last_activity_date': last_activity_date,
                'last_edit_date': last_edit_date,
                'is_accepted': is_accepted,
                'owner': {
                    'account_id': account_id,
                    'reputation': user_reputation,
                    'user_id': user_id,
                    'user_type': 'registered',
                    'profile_image': user_profile_image,
                    'display_name': username,
                    'link': user_link
                },
                'content_license': "CC BY-SA 4.0",
                'body': body
            }

            answers.append(answer_data)
        except Exception as e:
            logger.error(f"Error processing answer for question ID {question_id}: {e}")

    logger.debug(f"Total answers scraped for question ID {question_id}: {len(answers)}")
    return answers
