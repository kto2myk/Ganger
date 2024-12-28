from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import Post
db_manager = DatabaseManager()
try:
    db_manager.delete(Post, {"post_id": 1})
    print("削除成功")
except Exception as e:
    print(f"削除失敗: {e}")