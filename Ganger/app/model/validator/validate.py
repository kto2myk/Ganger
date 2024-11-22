from werkzeug.security import check_password_hash


class Validator:
    from sqlalchemy.orm import Session

    @staticmethod
    def validate_existence(session: Session, model, conditions: dict):
        """
        任意のモデルと条件に基づいてデータを検索し、結果を返すメソッド。
        データが存在しない場合は None を返す。
        :param session: SQLAlchemy セッション
        :param model: SQLAlchemy モデルクラス（例: User）
        :param conditions: 辞書形式で指定する条件（例: {"user_id": "example", "email": "test@example.com"}）
        :return: 一致するデータオブジェクト、存在しない場合は None
        """
        query = session.query(model)
        for field, value in conditions.items():
            query = query.filter(getattr(model, field) == value)
        
        # 最初の一致するオブジェクトを返す
        return query.first()

    @staticmethod
    def validate_email_format(email: str):
        import re
        if not re.match(r'^\S+@\S+\.\S+$', email):
            error_message = "無効なメールアドレス形式"
            raise ValueError (error_message)

    @staticmethod
    def validate_age(age: int):
        if age < 0:
            error_message = "無効なメールアドレス形式"
            raise ValueError(error_message)
