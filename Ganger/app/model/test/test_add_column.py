from Ganger.app.model.database_manager.db_creator import TableManager
# 使用例
try:
    db_manager = TableManager()  # SQLiteを使用
    result = db_manager.add_column_to_table(
        table_name="likes",
        column_name="created_at",
        column_type="DATETIME",
        default="CURRENT_TIMESTAMP",  # デフォルト値としてCURRENT_TIMESTAMPを直接渡す
        nullable=False
    )
    print(result)
except Exception as e:
    print(f"エラー: {e}")

