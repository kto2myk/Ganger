from Ganger.app.view.app import app
from Ganger.app.model.database_manager.database_manager import DatabaseManager

with app.test_request_context():
    try:
        db_manager = DatabaseManager(app)
        for trending in db_manager.trending:
            data = db_manager.redis.get_ranking_ids(ranking_key=trending)
            app.logger.info(f"key = {trending}")
            app.logger.info(data)
    except Exception as e:
        app.logger.info(e)