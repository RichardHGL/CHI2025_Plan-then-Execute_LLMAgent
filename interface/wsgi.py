from flaskr import create_app
import logging

app = create_app()
# gunicorn_logger = logging.getLogger('gunicorn.error')
# app.logger.handlers = gunicorn_logger.handlers
# app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run()
