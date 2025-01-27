from werkzeug.security import check_password_hash
from cryptography.fernet import Fernet
from datetime import datetime, date
import re
from sqlalchemy.orm import Session

class Validator:
    SECRET_KEY = Fernet.generate_key()  # 本番環境では固定の安全なキーを使用
    cipher = Fernet(SECRET_KEY)
#     @staticmethod
#     def validate_existence(session: Session, model, conditions: dict):
#         """
#         任意のモデルと条件に基づいてデータを検索し、結果を返すメソッド。
#         データが存在しない場合は None を返す。
#         """
#         query = session.query(model)  # クエリ作成
#         print(f"[DEBUG] Initial Query: {query}")
#         print(f"[DEBUG] Model Columns: {[col.key for col in model.__table__.columns]}")

#         # 条件の確認
#         print(f"[DEBUG] Conditions: {conditions} (Type: {type(conditions)})")
#         if not isinstance(conditions, dict):
#             print(f"[ERROR] Invalid conditions type: {type(conditions)}. Expected dict.")
#             raise TypeError("Conditions must be a dictionary.")
#         if not conditions:
#             print("[ERROR] No conditions provided.")
#             raise ValueError("Conditions must not be empty.")

#         # フィルタリング処理
#         for field, value in conditions.items():
#             print(f"[DEBUG] Adding Filter: {field} == {value}")
#             print(f"[DEBUG] Does Model Have Field '{field}'? {hasattr(model, field)}")
#             if hasattr(model, field):
#                 query = query.filter(getattr(model, field) == value)
#                 print(f"[DEBUG] Query after Filter: {query}")
#             else:
#                 raise AttributeError(f"Model '{model.__name__}' does not have attribute '{field}'")

#         # クエリ結果を取得
#         try:
#             result = query.first()  # 最初の一致データを取得
#             print(f"[DEBUG] Query Result: {result}")
#         except Exception as e:
#             print(f"[ERROR] Query Execution Failed: {e}")
#             raise
#         return result

    @staticmethod
    def encrypt(value):
        """
        指定された値を暗号化する
        :param value: 暗号化する文字列または数値
        :return: 暗号化された文字列
        """
        return Validator.cipher.encrypt(str(value).encode()).decode()

    @staticmethod
    def decrypt(value):
        """
        指定された暗号化値を復号化する
        :param value: 暗号化された文字列
        :return: 復号化された元の値
        """
        return int(Validator.cipher.decrypt(value.encode()).decode())

    @staticmethod
    def validate_email_format(email: str):
        if not re.match(r'^\S+@\S+\.\S+$', email):
            error_message = "無効なメールアドレス形式"
            raise ValueError (error_message)


    @staticmethod
    def validate_date(year: int, month: int, day: int) -> tuple:

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


    @staticmethod
    def calculate_time_difference(post_time):
        """
        現在時刻と投稿時刻の差分を計算してフォーマットする
        :param post_time: 投稿時刻 (datetimeオブジェクト)
        :return: 差分を表す文字列（例: "5秒前", "5分前", "2時間前", "1日前"）
        """
        now = datetime.now()
        time_diff = now - post_time
        seconds_diff = int(time_diff.total_seconds())
        minutes_diff = seconds_diff // 60

        if seconds_diff < 60:  # 60秒未満
            return f"{seconds_diff}秒前"
        elif minutes_diff < 60:  # 60分未満
            return f"{minutes_diff}分前"
        elif minutes_diff < 1440:  # 24時間未満
            return f"{minutes_diff // 60}時間前"
        else:
            return f"{minutes_diff // 1440}日前"
        
    # @staticmethod
    # def object_to_dict(obj, include_relationships=True):
    #     """
    #     SQLAlchemy オブジェクトを辞書型に変換する関数。
    #     """
    #     from sqlalchemy.inspection import inspect

    #     try:
    #         # オブジェクトのカラム属性を辞書化
    #         result = {}
    #         for c in inspect(obj).mapper.column_attrs:
    #             value = getattr(obj, c.key)
    #             # 'id' が含まれるキーを暗号化
    #             if "id" in c.key.lower() and value is not None:
    #                 result[c.key] = Validator.encrypt(value)
    #             else:
    #                 result[c.key] = value

    #         if include_relationships:
    #             for relationship in inspect(obj).mapper.relationships:
    #                 related_obj = getattr(obj, relationship.key)
    #                 if related_obj is not None:
    #                     if relationship.uselist:  # 多対多・一対多の場合
    #                         result[relationship.key] = [
    #                             Validator.object_to_dict(o, include_relationships=False) for o in related_obj
    #                         ]
    #                     else:  # 一対一の場合
    #                         result[relationship.key] = Validator.object_to_dict(related_obj, include_relationships=False)

    #         return result

    #     except Exception as e:
    #         # エラーメッセージを生成してスロー
    #         error_message = f"Failed to convert object to dict: {str(e)}"
    #         raise ValueError(error_message) from e
        
    @staticmethod
    def to_json(obj):
        import json
        return json.dumps(obj)
    
    @staticmethod
    def calc_subtotal(price, quantity, discount):
        from decimal import Decimal

        # 安全な型変換と検証
        try:
            price = Decimal(price)
            quantity = int(quantity)
            discount = Decimal(discount)

            if quantity < 0 or price < 0 or discount < 0:
                raise ValueError("価格、数量、割引は正の値である必要があります")

            return price * quantity - Decimal(quantity * discount)

        except (ValueError, TypeError) as e:
            print(f"エラー: {e}")
            raise  # エラーを再度スロー

    @staticmethod
    def ensure_list(value):
        """
        単一値かリストかを判定し、常にリストとして返す

        Args:
            value (any): チェック対象の値（単一の値またはリスト）

        Returns:
            list: 常にリスト形式で返却
        """
        if value is None:
            return []
        if isinstance(value, (list, tuple, set)):
            return list(value)  # タプルやセットをリストに変換
        return [value]  # 単一値をリスト化