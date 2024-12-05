from werkzeug.security import generate_password_hash, check_password_hash
from ErrorManager import ErrorLogManager
from Ganger.app.model.database_manager.database_connector import DatabaseConnector
from Ganger.app.model.validator.validate import Validator
from Ganger.app.model.model_manager.model import User
from sqlalchemy.orm import Session

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

    def __get_user_by_identifier(self, session, identifier):
        """ユーザーをメールアドレスまたはユーザーIDで取得"""
        if "@" in identifier:
            return Validator.validate_existence(session, User, {"email": identifier})
        return Validator.validate_existence(session, User, {"user_id": identifier})

    def __log_and_rollback_error(self, user_id, error_message):
        """エラーログを記録し、セッションをロールバック"""
        self.__error_log_manager.add_error(user_id, error_message)
        print(f"[ERROR] {error_message}")
