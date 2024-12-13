from sqlalchemy.exc import SQLAlchemyError
from Ganger.app.model.database_manager.database_manager import DatabaseConnector
import os

class TableManager(DatabaseConnector):
    """
    テーブルを管理するためのクラス。
    DatabaseConnectorを継承して、データベース接続、テーブル作成、削除を行う。
    """
    def create_tables(self, Base) -> None:
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

    def drop_tables(self, Base) -> None:
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
    from Ganger.app.model.model_manager import Base  # 必要なモデルをインポート

    # TableManagerインスタンスを作成
    table_manager = TableManager()

    # テーブル作成
    table_manager.create_tables(Base)