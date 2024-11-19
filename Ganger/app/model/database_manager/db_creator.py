import os
from sqlalchemy.exc import SQLAlchemyError
from Ganger.app.model.database_manager.database_connector import DatabaseConnector

class TableCreator(DatabaseConnector):
    """
    テーブルを作成するためのクラス。
    DatabaseConnectorを継承して、データベース接続とテーブル作成を行う。
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
        # データベースのパスからディレクトリ部分を取得
        folder_path = os.path.dirname(self._DatabaseConnector__db_url.replace("sqlite:///", ""))
        
        # フォルダが存在しない場合、作成する
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
            # Baseのメタデータを使ってテーブルを作成
            Base.metadata.create_all(self.engine)
            print("Tables created successfully.")  # 成功メッセージ
        except SQLAlchemyError as e:
            # SQLAlchemyのエラーが発生した場合にエラーメッセージを出力
            print(f"Error while creating tables: {e}")
            raise  # エラーを再スローすることで、呼び出し元での処理を可能にする

# `if __name__ == "__main__":` で直接実行時に処理を行う部分
if __name__ == "__main__":
    # Baseをインポート。これにより、テーブルの構造を定義したモデルが使える。
    from Ganger.app.model.model_manager import Base
    
    # TableCreatorインスタンスを作成
    table_creator = TableCreator()  # データベース接続とフォルダ確認が行われる

    # テーブルを作成するメソッドを呼び出す
    table_creator.create_tables(Base)  # テーブル作成処理が実行される
