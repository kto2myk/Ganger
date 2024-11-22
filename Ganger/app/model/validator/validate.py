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
    def validate_date(year: int, month: int, day: int) -> tuple:
        from datetime import date, datetime

        """
        生年月日を検証し、日付型で返します。
        無効な場合はエラーメッセージを返します。
        
        :return: 成功時は (True, date) を返し、失敗時は (False, エラーメッセージ) を返す。
        """
        
        # 現在の日付を基準に120年前を計算
        current_year = datetime.today().year
        earliest_year = current_year - 120  # 現在から120年前

        # 年月日の型チェック
        if not all(isinstance(i, int) for i in [year, month, day]):
            raise ValueError("年、月、日はすべて整数でなければなりません。")
        
        # 範囲チェック
        if year < earliest_year or year > current_year + 1:
            raise ValueError(f"年は{earliest_year}年から{current_year + 1}年の範囲内で指定してください。")
        if month < 1 or month > 12:
            raise ValueError("月は1〜12の範囲内で指定してください。")
        if day < 1 or day > 31:
            raise ValueError("日は1〜31の範囲内で指定してください。")
        
        # 日付の作成
        birthday = date(year, month, day)

        # 未来の日付のチェック
        if birthday > datetime.today().date():
            raise ValueError("生年月日は未来の日付を指定できません。")

        # 成功時は日付を返す
        return birthday

