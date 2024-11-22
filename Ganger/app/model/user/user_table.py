from ErrorManager import ErrorLogManager, IntegrityError  
from Ganger.app.model.database_manager import Base, Column, Integer, String, DateTime, ForeignKey, func, relationship
from Ganger.app.model.database_manager.database_connector import DatabaseConnector
from Ganger.app.model.validator.validate import Validator
from Ganger.app.model.user.model import User
from werkzeug.security import generate_password_hash, check_password_hash

class UserManager(DatabaseConnector):
    def __init__(self):
        super().__init__()
        self.__error_log_manager = ErrorLogManager()  # エラーログ管理クラスを初期化

    def create_user(self, user_id: str, username: str, email: str, password: str, real_name: str, address: str, age: int):
        """
        新しいユーザーを作成し、データベースに保存します。
        エラーが発生した場合、エラーログに記録します。
        """
        new_user = User(
            user_id=user_id,
            username=username,
            email=email,
            password=generate_password_hash(password),
            real_name=real_name,
            address=address,
            age=age
        )

        with self.session as session:  # セッションの取得
            try:
                Validator.validate_email_format(email=email)
                if Validator.validate_existence( #重複確認
                    session=session,
                    model=User,
                    conditions={
                        "user_id":user_id,
                        "email":email
                    }
                ) is None:
                    raise ValueError ("このユーザーID,またはEmailは既に使用されています。")
                
                session.add(new_user)
                session.commit()
                print(f"[INFO] ユーザー {username} が正常に作成されました。")

            except (IntegrityError, TypeError) as e:
                session.rollback()
                # エラーログに記録
                self.__error_log_manager.add_error(
                    user_id=None,  # このエラーはユーザー作成前に発生するため、user_idは指定しない
                    error_message=str(e)
                )
                print(f"[ERROR] ユーザー作成中にエラーが発生しました: {e}")
            except ValueError as e:
                self.__error_log_manager.add_error(
                    user_id=None,
                    error_message=str(e)
                )
                print(f"[ERROR] ユーザー作成中にエラーが発生しました: {e}")

            except Exception as e:
                session.rollback()
                # エラーログに記録
                self.__error_log_manager.add_error(
                    user_id=None,
                    error_message=str(e)
                )
                print(f"[CRITICAL] 予期しないエラーが発生しました: {e}")


#ログイン認証
    def login(self, identifier: str, password: str):
        """
        メールアドレスまたはユーザーIDでログイン
        :param identifier: メールアドレスまたはユーザーID
        :param password: パスワード
        :return: ログイン成功時はユーザーオブジェクト、失敗時は None
        """
        with self.session as session:
            try:
                # Validatorを使用してユーザーを取得
                user = None
                if "@" in identifier:  # メールアドレスの場合
                    user = Validator.validate_existence(session=session,
                                                        model=User, 
                                                        conditions={"email": identifier})
                else:  # ユーザーIDの場合
                    user = Validator.validate_existence(session=session,
                                                        model=User,
                                                        conditions={"user_id": identifier})

                # ユーザーが存在し、パスワードが一致するかを検証
                if user and check_password_hash(user.password, password):
                    print(f"[INFO] ユーザー {user.username} がログインしました。")
                    return user
                else:
                    print("[WARNING] ログインに失敗しました。")
                    return None
            except Exception as e:
                print(f"[ERROR] ログイン処理中にエラーが発生しました: {e}")
                return None
