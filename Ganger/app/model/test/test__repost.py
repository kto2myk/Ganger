from Ganger.app.model.post.post_manager import PostManager  
from Ganger.app.view.app import app
from Ganger.app.model.model_manager.model import Repost
from Ganger.app.model.database_manager.db_creator import TableManager
from Ganger.app.model.database_manager.database_manager import DatabaseManager
# db_manager = TableManager()
# try:
#     db_manager.drop_table(table_name="reposts")
#     print("Deleted repost")
# except Exception as e: 
#     print(e)
#     print("Failed to delete repost")
# テーブル削除
with app.app_context():
    try:
        db_manager = DatabaseManager()
        db_manager.delete(Repost, {"post_id":9})
        print("Deleted repost")
    except Exception as e:
        print(e)
        print("Failed to create repost table")
# テーブル作成
    # try:
    #     post_manager = PostManager()
    #     post = post_manager.create_repost(
    #         user_id=4,
    #         post_id=9,
    #     )
    #     print(post)
    # except Exception as e:
    #     print(e)
    #     print("Failed to create repost")


