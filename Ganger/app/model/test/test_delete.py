from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.database_manager.db_creator import TableManager
from Ganger.app.view.app import app
from Ganger.app.model.model_manager.model import Post,User
with app.test_request_context():
    # データ削除
    db_manager = DatabaseManager(app)
    try:
        db_manager.delete(User, {"id": 35})
        print("削除成功")
    except Exception as e:
        print(f"削除失敗: {e}")

    # # テーブル削除
    #     db_manager = TableManager()
    # try:
    #     table_name = "blocks"
    #     db_manager.drop_table(table_name=table_name)
    #     print(f"Deleted {table_name}")
    # except Exception as e: 
    #     print(e)
    #     print(f"Failed to delete{table_name}")
