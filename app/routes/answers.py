from flask import Blueprint, jsonify, request
from bs4 import BeautifulSoup
import logging

from app.utils import make_request_with_retries, parse_date
from app.scrapers import scrape_answer_by_id, scrape_answers_from_question_soup

logger = logging.getLogger(__name__)

bp = Blueprint('answers', __name__)


@bp.route('/answers/<string:ids>', methods=['GET'])
def get_answers_by_ids(ids):
    """Retrieve a list of Answer objects identified by ids."""
    answer_ids = ids.split(',')
    answers = []

    sort = request.args.get('sort', 'activity')
    min_date = request.args.get('min')
    max_date = request.args.get('max')
    from_date = request.args.get('fromdate')
    to_date = request.args.get('todate')

    min_timestamp = parse_date(min_date) if min_date else None
    max_timestamp = parse_date(max_date) if max_date else None
    from_timestamp = parse_date(from_date) if from_date else None
    to_timestamp = parse_date(to_date) if to_date else None

    for answer_id in answer_ids:
        answer_data = scrape_answer_by_id(answer_id)
        if answer_data:
            if (min_timestamp and answer_data['last_activity_date'] < min_timestamp) or \
               (max_timestamp and answer_data['last_activity_date'] > max_timestamp) or \
               (from_timestamp and answer_data['creation_date'] < from_timestamp) or \
               (to_timestamp and answer_data['creation_date'] > to_timestamp):
                continue
            answers.append(answer_data)
        else:
            logger.error(f"Failed to retrieve answer with ID: {answer_id}")

    if sort == 'activity':
        answers.sort(key=lambda x: x['last_activity_date'], reverse=True)
    elif sort == 'creation':
        answers.sort(key=lambda x: x['creation_date'], reverse=True)
    elif sort == 'votes':
        answers.sort(key=lambda x: x['score'], reverse=True)
    else:
        logger.warning(f"Unknown sort parameter: {sort}. Defaulting to sort by activity.")
        answers.sort(key=lambda x: x['last_activity_date'], reverse=True)

    return jsonify({"items": answers})


@bp.route('/questions/<string:ids>/answers', methods=['GET'])
def get_answers_by_question_ids(ids):
    """Retrieve a list of Answer objects for given question ids."""
    question_ids = ids.split(',')
    all_answers = []

    sort = request.args.get('sort', 'activity')
    order = request.args.get('order', 'desc')
    min_value = request.args.get('min', None)
    max_value = request.args.get('max', None)
    fromdate = request.args.get('fromdate', None)
    todate = request.args.get('todate', None)

    logger.debug(f"Received request to retrieve answers for question IDs: {question_ids}")
    logger.debug(f"Sorting by: {sort}, Order: {order}, Min: {min_value}, Max: {max_value}, From: {fromdate}, To: {todate}")

    for question_id in question_ids:
        logger.debug(f"Processing question ID: {question_id}")
        question_url = f"https://stackoverflow.com/questions/{question_id}"
        response = make_request_with_retries(question_url)

        if response is None or response.status_code != 200:
            logger.error(f"Failed to retrieve question with ID: {question_id}")
            continue

        logger.debug(f"Successfully retrieved question page for ID: {question_id}")
        soup = BeautifulSoup(response.text, 'html.parser')
        answers = scrape_answers_from_question_soup(soup, question_id)
        logger.debug(f"Found {len(answers)} answers for question ID: {question_id}")
        all_answers.extend(answers)

    # Filter answers based on min/max values
    if min_value or max_value:
        min_value = int(min_value) if min_value else None
        max_value = int(max_value) if max_value else None

        if sort == 'votes':
            all_answers = [a for a in all_answers if (min_value is None or a['score'] >= min_value) and (max_value is None or a['score'] <= max_value)]
        elif sort in ['activity', 'creation']:
            key = 'last_activity_date' if sort == 'activity' else 'creation_date'
            all_answers = [a for a in all_answers if (min_value is None or a[key] >= min_value) and (max_value is None or a[key] <= max_value)]

    if fromdate:
        fromdate = int(fromdate)
        all_answers = [a for a in all_answers if a['creation_date'] >= fromdate]
    if todate:
        todate = int(todate)
        all_answers = [a for a in all_answers if a['creation_date'] <= todate]

    if sort == 'activity':
        all_answers.sort(key=lambda x: x['last_activity_date'], reverse=(order == 'desc'))
    elif sort == 'creation':
        all_answers.sort(key=lambda x: x['creation_date'], reverse=(order == 'desc'))
    elif sort == 'votes':
        all_answers.sort(key=lambda x: x['score'], reverse=(order == 'desc'))

    logger.debug(f"Total answers after filtering and sorting: {len(all_answers)}")
    return jsonify({"items": all_answers})
