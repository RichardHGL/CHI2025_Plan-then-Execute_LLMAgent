import os

from flask import Flask, g, jsonify
# from flask.ext.bootstrap import Bootstrap
from flask_bootstrap import Bootstrap5
import logging
import os

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
        BOOTSTRAP_BOOTSWATCH_THEME='cerulean'
    )
    app.config['ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TESTING'] = True
    
    handler = logging.FileHandler('flask.log', encoding='UTF-8')
    handler.setLevel(logging.INFO)
    logging_format = logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
    handler.setFormatter(logging_format)
    app.logger.addHandler(handler)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import planning_agent
    app.register_blueprint(planning_agent.plan_bp)

    from flask import redirect, url_for, session, render_template, request

    # a simple page that says hello
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    bootstrap = Bootstrap5(app)

    return app
