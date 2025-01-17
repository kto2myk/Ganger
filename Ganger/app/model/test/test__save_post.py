from Ganger.app.model.post.post_manager import PostManager
from Ganger.app.model.model_manager.model import SavedPost
from Ganger.app.view.app import app
with app.app_context():
    try:
        post_manager = PostManager()
        save_post = post_manager.toggle_saved_post(
            user_id=1,
            post_id=2
        )
        app.logger.info("成功")
    except Exception as e:
        app.logger.error("失敗", str(e))
