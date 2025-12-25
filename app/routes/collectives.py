from flask import Blueprint, jsonify, request
import logging

from app.scrapers import scrape_collectives

logger = logging.getLogger(__name__)

bp = Blueprint('collectives', __name__)


@bp.route('/collectives', methods=['GET'])
def get_collectives():
    collectives = scrape_collectives()
    
    if collectives is None:
        return jsonify({"error": "Failed to retrieve collectives"}), 500
    
    sort_order = request.args.get('sort', 'asc').lower()
    if sort_order == 'asc':
        collectives = sorted(collectives, key=lambda x: x['name'])
    elif sort_order == 'desc':
        collectives = sorted(collectives, key=lambda x: x['name'], reverse=True)
    
    return jsonify({"items": collectives})
