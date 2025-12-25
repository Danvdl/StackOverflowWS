import logging
from bs4 import BeautifulSoup
from app.utils import make_request_with_retries, parse_reputation, parse_date, parse_view_count, clean_question_body
from app.scrapers.users import scrape_user_profile

logger = logging.getLogger(__name__)

BASE_URL = "https://stackoverflow.com"


def scrape_last_activity_date(soup):
    """Scrape the last activity date of a question."""
    last_activity_tag = soup.find('a', class_='s-link s-link__inherit', title=True, href=lambda x: 'lastactivity' in x)
    
    if last_activity_tag and last_activity_tag.has_attr('title'):
        last_activity_date_str = last_activity_tag['title']
        return parse_date(last_activity_date_str)
    else:
        logger.debug("Last activity date not found.")
        return None


def scrape_question_details(question_id):
    """Scrape the details of a question."""
    question_url = f"{BASE_URL}/questions/{question_id}"
    response = make_request_with_retries(question_url)
    
    if response is None or response.status_code != 200:
        logger.debug(f"Failed to fetch question details for ID {question_id}")
        return None, None, None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    creation_date_tag = soup.find('time', itemprop='dateCreated')
    if creation_date_tag and creation_date_tag.has_attr('datetime'):
        creation_date_str = creation_date_tag['datetime']
        creation_date = parse_date(creation_date_str.replace('T', ' ').replace('Z', ''))
    else:
        logger.debug(f"Creation date not found for question ID: {question_id}")
        creation_date = None
    
    last_activity_date = scrape_last_activity_date(soup)
    
    body_tag = soup.find('div', class_='s-prose js-post-body')
    if body_tag:
        body = clean_question_body(body_tag.get_text().strip())
    else:
        logger.debug(f"Body of the question not found for question ID: {question_id}")
        body = None
    
    return creation_date, last_activity_date, body


def scrape_questions(html_content):
    """Scrape questions from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    questions = []

    question_summaries = soup.find_all('div', class_='s-post-summary')
    
    for summary in question_summaries:
        try:
            question_id = int(summary['data-post-id'])
            logger.debug(f"Processing question ID: {question_id}")
            
            vote_count = int(summary.find('span', class_='s-post-summary--stats-item-number').text.strip())
            answer_count = int(summary.find_all('span', class_='s-post-summary--stats-item-number')[1].text.strip())
            
            title_tag = summary.find('h3', class_='s-post-summary--content-title').find('a')
            title = title_tag.text.strip()
            link = BASE_URL + title_tag['href']
            logger.debug(f"Title: {title}, Link: {link}")
            
            tags = [tag.text for tag in summary.find_all('a', class_='s-tag')]
            
            user_card = summary.find('div', class_='s-user-card')
            username = user_card.find('a', class_='flex--item').text.strip()
            user_reputation = parse_reputation(user_card.find('li', class_='s-user-card--rep').find('span').text.strip())
            user_profile_image = user_card.find('img', class_='s-avatar--image')['src']
            user_link = BASE_URL + user_card.find('a', class_='flex--item')['href']
            
            user_id, account_id = scrape_user_profile(user_link)
            if user_id is None or account_id is None:
                logger.debug(f"Missing user ID or account ID for user link: {user_link}")
            
            creation_date, last_activity_date, body = scrape_question_details(question_id)
            if creation_date is None:
                logger.debug(f"Missing creation date for question ID: {question_id}")
            
            is_answered = answer_count > 0
            view_count_tag = summary.find('div', class_='flex--item ws-nowrap mb8')

            if view_count_tag:
                view_count_str = view_count_tag.get_text().split()[0].strip()
                view_count = parse_view_count(view_count_str)
                logger.debug(f"View count found: {view_count}")
            else:
                logger.warning("View count not found, setting to 0.")
                view_count = 0
         
            question_data = {
                'question_id': question_id,
                'tags': tags,
                'owner': {
                    'account_id': account_id,
                    'reputation': user_reputation,
                    'user_id': user_id,
                    'user_type': 'registered',
                    'profile_image': user_profile_image,
                    'display_name': username,
                    'link': user_link
                },
                'is_answered': is_answered,
                'view_count': view_count,
                'answer_count': answer_count,
                'score': vote_count,
                'last_activity_date': last_activity_date,
                'creation_date': creation_date,
                'title': title,
                'link': link,
                'content_license': "CC BY-SA 4.0",
                'body': body
            }
            
            community_wiki_tag = summary.find('span', class_='community-wiki')
            if community_wiki_tag and 'title' in community_wiki_tag.attrs:
                community_owned_date_str = community_wiki_tag['title'].split("as of ")[1]
                community_owned_date = parse_date(community_owned_date_str)
                question_data['community_owned_date'] = community_owned_date

            closed_notice = summary.find('aside', class_='s-notice s-notice__info post-notice js-post-notice mb16')
            if closed_notice:
                logger.debug(f"Question {question_id} is closed.")
                closed_reason = closed_notice.get_text(strip=True).split('.')[1].strip()
                close_date_tag = closed_notice.find('span', class_='relativetime')
                if close_date_tag and close_date_tag.has_attr('title'):
                    closed_date_str = close_date_tag['title']
                    closed_date = parse_date(closed_date_str.replace('T', ' ').replace('Z', ''))
                    question_data['closed_reason'] = closed_reason
                    question_data['closed_date'] = closed_date

            questions.append(question_data)
        
        except Exception as e:
            logger.debug(f"Error processing question summary: {e}")
    
    return questions


def scrape_question_by_id(question_id):
    """Scrape a question by its ID."""
    question_url = f"{BASE_URL}/questions/{question_id}"
    logger.debug(f"Fetching question details from URL: {question_url}")
    response = make_request_with_retries(question_url)
    
    if response is None or response.status_code != 200:
        logger.error(f"Failed to fetch question details for ID {question_id}")
        return None
    
    logger.debug("Successfully fetched the question page.")
    soup = BeautifulSoup(response.text, 'html.parser')
    
    creation_date_tag = soup.find('time', itemprop='dateCreated')
    if creation_date_tag and creation_date_tag.has_attr('datetime'):
        creation_date_str = creation_date_tag['datetime']
        creation_date = parse_date(creation_date_str.replace('T', ' ').replace('Z', ''))
        logger.debug(f"Found creation date: {creation_date_str}")
    else:
        logger.warning("Creation date not found.")
        creation_date = None
    
    last_activity_date = scrape_last_activity_date(soup)
    logger.debug(f"Last activity date: {last_activity_date}")
    
    body_tag = soup.find('div', class_='s-prose js-post-body')
    if body_tag:
        body = clean_question_body(body_tag.get_text().strip())
        logger.debug(f"Question body found with length {len(body)} characters.")
    else:
        logger.warning("Body of the question not found.")
        body = None
    
    title_tag = soup.find('a', class_='question-hyperlink')
    if title_tag:
        title = title_tag.text.strip()
        logger.debug(f"Title found: {title}")
    else:
        logger.warning("Title not found.")
        title = "No title found"
    
    score_tag = soup.find('div', class_='js-vote-count')
    if score_tag and score_tag.has_attr('data-value'):
        score = int(score_tag['data-value'])
        logger.debug(f"Score (votes) found: {score}")
    else:
        logger.warning("Score not found, setting to 0.")
        score = 0
  
    tags = list(set(tag.text for tag in soup.find_all('a', class_='post-tag')))
    logger.debug(f"Tags found: {tags}")
    
    view_count_tag = soup.find('div', class_='flex--item ws-nowrap mb8')
    if view_count_tag:
        view_count_str = view_count_tag.get_text().strip()
        view_count_number = view_count_str.split()[1].replace(',', '').replace('k', '000').replace('m', '000000')
        try:
            view_count = int(view_count_number)
        except ValueError:
            logger.warning(f"Failed to parse view count: {view_count_str}, defaulting to 0.")
            view_count = 0
        logger.debug(f"View count found: {view_count}")
    else:
        logger.warning("View count not found, setting to 0.")
        view_count = 0

    answer_count_tag = soup.find('h2', class_='mb0')
    if answer_count_tag and answer_count_tag.has_attr('data-answercount'):
        answer_count = int(answer_count_tag['data-answercount'])
        logger.debug(f"Answer count found: {answer_count}")
    else:
        logger.warning("Answer count not found, setting to 0.")
        answer_count = 0
    
    is_answered = soup.find('div', class_='js-accepted-answer-indicator') is not None
    logger.debug(f"Is the question answered? {is_answered}")
    
    user_card = soup.find('div', class_='user-details')
    if user_card:
        username_tag = user_card.find('a')
        username = username_tag.text.strip() if username_tag else "Unknown"
        user_link = BASE_URL + username_tag['href'] if username_tag else ""
        logger.debug(f"Username: {username}, User link: {user_link}")
        reputation_tag = user_card.find('span', class_='reputation-score')
        user_reputation = parse_reputation(reputation_tag.text.strip()) if reputation_tag else 0
        
        profile_image_tag = soup.find('div', class_='gravatar-wrapper-32')
        if profile_image_tag:
            user_profile_image = profile_image_tag.find('img')['src'] if profile_image_tag.find('img') else ""
        else:
            user_profile_image = ""
        
        user_id, account_id = scrape_user_profile(user_link) if user_link else (None, None)
        logger.debug(f"User ID: {user_id}, Account ID: {account_id}")
    else:
        logger.warning("User details not found.")
        username = "Unknown"
        user_reputation = 0
        user_profile_image = ""
        user_link = ""
        user_id, account_id = None, None
    
    question = {
        'question_id': question_id,
        'creation_date': creation_date,
        'last_activity_date': last_activity_date,
        'body': body,
        'title': title,
        'score': score,
        'tags': tags,
        'owner': {
            'account_id': account_id,
            'reputation': user_reputation,
            'user_id': user_id,
            'user_type': 'registered',
            'profile_image': user_profile_image,
            'display_name': username,
            'link': user_link
        },
        'link': question_url,
        'is_answered': is_answered,
        'view_count': view_count,
        'answer_count': answer_count,
        'content_license': "CC BY-SA 4.0"
    }
    
    closed_notice = soup.find('aside', class_='s-notice s-notice__info post-notice js-post-notice mb16')
    if closed_notice:
        logger.debug(f"Question {question_id} is closed.")
        closed_reason = closed_notice.get_text(strip=True).split('.')[1].strip()
        close_date_tag = closed_notice.find('span', class_='relativetime')
        if close_date_tag and close_date_tag.has_attr('title'):
            closed_date_str = close_date_tag['title']
            closed_date = parse_date(closed_date_str.replace('T', ' ').replace('Z', ''))
            question['closed_reason'] = closed_reason
            question['closed_date'] = closed_date
            logger.debug(f"Closed reason: {closed_reason}, Closed date: {closed_date}")

    return question
