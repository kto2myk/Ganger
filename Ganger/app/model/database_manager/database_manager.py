import os
from sqlalchemy import create_engine,inspect
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from flask import session
from werkzeug.security import check_password_hash 
from Ganger.app.model.validator import Validator  # 検証用
from Ganger.app.model.model_manager.model import Base
from ErrorManager.error_manager import ErrorLogManager  #errorログ記録

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

    @property
    def engine(self):
        """
        データベースエンジンのインスタンスを返す。
        """
        return self.__engine
    



class DatabaseManager(DatabaseConnector):
    def __init__(self):
        super().__init__()
        self.__error_log_manager = ErrorLogManager()
    
    @property
    def error_log_manager(self):
        return self.__error_log_manager

    def insert(self, model, data, unique_check=None):
        """
        データ挿入（重複チェックあり）
        :param model: 操作対象のモデル
        :param data: 挿入するデータ（辞書型）
        :param unique_check: 一意性チェックの条件（辞書型）
        :return: 挿入されたインスタンス or None
        """
        try:
            with Session(self.engine) as session:
                # 一意性チェック
                if unique_check:
                    # fetch_oneを使用して重複チェック
                    existing = self.fetch_one(model=model, filters=unique_check)
                    if existing:
                        print("重複あり.")
                        return None
                
                # 新規データ挿入
                new_entry = model(**data)
                session.add(new_entry)

                # 辞書形式に変換（ローカル変数で管理）
                session.commit()
                db_dict = {
                    column.name: getattr(new_entry, column.name) for column in model.__table__.columns
                }

                return db_dict
            
        except SQLAlchemyError as e:
            self.__error_log_manager.add_error(None, str(e))
            return None
    
    def update(self, model, filters, data):
        """データ更新"""
        try:
            with Session(self.engine) as session:
                query = session.query(model).filter_by(**filters)
                if not query.first():
                    print("No matching entry found for update.")
                    return None
                query.update(data)
                session.commit()
                return query.first()
        except SQLAlchemyError as e:
            self.__error_log_manager.add_error(None, str(e))
            return None

    def delete(self, model, filters):
        """データ削除"""
        try:
            with Session(self.engine) as session:
                query = session.query(model).filter_by(**filters)
                deleted_count = query.delete()
                session.commit()
                return deleted_count
        except SQLAlchemyError as e:
            self.__error_log_manager.add_error(None, str(e))
            return None

    def fetch(self, model, filters=None, relationships=None):
        """
        データ取得（リレーションシップ対応）
        :param model: 操作対象のモデル
        :param filters: フィルター条件（辞書型）
        :param relationships: ロードするリレーションシップのリスト
        :return: 該当するデータのリスト
        """
        try:
            with Session(self.engine) as session:
                query = session.query(model)

                # フィルターの適用
                if filters:
                    for field, value in filters.items():
                        if hasattr(model, field):
                            query = query.filter(getattr(model, field) == value)
                        else:
                            raise AttributeError(f"'{model.__name__}'モデルに'{field}'という属性は存在しません。")

                # リレーションシップのロード
                if relationships:
                    for rel in relationships:
                        if hasattr(model, rel):
                            query = query.options(joinedload(getattr(model, rel)))
                        else:
                            raise AttributeError(f"'{model.__name__}'モデルに'{rel}'というリレーションは存在しません。")

                return query.all()
        except SQLAlchemyError as e:
            self.__error_log_manager.add_error(None, str(e))
            return None

    def fetch_all(self, model, filters=None, relationships=None):
        """
        指定した条件に一致する全件のレコードを取得
        """
        try:
            return self.fetch(model, filters=filters, relationships=relationships)
        except Exception as e:
            self.__error_log_manager.add_error(None, str(e))
            return []

    def fetch_one(self, model, filters=None, relationships=None):
        """
        指定した条件に一致する最初のレコードを取得
        """
        try:
            records = self.fetch(model, filters=filters, relationships=relationships)
            return records[0] if records else None
        except Exception as e:
            self.__error_log_manager.add_error(None, str(e))
            return None

    # def get_user_by_identifier(self, session, identifier):
    #     """ユーザーをメールアドレスまたはユーザーIDで取得"""
    #     from Ganger.app.model.model_manager.model import User
    #     if "@" in identifier:
    #         return Validator.validate_existence(session, User, {"email": identifier})
    #     return Validator.validate_existence(session, User, {"user_id": identifier})

