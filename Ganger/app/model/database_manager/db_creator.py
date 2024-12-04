import os
from sqlalchemy.exc import SQLAlchemyError
from Ganger.app.model.database_manager.database_connector import DatabaseConnector

class TableManager(DatabaseConnector):
    """
    テーブルを管理するためのクラス。
    DatabaseConnectorを継承して、データベース接続、テーブル作成、削除を行う。
    """
    def __init__(self, db_url="sqlite:///C:/HAL/IH/IH22/Ganger/app/model/database_manager/Ganger.db", echo=False):
        """
        コンストラクタ
        :param db_url: データベースのURL（デフォルトは固定のパス）
        :param echo: SQLAlchemyのSQLログを出力するかどうか（デバッグ用）
        """
        super().__init__(db_url=db_url, echo=echo)  # DatabaseConnectorを初期化
        self._ensure_folder_exists()  # フォルダが存在しない場合に作成

    def _ensure_folder_exists(self):
        """
        データベースの保存先フォルダが存在するか確認し、存在しない場合は作成する。
        """
        folder_path = os.path.dirname(self._DatabaseConnector__db_url.replace("sqlite:///", ""))
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created folder: {folder_path}")
        else:
            print(f"Folder already exists: {folder_path}")

    def create_tables(self, Base):
        """
        データベースにテーブルを作成する。
        :param Base: SQLAlchemyのBaseクラス。全てのORMモデルがこのBaseを継承する。
        """
        try:
            Base.metadata.create_all(self.engine)
            print("Tables created successfully.")
        except SQLAlchemyError as e:
            print(f"Error while creating tables: {e}")
            raise

    def drop_tables(self, Base):
        """
        データベース内の全てのテーブルを削除する。
        :param Base: SQLAlchemyのBaseクラス。全てのORMモデルがこのBaseを継承する。
        """
        try:
            Base.metadata.drop_all(self.engine)
            print("Tables dropped successfully.")
        except SQLAlchemyError as e:
            print(f"Error while dropping tables: {e}")
            raise

# `if __name__ == "__main__":` で直接実行時に処理を行う部分
if __name__ == "__main__":
    from Ganger.app.model.model_manager import *

    # TableManagerインスタンスを作成
    table_manager = TableManager()  # データベース接続とフォルダ確認が行われる

    table_manager.create_tables(Base)  
