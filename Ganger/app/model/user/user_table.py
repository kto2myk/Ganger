from ErrorManager import ErrorLogManager, IntegrityError  
from Ganger.app.model.database_manager import Base, Column, Integer, String, DateTime, ForeignKey, func, relationship
from Ganger.app.model.database_manager.database_connector import DatabaseConnector
from Ganger.app.model.user.model import User

class UserManager(DatabaseConnector):
    def __init__(self):
        super().__init__()
        self.__user_list = []
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
            password=password,
            real_name=real_name,
            address=address,
            age=age
        )

        with self.session as session:  # セッションの取得
            try:
                session.add(new_user)
                session.commit()
                self.__user_list.append(new_user)
                print(f"[INFO] ユーザー {username} が正常に作成されました。")
            except (IntegrityError, TypeError) as e:
                session.rollback()
                # エラーログに記録
                self.__error_log_manager.add_error(
                    user_id=None,  # このエラーはユーザー作成前に発生するため、user_idは指定しない
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
