from werkzeug.security import generate_password_hash, check_password_hash
from ErrorManager import ErrorLogManager
from Ganger.app.model.database_manager.database_manager import DatabaseManager
from Ganger.app.model.validator.validate import Validator
from Ganger.app.model.model_manager.model import User
from sqlalchemy.orm import Session, joinedload

class UserManager(DatabaseManager):
    def __init__(self):
        super().__init__()


    def create_user(self, username: str, email: str, password: str):
        import uuid
        randomid = str(uuid.uuid4())[:8]
        user_id = f"{username}_{randomid}"

        try:
            Validator.validate_email_format(email) #email 型チェック

            user_data = {
                "user_id": user_id,
                "username": username,
                "email": email,
                "password": generate_password_hash(password)
                        }            
            new_user = self.insert(User, user_data, unique_check={"email": email})

            if not new_user:
                raise ValueError("このメールアドレスは既に使用されています。")
            return True, new_user
        
        except ValueError as ve:
            print(f"[ERROR] Validation error: {ve}")
            self.error_log_manager.add_error(None, str(ve))
            return False, str(ve)
        except Exception as e:
            print(f"[ERROR] Unexpected error: {e}")
            self.error_log_manager.add_error(None, str(e))
            return False, str(e)

    def login(self, identifier: str, password: str):
        """
        メールアドレスまたはユーザーIDでログイン
        """
        try:
            user = self.fetch_one(User, filters={"email": identifier}) or self.fetch_one(User, filters={"user_id": identifier})
            if not user or not check_password_hash(user.password, password):
                raise Exception("ユーザー名またはパスワードが間違っています。")
            return user, None
        
        except Exception as e:
            self.error_log_manager.add_error(None, str(e))
            return None, str(e)



