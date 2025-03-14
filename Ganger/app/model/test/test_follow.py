from Ganger.app.model.user.user_table import UserManager
from Ganger.app.view.app import app

with app.test_request_context():
    try:
        user_manager = UserManager()
        result = user_manager.toggle_follow(followed_user_id=5,sender_id=6
        )
        app.logger.info(result)
    except Exception as e:
        app.logger.error(f"Failed to toggle follow: {e}")
