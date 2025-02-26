import os
from sqlalchemy.exc import SQLAlchemyError
from ErrorManager.models import Base
from ErrorManager.table.table_connector import TableConnector

class TableCreator(TableConnector):
    def __init__(self, echo=False, folder_path=None):
        self.__folder_path = folder_path or "C:/HAL/IH/IH22/ErrorManager/table"
        self.__db_url = f"sqlite:///{self.__folder_path}/error_logs.db"

        # フォルダ作成処理
        self._ensure_folder_exists()

        # 親クラス初期化
        super().__init__(echo=echo)

    def _ensure_folder_exists(self):
        if not os.path.exists(self.__folder_path):
            os.makedirs(self.__folder_path)
            print(f"フォルダを作成しました: {self.__folder_path}")
        else:
            print(f"フォルダは既に存在します: {self.__folder_path}")

    def create_tables(self):
        try:
            Base.metadata.create_all(self.engine)
            print("テーブルの作成が完了しました。")
        except SQLAlchemyError as e:
            print(f"テーブル作成中にエラーが発生しました: {e}")

    def drop_tables(self):
        try:
            Base.metadata.drop_all(self.engine)
            print("テーブルの削除が完了しました。")
        except SQLAlchemyError as e:
            print(f"テーブル削除中にエラーが発生しました: {e}")

if __name__ == "__main__":
    creator = TableCreator()
    creator.drop_tables()
    creator.create_tables()
