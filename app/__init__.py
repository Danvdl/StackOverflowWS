from flask import Flask
import logging
import os

def create_app():
    app = Flask(__name__)
    app.logger.setLevel(logging.DEBUG)
    
    from app.routes import questions, answers, collectives
    app.register_blueprint(questions.bp)
    app.register_blueprint(answers.bp)
    app.register_blueprint(collectives.bp)
    
    @app.route('/')
    def home():
        return "Hello, Flask!"
    
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Not found"}, 404

    @app.errorhandler(400)
    def bad_request(error):
        return {"error": "Bad request"}, 400
    
    return app
