from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from ErrorManager.models import ErrorLog
from ErrorManager.table import TableConnector
import inspect
from flask import current_app as app

class ErrorLogManager(TableConnector):
    def add_error(self, user_id, error_message):
        """エラーログをデータベースに追加"""
        method_name = inspect.stack()[1].function
        new_error = ErrorLog(user_id=user_id, method_name=method_name, error_message=error_message)
        with self.session as session:
            try:
                session.add(new_error)
                session.commit()
                app.logger.info(f"[INFO] エラーログが記録されました（メソッド: {method_name}）")
            except IntegrityError:
                session.rollback()
                app.logger.warning("[WARNING] データの整合性エラーが発生しました。")
            except SQLAlchemyError as e:
                session.rollback()
                app.logger.error(f"[ERROR] エラーログ記録中にエラーが発生しました: {e}")
    
