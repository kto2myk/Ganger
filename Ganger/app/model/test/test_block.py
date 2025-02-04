from Ganger.app.model.user.user_table import UserManager
from Ganger.app.view.app import app

with app.test_request_context():
    try:
        user_manager = UserManager()
        result = user_manager.toggle_block(
            user_id=3,
            blocked_user_id=4)
        app.logger.info(result)
    except Exception as e:
        app.logger.error(e)