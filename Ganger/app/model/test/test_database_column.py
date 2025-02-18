from Ganger.app.model.database_manager.db_creator import TableManager
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.model_manager.model import Message
from Ganger.app.view.app import app
with app.test_request_context():
    try:
        # tb_manager = TableManager()
        # tb_manager.check_columns(table_name="messages")
        db = DatabaseManager()
        print(db.fetch(model=Message))

    except Exception as e:
        print(e)

# from sqlalchemy import create_engine, MetaData

# database_path = "Ganger.db"  # データベースのパス
# engine = create_engine(f"sqlite:///{database_path}")

# metadata = MetaData()
# metadata.reflect(bind=engine)

# # messages テーブルのカラムを取得
# messages_table = metadata.tables.get("messages")
# if messages_table:
#     print("SQLAlchemyが認識している messages テーブルのカラム:")
#     for column in messages_table.columns:
#         print(f"  - {column.name} (型: {column.type})")
# else:
#     print("messages テーブルが認識されていません！")
