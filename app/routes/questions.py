from datetime import datetime
from flask import Blueprint, jsonify, request
import logging

from app.utils import make_request_with_retries
from app.scrapers import scrape_questions, scrape_question_by_id

logger = logging.getLogger(__name__)

bp = Blueprint('questions', __name__)


@bp.route('/questions', methods=['GET'])
def get_questions():
    url = "https://stackoverflow.com/questions"
    response = make_request_with_retries(url)

    if not response:
        logger.error("Failed to retrieve data after retries.")
        return jsonify({"error": "Failed to retrieve data after retries"}), 429

    logger.debug("Successfully retrieved data from StackOverflow.")
    questions = scrape_questions(response.text)
    logger.debug(f"Scraped {len(questions)} questions from StackOverflow.")

    # Apply filtering by min and max
    min_value = request.args.get('min', type=int)
    max_value = request.args.get('max', type=int)
    if min_value is not None:
        logger.debug(f"Applying minimum score filter: {min_value}")
        questions = [q for q in questions if q['score'] >= min_value]
        logger.debug(f"Number of questions after min filter: {len(questions)}")
    if max_value is not None:
        logger.debug(f"Applying maximum score filter: {max_value}")
        questions = [q for q in questions if q['score'] <= max_value]
        logger.debug(f"Number of questions after max filter: {len(questions)}")

    # Apply filtering by tags
    tagged = request.args.get('tagged')
    if tagged:
        tags = tagged.split(',')
        logger.debug(f"Filtering by tags: {tags}")
        questions = [q for q in questions if any(tag in q['tags'] for tag in tags)]
        logger.debug(f"Number of questions after tag filter: {len(questions)}")

    # Sorting by specified sort parameter
    sort_by = request.args.get('sort', 'last_activity_date')
    order = request.args.get('order', 'desc').lower()

    reverse_order = (order == 'desc')
    if sort_by == 'creation_date':
        logger.debug("Sorting questions by creation_date")
        questions = sorted(questions, key=lambda x: x['creation_date'] if x['creation_date'] else 0, reverse=reverse_order)
    elif sort_by == 'last_activity_date':
        logger.debug("Sorting questions by last_activity_date")
        questions = sorted(questions, key=lambda x: x['last_activity_date'] if x['last_activity_date'] else 0, reverse=reverse_order)
    else:
        logger.warning(f"Unknown sort parameter: {sort_by}")

    # Filtering by fromdate and todate
    fromdate = request.args.get('fromdate', type=int)
    todate = request.args.get('todate', type=int)
    if fromdate is not None:
        questions = [q for q in questions if q['creation_date'] >= fromdate]
    if todate is not None:
        questions = [q for q in questions if q['creation_date'] <= todate]
    
    logger.debug(f"Number of questions after date filtering: {len(questions)}")

    # Apply built-in filters
    filter_type = request.args.get('filter', 'default')
    if filter_type == 'default':
        pass
    elif filter_type == 'withbody':
        questions = [q for q in questions if q['body']]
        logger.debug(f"Number of questions after body filter: {len(questions)}")
    elif filter_type == 'total':
        questions = [{'total': len(questions)}]
    elif filter_type == 'all':
        pass
    else:
        logger.warning(f"Unknown filter type: {filter_type}")

    # Implement paging
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('pagesize', 30, type=int)
    start = (page - 1) * page_size
    end = start + page_size

    if start >= len(questions):
        paged_questions = []
    else:
        paged_questions = questions[start:end]

    logger.debug(f"Returning page {page} with page size {page_size}, containing {len(paged_questions)} questions.")

    return jsonify({"items": paged_questions, "page": page, "pagesize": page_size, "total": len(questions)})


@bp.route('/questions/<ids>', methods=['GET'])
def get_questions_by_id(ids):
    question_ids = ids.split(',')
    questions = []
    
    sort_by = request.args.get('sort', 'activity')
    min_value = request.args.get('min')
    max_value = request.args.get('max')
    from_date = request.args.get('fromdate')
    to_date = request.args.get('todate')

    if from_date:
        from_date = datetime.strptime(from_date, '%Y-%m-%d')
    if to_date:
        to_date = datetime.strptime(to_date, '%Y-%m-%d')

    for question_id in question_ids:
        logger.debug(f"Fetching data for question ID {question_id}")
        question = scrape_question_by_id(question_id)
        
        if question:
            if min_value and question.get(sort_by, None) < int(min_value):
                continue
            if max_value and question.get(sort_by, None) > int(max_value):
                continue
            if from_date and datetime.strptime(question.get('creation_date'), '%Y-%m-%dT%H:%M:%S') < from_date:
                continue
            if to_date and datetime.strptime(question.get('creation_date'), '%Y-%m-%dT%H:%M:%S') > to_date:
                continue
            
            questions.append(question)
        else:
            logger.warning(f"No questions found for question ID {question_id}")
    
    questions.sort(key=lambda x: x.get(sort_by, None), reverse=(sort_by != 'creation'))

    return jsonify({"items": questions})
