import inspect
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ErrorManager.models import ErrorLog  # エラーログのモデルをインポート
from ErrorManager.table import TableConnector

class ErrorLogManager(TableConnector):
    def add_error(self, user_id, error_message):
        """
        エラーログをデータベースに追加
        :param user_id: エラーが関連するユーザーのID
        :param error_message: エラーの詳細メッセージ
        """
        # 呼び出し元のメソッド名を自動取得
        method_name = inspect.stack()[1].function

        new_error = ErrorLog(
            user_id=user_id,
            method_name=method_name,
            error_message=error_message
        )

        # `with`構文でセッションを管理
        with self.session as session:
            try:
                session.add(new_error)
                session.commit()
                print(f"[INFO] エラーログが記録されました（メソッド: {method_name}）")
            except IntegrityError as e:
                session.rollback()
                print(f"[WARNING] データの整合性エラーが発生しました: {e}")
            except SQLAlchemyError as e:
                session.rollback()
                print(f"[ERROR] エラーログ記録中にエラーが発生しました: {e}")
            except Exception as e:
                session.rollback()
                print(f"[CRITICAL] 想定外のエラーが発生しました: {e}")
