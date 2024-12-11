import os
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

class DatabaseConnector:
    def __init__(self, db_relative_path="Ganger/app/model/database_manager/Ganger.db", echo=False):
        """
        コンストラクタ
        :param db_relative_path: プロジェクト内でのデータベースの相対パス
        :param echo: SQLAlchemyのSQLログを出力するかどうか
        """
        # プロジェクトルートからの絶対パスを固定
        self.__db_path = os.path.abspath(db_relative_path)
        self.__ensure_folder_exists()  # データベースフォルダの存在を確認・作成
        # データベースURLを設定
        self.__db_url = f"sqlite:///{self.__db_path}"
        # SQLAlchemyエンジンを作成
        self.__engine = create_engine(self.__db_url, echo=echo)

    def __ensure_folder_exists(self):
        """
        データベースの保存先フォルダが存在するか確認し、存在しない場合は作成する。
        """
        folder_path = os.path.dirname(self.__db_path)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"Created folder: {folder_path}")
        else:
            print(f"Folder already exists: {folder_path}")

    @property
    def engine(self):
        """
        データベースエンジンのインスタンスを返す。
        """
        return self.__engine