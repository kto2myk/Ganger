import os
import inspect
import threading
from sqlalchemy import create_engine,event
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from flask import current_app as app
from werkzeug.security import check_password_hash 
from Ganger.app.model.validator import Validator  # 検証用
from Ganger.app.model.model_manager.model import Base
from ErrorManager.error_manager import ErrorLogManager  #errorログ記録

class DatabaseConnector:
    __engine = None
    __lock = threading.Lock()
    def __init__(self, db_relative_path="Ganger/app/model/database_manager/Ganger.db", echo=False):
        """
        コンストラクタ
        :param db_relative_path: プロジェクト内でのデータベースの相対パス
        :param echo: SQLAlchemyのSQLログを出力するかどうか
        """
        # プロジェクトルートからの絶対パスを固定
        if not DatabaseConnector.__engine:
            with DatabaseConnector.__lock:
                if not DatabaseConnector.__engine:
                    db_path = os.path.abspath(db_relative_path)
                    db_folder = os.path.dirname(db_path)
                    self.__ensure_folder_exists(db_folder)  # データベースフォルダの存在を確認・作成
                    # データベースURLを設定
                    db_url = f"sqlite:///{db_path}"
                    # SQLAlchemyエンジンを作成
                    DatabaseConnector.__engine = create_engine(db_url, echo=echo,future=True,isolation_level="SERIALIZABLE")
                    if "sqlite" in db_url:
                        @event.listens_for(DatabaseConnector.__engine, "connect")
                        def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
                            cursor = dbapi_connection.cursor()
                            cursor.execute("PRAGMA foreign_keys=ON")
                            cursor.close()

    @staticmethod
    def __ensure_folder_exists(db_folder):
        """
        データベースの保存先フォルダが存在するか確認し、存在しない場合は作成する。
        """
        if not os.path.exists(db_folder):
            os.makedirs(db_folder)

    @classmethod
    def engine(cls):
        """
        データベースエンジンのインスタンスを返す。
        """
        return cls.__engine
    



class DatabaseManager(DatabaseConnector):
    __multi_stuck = []

    def __init__(self):
        super().__init__()
        self.__error_log_manager = ErrorLogManager()
    
    @property
    def error_log_manager(self):
        return self.__error_log_manager
    
    @classmethod
    def stuck(cls):
        """
        スタックリストの返却
        """
        return cls.__multi_stuck
    
    def insert(self, model, data, unique_check=None, Session = None):
        """
        データ挿入（重複チェックあり）
        :param model: 操作対象のモデル
        :param data: 挿入するデータ（辞書型）
        :param unique_check: 一意性チェックの条件（辞書型）
        :param session: DB接続情報（トランザクション管理用）
        :param multi: 複数処理の最中かどうか
        :return: 挿入されたインスタンス or None
        """
        try:
            Session = self.make_session(Session)
            # 一意性チェック
            if unique_check:
                # fetch_oneを使用して重複チェック
                existing = self.fetch_one(model=model, filters=unique_check,Session=Session)
                if existing:
                    app.logger.info("重複あり.")
                    self.pop_from_stack()
                    return None
            
            # 新規データ挿入
            new_entry = model(**data)
            Session.add(new_entry)
            self.make_commit_or_flush(Session=Session)
            # 辞書形式に変換（ローカル変数で管理）
            db_dict = {
                column.name: getattr(new_entry, column.name) for column in model.__table__.columns
            }
            return db_dict
        
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            self.__error_log_manager.add_error(None, str(e))
            return None
    
    def update(self, model, filters, data, Session = None):
        """データ更新"""
        try:
            Session = self.make_session(Session)
            query = Session.query(model).filter_by(**filters)
            if not query.first():
                app.logger.info("No matching entry found for update.")
                return None
            query.update(data)
            updated_instance = query.first()

            self.make_commit_or_flush(Session=Session)
            return updated_instance
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to update data: {e}")
            self.__error_log_manager.add_error(None, str(e))
            return None

    def delete(self, model, filters, Session = None):
        """データ削除"""
        try:
            Session = self.make_session(Session)
            query = Session.query(model).filter_by(**filters)
            deleted_count = query.delete()
            self.make_commit_or_flush(Session=Session)
            return deleted_count
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to delete data: {e}")
            self.__error_log_manager.add_error(None, str(e))
            return None

    def fetch(self, model, filters=None, relationships=None,Session = None):
        """
        データ取得（リレーションシップ対応）
        :param model: 操作対象のモデル
        :param filters: フィルター条件（辞書型）
        :param relationships: ロードするリレーションシップのリスト
        :return: 該当するデータのリスト
        """
        try:
            Session = self.make_session(Session)
            query = Session.query(model)

            # フィルターの適用
            if filters:
                for field, value in filters.items():
                    if hasattr(model, field):
                        query = query.filter(getattr(model, field) == value)
                    else:
                        app.logger.error(f"'{model.__name__}'モデルに'{field}'という属性は存在しません。")
                        raise AttributeError(f"'{model.__name__}'モデルに'{field}'という属性は存在しません。")

            # リレーションシップのロード
            if relationships:
                for rel in relationships:
                    if hasattr(model, rel):
                        query = query.options(joinedload(getattr(model, rel)))
                    else:
                        app.logger.error(f"'{model.__name__}'モデルに'{rel}'というリレーションは存在しません。")
                        raise AttributeError(f"'{model.__name__}'モデルに'{rel}'というリレーションは存在しません。")
            self.pop_from_stack()
            return query.all()
        
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to fetch data: {e}")
            self.__error_log_manager.add_error(None, str(e))
            return None


    def fetch_one(self, model, filters=None, relationships=None,Session = None):
        """
        指定した条件に一致する最初のレコードを取得
        """
        try:
            Session = self.make_session(Session)
            query = Session.query(model)

            # フィルターの適用
            if filters:
                for field, value in filters.items():
                    if hasattr(model, field):
                        query = query.filter(getattr(model, field) == value)
                    else:
                        app.logger.error(f"'{model.__name__}'モデルに'{field}'という属性は存在しません。")
                        raise AttributeError(f"'{model.__name__}'モデルに'{field}'という属性は存在しません。")

            # リレーションシップのロード
            if relationships:
                for rel in relationships:
                    if hasattr(model, rel):
                        query = query.options(joinedload(getattr(model, rel)))
                    else:
                        app.logger.error(f"'{model.__name__}'モデルに'{rel}'というリレーションは存在しません。")
                        raise AttributeError(f"'{model.__name__}'モデルに'{rel}'というリレーションは存在しません。")

            # 最初の一件を取得
            self.pop_from_stack()
            return query.first()
        except SQLAlchemyError as e:
            self.session_rollback(Session)
            app.logger.error(f"Failed to fetch one data: {e}")
            self.__error_log_manager.add_error(None, str(e))
            return None
        

    def build_query(self, Session, model, filters):
        """
        動的にクエリを構築する汎用メソッド

        :param Session: SQLAlchemy セッション
        :param model: 対象モデル
        :param filters: 条件の辞書 (キー: モデルの属性, 値: フィルタ値)
        :return: 構築されたクエリ
        :raises AttributeError: モデルに存在しない属性が指定された場合
        :raises SQLAlchemyError: クエリ構築中にSQLAlchemy関連のエラーが発生した場合
        """
        try:
            query = Session.query(model)
            for key, value in filters.items():
                if value is not None:  # None の条件は無視
                    if not hasattr(model, key):
                        raise AttributeError(f"Model '{model.__name__}' has no attribute '{key}'")
                    query = query.filter(getattr(model, key) == value)
            return query
        except AttributeError as ae:
            app.logger.error(f"Query building error: {ae}")
            raise
        except SQLAlchemyError as se:
            app.logger.error(f"SQLAlchemy error during query building: {se}")
            raise
        except Exception as e:
            app.logger.error(f"Unexpected error during query building: {e}")
            raise


    @classmethod
    def push_to_stack(cls, value:bool):
        """
        スタックに値を追加。
        """
        try:
            cls.__multi_stuck.append(value)
            app.logger.info(f"add {value} to stuck in {inspect.stack()[2].function}")
            app.logger.info(f"stuck is {cls.__multi_stuck} now")
        except Exception as e:
            app.logger.error(e)
            raise


    @classmethod
    def pop_from_stack(cls):
        """
        スタックから値を取り出す。
        """
        try:
            if cls.__multi_stuck:
                app.logger.info(f"pop {cls.__multi_stuck[-1]} from stuck")
                app.logger.info(f"stuck is {cls.__multi_stuck[:-1]} now")
                return cls.__multi_stuck.pop()
            
            else:
                e = "スタックが空です。pop操作に失敗しました。"
                app.logger.error(e)
                return None
        except Exception as e:
            app.logger.error(e)
            raise
        
    @classmethod
    def session_rollback(cls,Session):
        """
        スタックをクリアして、セッションをロールバックします。
        """
        try:
            cls.__multi_stuck.clear()
            Session.rollback()
            app.logger.info(f"clear the stuck,error occur {inspect.stack()[1].function},session rollback!!")
        except Exception as e:
            app.logger.error(e)
            raise
        finally:
            DatabaseManager.session_close(Session)

    @classmethod
    def peek_stack(cls):
        """
        スタックの最後の値を確認する（削除せずに）。
        """
        if cls.__multi_stuck:
            return cls.__multi_stuck[-1]
        return None
    
    @staticmethod
    def session_close(Session):
        try:
            Session.close()
            app.logger.info("session is closed")
        except Exception as e:
            app.logger.error(e)
            raise
        
    def make_session(self, db_session=None):
        """
        渡されたセッションを再利用し、渡されていない場合は新しいセッションを作成。
        __multi_stackにトランザクション状態を記録。
        """
        try:
            if db_session is None or self.stuck() is False:
                app.logger.info(f"make session in {inspect.stack()[1].function}")
                self.push_to_stack(False)
                db_session = Session(self.engine())
                db_session.begin()
                app.logger.info("created top session")
            else:
                self.push_to_stack(True)
                app.logger.info("session is reused,nested transaction")
                db_session.begin_nested()

            return db_session
        
        except Exception as e:
            if db_session:
                self.session_rollback(db_session)
            app.logger.error(e)
            raise

    @classmethod
    def pop_and_close(cls, Session):
        """
        スタックをポップし、セッションを閉じる。
        主にコミットやフラッシュを必要としない操作の後に呼び出す。
        """
        try:
            # スタックの状態を確認し、ポップ
            popped_value = cls.pop_from_stack()
            if popped_value is None:
                app.logger.error("スタックが空の状態で pop_and_close が呼び出されました。")
                raise ValueError("トランザクション状態が不正です。")

            # Trueの場合は何もせず終了（ネストされたトランザクションを終了しない）
            if popped_value is True:
                app.logger.info("ネストされたトランザクションの終了をスキップします。")
                return

            # Falseの場合はセッションを閉じる
            if popped_value is False and Session:
                DatabaseManager.session_close(Session=Session)
            else:
                app.logger.warning("セッションが無効、または既に閉じられています。")

        except Exception as e:
            app.logger.error(f"pop_and_close 中にエラーが発生しました: {e}")
            raise
    
    def make_commit_or_flush(self, Session):
        """
        スタックのトップを確認してフラッシュまたはコミットを行う。
        処理後にスタックから状態を取り出す。
        """
        try:
            is_multi = self.pop_from_stack()
            if is_multi is None:
                e = "トランザクション状態が不正です。"
                app.logger.error(e)
                raise  SystemError(e)
            
            if is_multi:
                Session.flush()  # トランザクションを継続する場合
                app.logger.info(f"session.flush() in {inspect.stack()[1].function}")
            else:
                Session.commit()  # トランザクションを確定する場合
                app.logger.info(f"session.commit() in {inspect.stack()[1].function}")
                DatabaseManager.session_close(Session=Session)
        except Exception as e:
            self.session_rollback(Session)
            app.logger.error(e)
            raise

    # def get_user_by_identifier(self, session, identifier):
    #     """ユーザーをメールアドレスまたはユーザーIDで取得"""
    #     from Ganger.app.model.model_manager.model import User
    #     if "@" in identifier:
    #         return Validator.validate_existence(session, User, {"email": identifier})
    #     return Validator.validate_existence(session, User, {"user_id": identifier})

