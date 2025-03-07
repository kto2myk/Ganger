from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import MetaData, text
import sqlite3

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
            Base.metadata.create_all(self.engine())
            print("Tables created successfully.")
        except SQLAlchemyError as e:
            print(f"Error while creating tables: {e}")
            raise

    def drop_table(self,table_name):
        """
        指定したテーブルを削除する。

        Args:
            engine: SQLAlchemyのエンジンオブジェクト
            table_name: 削除するテーブル名
        """
        try:
            meta = MetaData()
            meta.reflect(bind=self.engine())
            
            if table_name in meta.tables:
                table = meta.tables[table_name]
                table.drop(self.engine())
                print(f"Table '{table_name}' has been dropped.")
            else:
                print(f"Table '{table_name}' does not exist.")
        except Exception as e:
            print(f"Failed to drop table '{table_name}': {e}")


    def drop_tables(self, Base) -> None:
        """
        データベース内の全てのテーブルを削除する。
        :param Base: SQLAlchemyのBaseクラス。全てのORMモデルがこのBaseを継承する。
        """
        try:
            Base.metadata.drop_all(self.engine())
            print("Tables dropped successfully.")
        except SQLAlchemyError as e:
            print(f"Error while dropping tables: {e}")
            raise


    def add_column_to_table(self, table_name, column_name, column_type, default=None, nullable=True):
        try:
            # 生SQLを直接構築
            sql = f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'
            if default is not None:
                sql += f" DEFAULT {default}"  # デフォルト値を直接埋め込む
            if not nullable:
                sql += " NOT NULL"

            # データベース接続でSQL文を実行
            with self.engine().connect() as conn:
                conn.execute(text(sql))
                return f"カラム '{column_name}' をテーブル '{table_name}' に追加しました。"

        except SQLAlchemyError as e:
            return f"エラーが発生しました: {e}"
    
    def check_columns(self,table_name,database_path="Ganger/app/model/database_manager/Ganger.db"):
        """
        指定したSQLiteデータベースのテーブルのカラム情報を取得する
        """
        try:
            # SQLiteデータベースに接続
            conn = sqlite3.connect(database_path)
            cursor = conn.cursor()

            # PRAGMA table_info を使ってカラム情報を取得
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()

            # カラム情報を表示
            if columns:
                print(f"テーブル '{table_name}' のカラム情報:")
                for col in columns:
                    print(f"  - {col[1]} (型: {col[2]})")
            else:
                print(f"テーブル '{table_name}' が見つかりません。")

            # 接続を閉じる
            conn.close()
        except sqlite3.Error as e:
            print(f"エラー: {e}")

                
# `if __name__ == "__main__":` で直接実行時に処理を行う部分
if __name__ == "__main__":
    from Ganger.app.model.model_manager import Base  # 必要なモデルをインポート

    # TableManagerインスタンスを作成
    table_manager = TableManager()
    # table_manager.drop_table(table_name="sales_items")
    # テーブル作成
    table_manager.drop_tables(Base)
    table_manager.create_tables(Base)

    conn = None
    try:
        conn = table_manager.engine().raw_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        result = cursor.fetchone()
        print("Foreign keys enabled:", result[0])  # 1 が返れば有効
    finally:
        if conn:
            conn.close()