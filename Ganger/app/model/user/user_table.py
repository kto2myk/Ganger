from werkzeug.security import generate_password_hash, check_password_hash
from ErrorManager import ErrorLogManager
from Ganger.app.model.database_manager.database_connector import DatabaseConnector
from Ganger.app.model.validator.validate import Validator
from Ganger.app.model.model_manager.model import User
from sqlalchemy.orm import Session, joinedload

class UserManager(DatabaseConnector):
    def __init__(self):
        super().__init__()
        self.__error_log_manager = ErrorLogManager()  # エラーログ管理クラスを初期化

    
    def create_user(self, username: str, email: str, password: str, year: int, month: int, day: int):
        """
        新しいユーザーを作成し、データベースに保存します。
        """
        import uuid
        randomid = str(uuid.uuid4())[:8]
        user_id = f"{username}_{randomid}"

        try:
            # メールアドレスと生年月日の検証
            Validator.validate_email_format(email)
            birthday = Validator.validate_date(year, month, day)

            # 重複チェックとユーザー作成
            new_user = User(
                user_id=user_id,
                username=username,
                email=email,
                password=generate_password_hash(password),
                birthday=birthday
            )
            with Session(self.engine) as session:
                if Validator.validate_existence(
                        session=session, model=User, conditions={"email": email}):
                    raise ValueError("このメールアドレスは既に使用されています。")
                session.add(new_user)
                session.commit()

                # セッション外でも安全に利用できるデータを辞書で返す
                user_data = {
                    "id": new_user.id,
                    "user_id": new_user.user_id,
                    "username": new_user.username,
                    "email": new_user.email,
                    "create_time": new_user.create_time,
                    "birthday": new_user.birthday,
                    "profile_image":new_user.profile_image
                }
                print(f"[INFO] ユーザー {username} が正常に作成されました。")
                return True, user_data

        except ValueError as ve:
            self.__log_and_rollback_error(user_id=None, error_message=str(ve))
            return False, str(ve)
        except Exception as e:
            self.__log_and_rollback_error(user_id=None, error_message=str(e))
            return False, str(e)
            
            
    def login(self, identifier: str, password: str):
        """
        メールアドレスまたはユーザーIDでログイン
        """
        with Session(self.engine) as session:
            print(f"[DEBUG] Session Object: {session}")
            print(f"[DEBUG] Engine URL: {self.engine.url}")
            try:
                user = self.__get_user_by_identifier(session, identifier)
                if not user or not check_password_hash(user.password, password):
                    print("[WARNING] ログインに失敗しました。")
                    return None

                print(f"[INFO] ユーザー {user.username} がログインしました。")
                return user
            except Exception as e:
                self.__log_and_rollback_error(user_id=None, error_message=str(e))
                return None

    def update_user(self, user_id: str, updates: dict):
        """
        ユーザー情報を更新します。
        :param user_id: 更新対象のユーザーID
        :param updates: 更新するフィールドと値の辞書
        """
        with Session(self.engine) as session:
            try:
                user = session.query(User).filter_by(user_id=user_id).first()
                if not user:
                    raise ValueError("ユーザーが見つかりません。")
                
                for key, value in updates.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                    else:
                        raise AttributeError(f"Userクラスに'{key}'という属性は存在しません。")
                
                session.commit()
                print(f"[INFO] ユーザー {user.username} の情報が更新されました。")
                return True
            except Exception as e:
                self.__log_and_rollback_error(user_id=user_id, error_message=str(e))
                return False, str(e)
    
    def delete_user(self, user_id: str):
        """
        ユーザーを削除します。
        :param user_id: 削除対象のユーザーID
        """
        with Session(self.engine) as session:
            try:
                user = session.query(User).filter_by(user_id=user_id).first()
                if not user:
                    raise ValueError("ユーザーが見つかりません。")
                
                session.delete(user)
                session.commit()
                print(f"[INFO] ユーザー {user.username} が削除されました。")
                return True
            except Exception as e:
                self.__log_and_rollback_error(user_id=user_id, error_message=str(e))
                return False, str(e)

    def search_users(self, conditions: dict):
        """
        特定の条件に基づいてユーザーを検索します。
        :param conditions: 検索条件の辞書
        """
        with Session(self.engine) as session:
            try:
                query = session.query(User)
                for field, value in conditions.items():
                    if hasattr(User, field):
                        query = query.filter(getattr(User, field).like(f"%{value}%"))
                    else:
                        raise AttributeError(f"Userクラスに'{field}'という属性は存在しません。")
                
                users = query.all()
                return [{"user_id": u.user_id, "username": u.username, "email": u.email} for u in users]
            except Exception as e:
                self.__log_and_rollback_error(user_id=None, error_message=str(e))
                return []

    def reset_password(self, email: str, new_password: str):
        """
        ユーザーのパスワードをリセットします。
        :param email: リセット対象のメールアドレス
        :param new_password: 新しいパスワード
        """
        with Session(self.engine) as session:
            try:
                user = session.query(User).filter_by(email=email).first()
                if not user:
                    raise ValueError("メールアドレスに一致するユーザーが見つかりません。")
                
                user.password = generate_password_hash(new_password)
                session.commit()
                print(f"[INFO] ユーザー {user.username} のパスワードがリセットされました。")
                return True
            except Exception as e:
                self.__log_and_rollback_error(user_id=None, error_message=str(e))
                return False, str(e)

    def fetch_records(self, model, conditions=None, relationships=None):
            """
            指定したモデル、条件、リレーションに基づいてレコードを全件取得します。
            :param model: SQLAlchemyモデルクラス
            :param conditions: 取得条件（辞書形式: {フィールド名: 値}）
            :param relationships: 取得するリレーションのリスト
            :return: レコードのリスト
            """
            with Session(self.engine) as session:
                try:
                    # ベースクエリの作成
                    query = session.query(model)

                    # 条件の適用
                    if conditions:
                        for field, value in conditions.items():
                            if hasattr(model, field):
                                query = query.filter(getattr(model, field) == value)
                            else:
                                raise AttributeError(f"'{model.__name__}'モデルに'{field}'という属性は存在しません。")

                    # リレーションのロード
                    if relationships:
                        for rel in relationships:
                            if hasattr(model, rel):
                                query = query.options(joinedload(getattr(model, rel)))
                            else:
                                raise AttributeError(f"'{model.__name__}'モデルに'{rel}'というリレーションは存在しません。")

                    # 結果の取得
                    results = query.all()
                    return results
                except Exception as e:
                    print(f"[ERROR] Fetching records failed: {e}")
                    raise


    def __get_user_by_identifier(self, session, identifier):
        """ユーザーをメールアドレスまたはユーザーIDで取得"""
        if "@" in identifier:
            return Validator.validate_existence(session, User, {"email": identifier})
        return Validator.validate_existence(session, User, {"user_id": identifier})

    def __log_and_rollback_error(self, user_id, error_message):
        """エラーログを記録し、セッションをロールバック"""
        self.__error_log_manager.add_error(user_id, error_message)
        print(f"[ERROR] {error_message}")
